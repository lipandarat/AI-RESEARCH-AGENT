package sentiment

import (
	"fmt"
	"log"
	"math/rand"
	"strings"
	"time"
)

// NewsScraper scrapes and analyzes crypto news sentiment
type NewsScraper struct {
	sources []string
	// In production, add HTTP client, rate limiter, etc.
}

// NewNewsScraper creates a new news scraper
func NewNewsScraper() *NewsScraper {
	return &NewsScraper{
		sources: []string{
			"coindesk.com",
			"cointelegraph.com",
			"decrypt.co",
			"theblock.co",
			"bitcoinmagazine.com",
			"cryptoslate.com",
		},
	}
}

// Analyze analyzes news sentiment for a symbol
func (ns *NewsScraper) Analyze(symbol string) (NewsMetrics, error) {
	log.Printf("📰 [News] Analyzing news sentiment for %s", symbol)

	coinName, fullName := extractCoinNames(symbol)

	// In production, this would:
	// 1. Scrape news from multiple sources (CoinDesk, CoinTelegraph, etc.)
	// 2. Use NLP to analyze headline and article sentiment
	// 3. Aggregate sentiment scores
	// 4. Detect trending topics
	//
	// Example implementation:
	// - Use goquery for web scraping
	// - Use go-nlp or external NLP API for sentiment analysis
	// - Consider using NewsAPI, CryptoCompare News API, or similar

	metrics := ns.generateMockMetrics(coinName, fullName)

	log.Printf("✅ [News] %s - Articles: %d, Positive: %d, Negative: %d, Sentiment: %s",
		symbol, metrics.ArticleCount, metrics.PositiveCount, metrics.NegativeCount, metrics.Sentiment)

	return metrics, nil
}

// extractCoinNames is duplicated here for package independence
func extractCoinNames(symbol string) (string, string) {
	coin := strings.TrimSuffix(symbol, "USDT")
	coin = strings.TrimSuffix(coin, "BUSD")
	coin = strings.TrimSuffix(coin, "USD")

	coinNames := map[string]string{
		"BTC":  "Bitcoin",
		"ETH":  "Ethereum",
		"SOL":  "Solana",
		"BNB":  "BNB",
		"XRP":  "Ripple",
		"ADA":  "Cardano",
		"DOGE": "Dogecoin",
		"AVAX": "Avalanche",
		"DOT":  "Polkadot",
		"MATIC": "Polygon",
	}

	fullName, exists := coinNames[coin]
	if !exists {
		fullName = coin
	}

	return coin, fullName
}

// generateMockMetrics generates realistic mock news metrics
// TODO: Replace with real news scraping
func (ns *NewsScraper) generateMockMetrics(coinName, fullName string) NewsMetrics {
	r := rand.New(rand.NewSource(time.Now().UnixNano()))

	// Major coins get more news coverage
	var baseArticles int
	switch coinName {
	case "BTC":
		baseArticles = 20 + r.Intn(30) // 20-50 articles
	case "ETH":
		baseArticles = 15 + r.Intn(20) // 15-35 articles
	case "SOL", "BNB", "XRP":
		baseArticles = 5 + r.Intn(15)  // 5-20 articles
	default:
		baseArticles = 1 + r.Intn(8)   // 1-9 articles
	}

	// Generate sentiment distribution
	positiveCount := int(float64(baseArticles) * (0.3 + r.Float64()*0.3))  // 30-60%
	negativeCount := int(float64(baseArticles) * (0.1 + r.Float64()*0.2))  // 10-30%
	neutralCount := baseArticles - positiveCount - negativeCount

	// Ensure valid counts
	if neutralCount < 0 {
		neutralCount = 0
		positiveCount = baseArticles - negativeCount
	}

	// Determine overall sentiment
	var sentiment string
	if positiveCount > negativeCount*2 {
		sentiment = "positive"
	} else if negativeCount > positiveCount*2 {
		sentiment = "negative"
	} else {
		sentiment = "neutral"
	}

	// Generate mock headlines
	headlines := ns.generateMockHeadlines(coinName, fullName, sentiment, 5)

	return NewsMetrics{
		ArticleCount:  baseArticles,
		PositiveCount: positiveCount,
		NegativeCount: negativeCount,
		NeutralCount:  neutralCount,
		Sentiment:     sentiment,
		TopHeadlines:  headlines,
		Sources:       ns.sources,
	}
}

// generateMockHeadlines generates realistic news headlines
func (ns *NewsScraper) generateMockHeadlines(coinName, fullName, sentiment string, count int) []string {
	r := rand.New(rand.NewSource(time.Now().UnixNano()))

	positiveTemplates := []string{
		"%s Surges Past Key Resistance Level",
		"%s Adoption Grows as Major Institutions Show Interest",
		"Analysts Predict %s Bull Run Continuation",
		"%s Network Upgrade Shows Promising Results",
		"Why %s Could Reach New All-Time Highs",
		"%s Fundamentals Remain Strong Despite Market Volatility",
		"Institutional Investors Accumulating %s",
	}

	negativeTemplates := []string{
		"%s Faces Selling Pressure as Market Turns Bearish",
		"Analysts Warn of Potential %s Correction",
		"%s Drops Below Critical Support Level",
		"Regulatory Concerns Impact %s Price",
		"Why Some Investors Are Taking Profits on %s",
		"%s Struggles to Maintain Momentum",
		"Technical Indicators Suggest %s Weakness",
	}

	neutralTemplates := []string{
		"%s Price Analysis: What to Expect Next Week",
		"Understanding %s Recent Price Action",
		"%s Market Update: Key Levels to Watch",
		"What's Driving %s Trading Volume?",
		"%s Technical Analysis: Neutral Outlook",
		"Investors Divided on %s Short-Term Direction",
		"%s Consolidates After Recent Volatility",
	}

	var templates []string
	switch sentiment {
	case "positive":
		templates = positiveTemplates
	case "negative":
		templates = negativeTemplates
	default:
		templates = neutralTemplates
	}

	headlines := make([]string, 0, count)
	usedIndices := make(map[int]bool)

	for i := 0; i < count && len(usedIndices) < len(templates); i++ {
		idx := r.Intn(len(templates))
		if !usedIndices[idx] {
			usedIndices[idx] = true
			headline := fmt.Sprintf(templates[idx], fullName)
			headlines = append(headlines, headline)
		}
	}

	return headlines
}

// ScrapeArticles scrapes full articles from news sources
// TODO: Implement with real web scraping
func (ns *NewsScraper) ScrapeArticles(symbol string, hours int) ([]NewsArticle, error) {
	// In production:
	// 1. Use goquery or colly for web scraping
	// 2. Respect robots.txt and rate limits
	// 3. Parse article text, not just headlines
	// 4. Use NLP for sentiment analysis
	// 5. Cache results to avoid re-scraping

	coinName, fullName := extractCoinNames(symbol)
	_ = coinName

	articles := make([]NewsArticle, 0)
	r := rand.New(rand.NewSource(time.Now().UnixNano()))

	// Generate 3-10 mock articles
	numArticles := 3 + r.Intn(8)

	for i := 0; i < numArticles; i++ {
		// Random sentiment
		sentiments := []string{"positive", "negative", "neutral"}
		sentiment := sentiments[r.Intn(len(sentiments))]

		var score float64
		switch sentiment {
		case "positive":
			score = 0.3 + r.Float64()*0.7
		case "negative":
			score = -0.3 - r.Float64()*0.7
		default:
			score = -0.2 + r.Float64()*0.4
		}

		article := NewsArticle{
			Title:       fmt.Sprintf("Analysis: %s market trends and predictions", fullName),
			URL:         fmt.Sprintf("https://cryptonews.com/article/%d", r.Intn(100000)),
			Source:      ns.sources[r.Intn(len(ns.sources))],
			PublishedAt: time.Now().Add(-time.Duration(r.Intn(hours)) * time.Hour),
			Sentiment:   sentiment,
			Score:       score,
			Keywords:    []string{fullName, "cryptocurrency", "trading", "market analysis"},
		}
		articles = append(articles, article)
	}

	return articles, nil
}

// DetectBreakingNews detects breaking news that might impact price
func (ns *NewsScraper) DetectBreakingNews(symbol string) ([]NewsArticle, error) {
	// In production:
	// 1. Monitor news feeds for breaking news
	// 2. Use keywords like "breaking", "urgent", "alert"
	// 3. Check publication time (last 1-2 hours)
	// 4. Analyze potential price impact

	// Mock: return empty for now
	return []NewsArticle{}, nil
}

// AnalyzeHeadlineSentiment analyzes sentiment from headline only
func (ns *NewsScraper) AnalyzeHeadlineSentiment(headline string) (string, float64) {
	// Simple keyword-based sentiment analysis
	// In production, use proper NLP library or API

	headline = strings.ToLower(headline)

	positiveKeywords := []string{
		"surge", "rally", "gain", "rise", "bull", "growth",
		"adoption", "breakthrough", "success", "upgrade", "moon",
		"bullish", "soar", "jump", "climb",
	}

	negativeKeywords := []string{
		"drop", "fall", "crash", "decline", "bear", "loss",
		"fear", "concern", "warning", "risk", "correction",
		"bearish", "plunge", "tumble", "sell-off",
	}

	positiveCount := 0
	negativeCount := 0

	for _, keyword := range positiveKeywords {
		if strings.Contains(headline, keyword) {
			positiveCount++
		}
	}

	for _, keyword := range negativeKeywords {
		if strings.Contains(headline, keyword) {
			negativeCount++
		}
	}

	var sentiment string
	var score float64

	if positiveCount > negativeCount {
		sentiment = "positive"
		score = float64(positiveCount) / (float64(positiveCount + negativeCount) + 1.0)
	} else if negativeCount > positiveCount {
		sentiment = "negative"
		score = -float64(negativeCount) / (float64(positiveCount + negativeCount) + 1.0)
	} else {
		sentiment = "neutral"
		score = 0.0
	}

	return sentiment, score
}
