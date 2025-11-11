package sentiment

import (
	"fmt"
	"log"
	"sync"
	"time"
)

// Analyzer is the main sentiment analysis engine
type Analyzer struct {
	twitterAnalyzer   *TwitterAnalyzer
	newsScr aper      *NewsScraper
	socialAnalyzer    *SocialAnalyzer
	cache             *SentimentCache
	mu                sync.RWMutex
}

// SentimentCache caches sentiment data to avoid excessive API calls
type SentimentCache struct {
	data      map[string]*SentimentData
	expiry    time.Duration
	mu        sync.RWMutex
}

// NewAnalyzer creates a new sentiment analyzer
func NewAnalyzer() *Analyzer {
	return &Analyzer{
		twitterAnalyzer: NewTwitterAnalyzer(),
		newsScraper:     NewNewsScraper(),
		socialAnalyzer:  NewSocialAnalyzer(),
		cache: &SentimentCache{
			data:   make(map[string]*SentimentData),
			expiry: 5 * time.Minute, // Cache for 5 minutes
		},
	}
}

// Analyze performs comprehensive sentiment analysis for a symbol
func (a *Analyzer) Analyze(symbol string) (*SentimentData, error) {
	// Check cache first
	if cached := a.cache.Get(symbol); cached != nil {
		log.Printf("📊 [Sentiment] Using cached data for %s", symbol)
		return cached, nil
	}

	log.Printf("🔍 [Sentiment] Analyzing sentiment for %s", symbol)

	// Run all analyzers concurrently
	var wg sync.WaitGroup
	var (
		twitterMetrics TwitterMetrics
		newsMetrics    NewsMetrics
		socialMetrics  SocialMetrics
		fgIndex        int
	)

	// Errors channel
	errChan := make(chan error, 4)

	// Twitter analysis
	wg.Add(1)
	go func() {
		defer wg.Done()
		metrics, err := a.twitterAnalyzer.Analyze(symbol)
		if err != nil {
			log.Printf("⚠️  Twitter analysis failed: %v", err)
			errChan <- err
			return
		}
		twitterMetrics = metrics
	}()

	// News analysis
	wg.Add(1)
	go func() {
		defer wg.Done()
		metrics, err := a.newsScraper.Analyze(symbol)
		if err != nil {
			log.Printf("⚠️  News analysis failed: %v", err)
			errChan <- err
			return
		}
		newsMetrics = metrics
	}()

	// Social media analysis
	wg.Add(1)
	go func() {
		defer wg.Done()
		metrics, err := a.socialAnalyzer.Analyze(symbol)
		if err != nil {
			log.Printf("⚠️  Social analysis failed: %v", err)
			errChan <- err
			return
		}
		socialMetrics = metrics
	}()

	// Fear & Greed Index (only for BTC)
	wg.Add(1)
	go func() {
		defer wg.Done()
		if symbol == "BTCUSDT" || symbol == "BTC" {
			index, err := a.getFearGreedIndex()
			if err != nil {
				log.Printf("⚠️  Fear & Greed index failed: %v", err)
				errChan <- err
				return
			}
			fgIndex = index
		}
	}()

	wg.Wait()
	close(errChan)

	// Check if we have any errors
	var errors []error
	for err := range errChan {
		if err != nil {
			errors = append(errors, err)
		}
	}

	// If all sources failed, return error
	if len(errors) >= 4 {
		return nil, fmt.Errorf("all sentiment sources failed")
	}

	// Calculate overall sentiment score
	sentimentData := &SentimentData{
		Symbol:         symbol,
		Timestamp:      time.Now(),
		TwitterMetrics: twitterMetrics,
		NewsMetrics:    newsMetrics,
		SocialMetrics:  socialMetrics,
		FearGreedIndex: fgIndex,
	}

	// Calculate weighted sentiment score
	sentimentData.SentimentScore = a.calculateOverallScore(sentimentData)
	sentimentData.SentimentTrend = a.determineTrend(sentimentData.SentimentScore)
	sentimentData.Confidence = a.calculateConfidence(sentimentData)
	sentimentData.OverallAssessment = a.generateAssessment(sentimentData)

	// Cache the result
	a.cache.Set(symbol, sentimentData)

	log.Printf("✅ [Sentiment] %s sentiment score: %.1f (%s) - Confidence: %d%%",
		symbol, sentimentData.SentimentScore, sentimentData.SentimentTrend, sentimentData.Confidence)

	return sentimentData, nil
}

// calculateOverallScore computes weighted sentiment score (0-100)
func (a *Analyzer) calculateOverallScore(data *SentimentData) float64 {
	// Weights for different sentiment sources
	const (
		twitterWeight = 0.35
		newsWeight    = 0.30
		socialWeight  = 0.20
		fgWeight      = 0.15
	)

	var score float64

	// Twitter sentiment (0-100)
	if data.TwitterMetrics.Mentions > 0 {
		twitterScore := data.TwitterMetrics.PositiveRatio * 100
		score += twitterScore * twitterWeight
	}

	// News sentiment (0-100)
	if data.NewsMetrics.ArticleCount > 0 {
		newsScore := float64(data.NewsMetrics.PositiveCount) / float64(data.NewsMetrics.ArticleCount) * 100
		score += newsScore * newsWeight
	}

	// Social sentiment (0-100)
	if data.SocialMetrics.EngagementScore > 0 {
		score += data.SocialMetrics.EngagementScore * socialWeight
	}

	// Fear & Greed Index
	if data.FearGreedIndex > 0 {
		score += float64(data.FearGreedIndex) * fgWeight
	}

	return score
}

// determineTrend determines the overall sentiment trend
func (a *Analyzer) determineTrend(score float64) string {
	switch {
	case score >= 70:
		return "strongly_bullish"
	case score >= 60:
		return "bullish"
	case score >= 40 && score < 60:
		return "neutral"
	case score >= 30:
		return "bearish"
	default:
		return "strongly_bearish"
	}
}

// calculateConfidence calculates confidence level based on data availability
func (a *Analyzer) calculateConfidence(data *SentimentData) int {
	confidence := 0

	// More data sources = higher confidence
	if data.TwitterMetrics.Mentions > 100 {
		confidence += 25
	} else if data.TwitterMetrics.Mentions > 10 {
		confidence += 15
	}

	if data.NewsMetrics.ArticleCount > 10 {
		confidence += 25
	} else if data.NewsMetrics.ArticleCount > 3 {
		confidence += 15
	}

	if data.SocialMetrics.RedditMentions > 50 {
		confidence += 25
	} else if data.SocialMetrics.RedditMentions > 10 {
		confidence += 15
	}

	if data.FearGreedIndex > 0 {
		confidence += 25
	}

	// Cap at 100
	if confidence > 100 {
		confidence = 100
	}

	return confidence
}

// generateAssessment generates a text assessment of the sentiment
func (a *Analyzer) generateAssessment(data *SentimentData) string {
	trend := data.SentimentTrend
	score := data.SentimentScore

	var assessment string

	switch trend {
	case "strongly_bullish":
		assessment = fmt.Sprintf("極度看漲情緒 (分數: %.1f/100)。", score)
		assessment += "Twitter、新聞和社交媒體均顯示強烈的正面情緒。"
	case "bullish":
		assessment = fmt.Sprintf("看漲情緒 (分數: %.1f/100)。", score)
		assessment += "市場情緒偏向正面，但應謹慎行事。"
	case "neutral":
		assessment = fmt.Sprintf("中立情緒 (分數: %.1f/100)。", score)
		assessment += "市場情緒混合，無明顯方向。"
	case "bearish":
		assessment = fmt.Sprintf("看跌情緒 (分數: %.1f/100)。", score)
		assessment += "市場情緒偏向負面，建議謹慎。"
	case "strongly_bearish":
		assessment = fmt.Sprintf("極度看跌情緒 (分數: %.1f/100)。", score)
		assessment += "各來源均顯示強烈負面情緒，高風險。"
	}

	// Add specific insights
	if data.TwitterMetrics.TrendingRank > 0 && data.TwitterMetrics.TrendingRank <= 10 {
		assessment += fmt.Sprintf(" 在Twitter趨勢榜排名#%d。", data.TwitterMetrics.TrendingRank)
	}

	if data.NewsMetrics.ArticleCount > 20 {
		assessment += fmt.Sprintf(" 過去24小時有%d篇相關新聞報導。", data.NewsMetrics.ArticleCount)
	}

	return assessment
}

// getFearGreedIndex fetches the crypto fear & greed index
func (a *Analyzer) getFearGreedIndex() (int, error) {
	// TODO: Implement actual API call to alternative.me or similar
	// For now, return a mock value
	// In production, this would call: https://api.alternative.me/fng/

	// Mock implementation
	// In real implementation, you would:
	// 1. HTTP GET https://api.alternative.me/fng/
	// 2. Parse JSON response
	// 3. Return value

	return 50, nil // Neutral mock value
}

// GenerateSignal generates a trading signal based on sentiment analysis
func (a *Analyzer) GenerateSignal(symbol string) (*SentimentSignal, error) {
	data, err := a.Analyze(symbol)
	if err != nil {
		return nil, err
	}

	signal := &SentimentSignal{
		Symbol:    symbol,
		Timestamp: time.Now(),
		Metrics:   *data,
	}

	// Determine signal based on sentiment score and confidence
	score := data.SentimentScore
	confidence := data.Confidence

	// Only generate strong signals if confidence is high
	if confidence < 50 {
		signal.Signal = "neutral"
		signal.Strength = confidence
		signal.Reasoning = "信心度不足，建議觀望"
		return signal, nil
	}

	switch {
	case score >= 75:
		signal.Signal = "strong_buy"
		signal.Strength = int(score)
		signal.Reasoning = fmt.Sprintf("極度樂觀情緒 (%.1f/100)，高信心度 (%d%%)，建議做多", score, confidence)
	case score >= 60:
		signal.Signal = "buy"
		signal.Strength = int(score)
		signal.Reasoning = fmt.Sprintf("樂觀情緒 (%.1f/100)，建議謹慎做多", score)
	case score >= 40 && score < 60:
		signal.Signal = "neutral"
		signal.Strength = 50
		signal.Reasoning = fmt.Sprintf("中立情緒 (%.1f/100)，建議觀望", score)
	case score >= 25:
		signal.Signal = "sell"
		signal.Strength = 100 - int(score)
		signal.Reasoning = fmt.Sprintf("悲觀情緒 (%.1f/100)，建議謹慎做空", score)
	default:
		signal.Signal = "strong_sell"
		signal.Strength = 100 - int(score)
		signal.Reasoning = fmt.Sprintf("極度悲觀情緒 (%.1f/100)，建議做空", score)
	}

	return signal, nil
}

// SentimentCache methods

func (c *SentimentCache) Get(symbol string) *SentimentData {
	c.mu.RLock()
	defer c.mu.RUnlock()

	if data, exists := c.data[symbol]; exists {
		// Check if expired
		if time.Since(data.Timestamp) < c.expiry {
			return data
		}
		// Expired, remove from cache
		delete(c.data, symbol)
	}
	return nil
}

func (c *SentimentCache) Set(symbol string, data *SentimentData) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.data[symbol] = data
}

func (c *SentimentCache) Clear() {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.data = make(map[string]*SentimentData)
}
