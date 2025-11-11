package sentiment

import "time"

// SentimentData represents comprehensive sentiment analysis for an asset
type SentimentData struct {
	Symbol            string    `json:"symbol"`
	Timestamp         time.Time `json:"timestamp"`
	SentimentScore    float64   `json:"sentiment_score"`     // 0-100 (0=極度悲觀, 50=中立, 100=極度樂觀)
	SentimentTrend    string    `json:"sentiment_trend"`     // "bullish", "bearish", "neutral"
	Confidence        int       `json:"confidence"`          // 0-100
	TwitterMetrics    TwitterMetrics    `json:"twitter_metrics"`
	NewsMetrics       NewsMetrics       `json:"news_metrics"`
	SocialMetrics     SocialMetrics     `json:"social_metrics"`
	FearGreedIndex    int               `json:"fear_greed_index"`    // 0-100
	OverallAssessment string            `json:"overall_assessment"`
}

// TwitterMetrics contains Twitter sentiment metrics
type TwitterMetrics struct {
	Mentions      int     `json:"mentions"`       // 提及次數
	PositiveRatio float64 `json:"positive_ratio"` // 正面推文比例
	NegativeRatio float64 `json:"negative_ratio"` // 負面推文比例
	NeutralRatio  float64 `json:"neutral_ratio"`  // 中立推文比例
	Sentiment     string  `json:"sentiment"`      // "positive", "negative", "neutral"
	TrendingRank  int     `json:"trending_rank"`  // Twitter trending rank (0 if not trending)
}

// NewsMetrics contains news sentiment metrics
type NewsMetrics struct {
	ArticleCount   int     `json:"article_count"`   // 新聞文章數量
	PositiveCount  int     `json:"positive_count"`  // 正面新聞數量
	NegativeCount  int     `json:"negative_count"`  // 負面新聞數量
	NeutralCount   int     `json:"neutral_count"`   // 中立新聞數量
	Sentiment      string  `json:"sentiment"`       // "positive", "negative", "neutral"
	TopHeadlines   []string `json:"top_headlines"`  // 熱門新聞標題
	Sources        []string `json:"sources"`        // 新聞來源
}

// SocialMetrics contains social media metrics from Reddit, Discord, etc.
type SocialMetrics struct {
	RedditMentions    int     `json:"reddit_mentions"`
	RedditSentiment   string  `json:"reddit_sentiment"`
	DiscordMentions   int     `json:"discord_mentions"`
	TelegramMentions  int     `json:"telegram_mentions"`
	OverallSentiment  string  `json:"overall_sentiment"`
	EngagementScore   float64 `json:"engagement_score"`   // 0-100
}

// NewsArticle represents a single news article
type NewsArticle struct {
	Title       string    `json:"title"`
	URL         string    `json:"url"`
	Source      string    `json:"source"`
	PublishedAt time.Time `json:"published_at"`
	Sentiment   string    `json:"sentiment"`      // "positive", "negative", "neutral"
	Score       float64   `json:"score"`          // -1 to 1
	Keywords    []string  `json:"keywords"`
}

// TweetData represents a single tweet
type TweetData struct {
	ID        string    `json:"id"`
	Text      string    `json:"text"`
	Author    string    `json:"author"`
	Likes     int       `json:"likes"`
	Retweets  int       `json:"retweets"`
	Timestamp time.Time `json:"timestamp"`
	Sentiment string    `json:"sentiment"`
	Score     float64   `json:"score"`
}

// FearGreedData represents crypto fear & greed index
type FearGreedData struct {
	Value         int       `json:"value"`          // 0-100
	Classification string    `json:"classification"` // "Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"
	Timestamp     time.Time `json:"timestamp"`
	Components    map[string]float64 `json:"components"` // Breakdown by component
}

// SentimentSignal represents a trading signal based on sentiment
type SentimentSignal struct {
	Symbol     string    `json:"symbol"`
	Signal     string    `json:"signal"`      // "strong_buy", "buy", "neutral", "sell", "strong_sell"
	Strength   int       `json:"strength"`    // 0-100
	Reasoning  string    `json:"reasoning"`
	Timestamp  time.Time `json:"timestamp"`
	Metrics    SentimentData `json:"metrics"`
}
