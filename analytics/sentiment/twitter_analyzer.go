package sentiment

import (
	"fmt"
	"log"
	"math/rand"
	"strings"
	"time"
)

// TwitterAnalyzer analyzes Twitter sentiment for crypto assets
type TwitterAnalyzer struct {
	apiKey    string
	apiSecret string
	// In production, add Twitter API client here
}

// NewTwitterAnalyzer creates a new Twitter analyzer
func NewTwitterAnalyzer() *TwitterAnalyzer {
	return &TwitterAnalyzer{
		// Initialize with API keys from environment/config
	}
}

// Analyze analyzes Twitter sentiment for a symbol
func (ta *TwitterAnalyzer) Analyze(symbol string) (TwitterMetrics, error) {
	log.Printf("🐦 [Twitter] Analyzing sentiment for %s", symbol)

	// Extract coin name from symbol (e.g., "BTCUSDT" -> "BTC", "Bitcoin")
	coinName, coinFullName := ta.extractCoinNames(symbol)

	// In production, this would call Twitter API v2:
	// 1. Search for tweets containing coin name/symbol
	// 2. Get tweet metrics (likes, retweets, replies)
	// 3. Analyze sentiment using NLP
	// 4. Check if trending
	//
	// Example API calls:
	// - GET /2/tweets/search/recent?query=Bitcoin OR BTC
	// - GET /2/trends/place/:id
	//
	// For now, we'll generate realistic mock data

	metrics := ta.generateMockMetrics(coinName, coinFullName)

	log.Printf("✅ [Twitter] %s - Mentions: %d, Positive: %.1f%%, Sentiment: %s",
		symbol, metrics.Mentions, metrics.PositiveRatio*100, metrics.Sentiment)

	return metrics, nil
}

// extractCoinNames extracts coin name and full name from symbol
func (ta *TwitterAnalyzer) extractCoinNames(symbol string) (string, string) {
	// Remove trading pair suffix
	coin := strings.TrimSuffix(symbol, "USDT")
	coin = strings.TrimSuffix(coin, "BUSD")
	coin = strings.TrimSuffix(coin, "USD")

	// Map to full names (in production, use a comprehensive mapping)
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

// generateMockMetrics generates realistic mock Twitter metrics
// TODO: Replace with real Twitter API integration
func (ta *TwitterAnalyzer) generateMockMetrics(coinName, fullName string) TwitterMetrics {
	// Seed random for deterministic results in testing
	r := rand.New(rand.NewSource(time.Now().UnixNano()))

	// Different coins have different Twitter activity levels
	var baseMentions int
	switch coinName {
	case "BTC":
		baseMentions = 15000 + r.Intn(10000) // Bitcoin: 15k-25k mentions
	case "ETH":
		baseMentions = 8000 + r.Intn(7000)   // Ethereum: 8k-15k mentions
	case "SOL", "BNB", "XRP":
		baseMentions = 3000 + r.Intn(4000)   // Major alts: 3k-7k mentions
	default:
		baseMentions = 500 + r.Intn(1500)    // Other coins: 500-2k mentions
	}

	// Generate sentiment ratios (should sum to ~1.0)
	// Use beta distribution for more realistic sentiment distribution
	positiveRatio := 0.3 + r.Float64()*0.4  // 30-70% positive
	negativeRatio := 0.1 + r.Float64()*0.3  // 10-40% negative
	neutralRatio := 1.0 - positiveRatio - negativeRatio

	// Normalize to ensure sum = 1.0
	total := positiveRatio + negativeRatio + neutralRatio
	positiveRatio /= total
	negativeRatio /= total
	neutralRatio /= total

	// Determine overall sentiment
	var sentiment string
	if positiveRatio > 0.55 {
		sentiment = "positive"
	} else if negativeRatio > 0.45 {
		sentiment = "negative"
	} else {
		sentiment = "neutral"
	}

	// Trending rank (0 if not trending, 1-50 if trending)
	var trendingRank int
	if coinName == "BTC" && r.Float64() > 0.5 {
		trendingRank = 1 + r.Intn(5) // BTC often in top 5
	} else if coinName == "ETH" && r.Float64() > 0.6 {
		trendingRank = 5 + r.Intn(10) // ETH sometimes in top 15
	} else if r.Float64() > 0.85 {
		trendingRank = 10 + r.Intn(40) // Other coins rarely trending
	}

	return TwitterMetrics{
		Mentions:      baseMentions,
		PositiveRatio: positiveRatio,
		NegativeRatio: negativeRatio,
		NeutralRatio:  neutralRatio,
		Sentiment:     sentiment,
		TrendingRank:  trendingRank,
	}
}

// GetRecentTweets fetches recent tweets about a coin
// TODO: Implement with real Twitter API
func (ta *TwitterAnalyzer) GetRecentTweets(symbol string, maxResults int) ([]TweetData, error) {
	// In production, this would:
	// 1. Call Twitter API v2 /tweets/search/recent
	// 2. Parse tweets
	// 3. Analyze sentiment for each tweet
	// 4. Return structured data

	coinName, fullName := ta.extractCoinNames(symbol)
	_ = fullName // Use fullName in search query

	// Mock implementation
	tweets := make([]TweetData, 0, maxResults)
	r := rand.New(rand.NewSource(time.Now().UnixNano()))

	mockTexts := []string{
		fmt.Sprintf("%s to the moon! 🚀", coinName),
		fmt.Sprintf("Just bought more %s, bullish!", coinName),
		fmt.Sprintf("%s looking strong on the charts", coinName),
		fmt.Sprintf("Taking profits on %s", coinName),
		fmt.Sprintf("%s breaking resistance!", coinName),
		fmt.Sprintf("Bearish on %s short term", coinName),
		fmt.Sprintf("%s showing weakness", coinName),
		fmt.Sprintf("Accumulating %s at these prices", coinName),
	}

	for i := 0; i < maxResults; i++ {
		sentiment := "neutral"
		score := 0.0

		// Determine sentiment based on text
		text := mockTexts[r.Intn(len(mockTexts))]
		if strings.Contains(text, "moon") || strings.Contains(text, "bullish") || strings.Contains(text, "strong") {
			sentiment = "positive"
			score = 0.5 + r.Float64()*0.5
		} else if strings.Contains(text, "bearish") || strings.Contains(text, "weakness") || strings.Contains(text, "profits") {
			sentiment = "negative"
			score = -0.5 - r.Float64()*0.5
		}

		tweet := TweetData{
			ID:        fmt.Sprintf("tweet_%d", time.Now().UnixNano()+int64(i)),
			Text:      text,
			Author:    fmt.Sprintf("@trader%d", r.Intn(10000)),
			Likes:     r.Intn(1000),
			Retweets:  r.Intn(500),
			Timestamp: time.Now().Add(-time.Duration(r.Intn(24)) * time.Hour),
			Sentiment: sentiment,
			Score:     score,
		}
		tweets = append(tweets, tweet)
	}

	return tweets, nil
}

// AnalyzeInfluencers analyzes sentiment from crypto influencers
// TODO: Implement with curated list of influencers
func (ta *TwitterAnalyzer) AnalyzeInfluencers(symbol string) (map[string]string, error) {
	// In production:
	// 1. Maintain a list of verified crypto influencers
	// 2. Fetch their recent tweets about the symbol
	// 3. Weight their sentiment by follower count
	// 4. Return aggregated influencer sentiment

	coinName, _ := ta.extractCoinNames(symbol)

	influencers := map[string]string{
		"@elonmusk":       "neutral",
		"@VitalikButerin": "positive",
		"@cz_binance":     "positive",
		"@SBF_FTX":        "neutral",
		"@APompliano":     "bullish",
	}

	// Mock: only return relevant influencers
	relevant := make(map[string]string)
	if coinName == "BTC" {
		relevant["@APompliano"] = "bullish"
		relevant["@elonmusk"] = "neutral"
	} else if coinName == "ETH" {
		relevant["@VitalikButerin"] = "positive"
	}

	return relevant, nil
}
