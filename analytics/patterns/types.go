package patterns

import "time"

// PatternType represents different chart pattern types
type PatternType string

const (
	// Chart Patterns
	HeadAndShoulders       PatternType = "head_and_shoulders"
	InverseHeadAndShoulders PatternType = "inverse_head_and_shoulders"
	DoubleTop              PatternType = "double_top"
	DoubleBottom           PatternType = "double_bottom"
	TripleTop              PatternType = "triple_top"
	TripleBottom           PatternType = "triple_bottom"
	AscendingTriangle      PatternType = "ascending_triangle"
	DescendingTriangle     PatternType = "descending_triangle"
	SymmetricalTriangle    PatternType = "symmetrical_triangle"
	RisingWedge            PatternType = "rising_wedge"
	FallingWedge           PatternType = "falling_wedge"
	BullFlag               PatternType = "bull_flag"
	BearFlag               PatternType = "bear_flag"
	BullPennant            PatternType = "bull_pennant"
	BearPennant            PatternType = "bear_pennant"
	Cup AndHandle          PatternType = "cup_and_handle"

	// Candlestick Patterns
	Doji                   PatternType = "doji"
	Hammer                 PatternType = "hammer"
	InvertedHammer         PatternType = "inverted_hammer"
	ShootingStar           PatternType = "shooting_star"
	HangingMan             PatternType = "hanging_man"
	BullishEngulfing       PatternType = "bullish_engulfing"
	BearishEngulfing       PatternType = "bearish_engulfing"
	MorningStar            PatternType = "morning_star"
	EveningStar            PatternType = "evening_star"
	ThreeWhiteSoldiers     PatternType = "three_white_soldiers"
	ThreeBlackCrows        PatternType = "three_black_crows"
	BullishHarami          PatternType = "bullish_harami"
	BearishHarami          PatternType = "bearish_harami"
)

// PatternSignal represents the trading signal from a pattern
type PatternSignal string

const (
	StrongBuy  PatternSignal = "strong_buy"
	Buy        PatternSignal = "buy"
	Neutral    PatternSignal = "neutral"
	Sell       PatternSignal = "sell"
	StrongSell PatternSignal = "strong_sell"
)

// Pattern represents a detected chart pattern
type Pattern struct {
	Type          PatternType   `json:"type"`
	Signal        PatternSignal `json:"signal"`
	Confidence    int           `json:"confidence"`     // 0-100
	Symbol        string        `json:"symbol"`
	Timeframe     string        `json:"timeframe"`      // "1m", "5m", "1h", "4h", "1d"
	DetectedAt    time.Time     `json:"detected_at"`
	StartTime     time.Time     `json:"start_time"`
	EndTime       time.Time     `json:"end_time"`

	// Pattern-specific data
	KeyPoints     []PricePoint  `json:"key_points"`     // Important price levels
	BreakoutLevel float64       `json:"breakout_level"` // Expected breakout price
	TargetPrice   float64       `json:"target_price"`   // Price target
	StopLoss      float64       `json:"stop_loss"`      // Suggested stop loss

	// Pattern metrics
	Height        float64       `json:"height"`         // Pattern height in price
	Width         int           `json:"width"`          // Pattern width in bars
	Volume        []float64     `json:"volume"`         // Volume data

	Description   string        `json:"description"`
	TradingAdvice string        `json:"trading_advice"`
}

// PricePoint represents a key price point in a pattern
type PricePoint struct {
	Time  time.Time `json:"time"`
	Price float64   `json:"price"`
	Label string    `json:"label"` // "left_shoulder", "head", "right_shoulder", etc.
}

// CandlestickPattern represents a candlestick pattern detection
type CandlestickPattern struct {
	Pattern
	Candles []Candle `json:"candles"` // The candles forming the pattern
}

// Candle represents a single candlestick
type Candle struct {
	Time   time.Time `json:"time"`
	Open   float64   `json:"open"`
	High   float64   `json:"high"`
	Low    float64   `json:"low"`
	Close  float64   `json:"close"`
	Volume float64   `json:"volume"`
}

// PatternDetectionResult contains all detected patterns
type PatternDetectionResult struct {
	Symbol            string                `json:"symbol"`
	Timestamp         time.Time             `json:"timestamp"`
	ChartPatterns     []Pattern             `json:"chart_patterns"`
	CandlestickPatterns []CandlestickPattern `json:"candlestick_patterns"`
	OverallSignal     PatternSignal         `json:"overall_signal"`
	Confidence        int                   `json:"confidence"`
	Summary           string                `json:"summary"`
}

// SupportResistance represents support/resistance levels
type SupportResistance struct {
	Symbol      string      `json:"symbol"`
	Support     []PriceLevel `json:"support"`
	Resistance  []PriceLevel `json:"resistance"`
	CurrentPrice float64     `json:"current_price"`
}

// PriceLevel represents a support or resistance level
type PriceLevel struct {
	Price      float64   `json:"price"`
	Strength   int       `json:"strength"`    // 0-100, how strong the level is
	Touches    int       `json:"touches"`     // Number of times price touched this level
	LastTouch  time.Time `json:"last_touch"`
	Type       string    `json:"type"`        // "support", "resistance"
}

// TrendLine represents a trend line
type TrendLine struct {
	StartPoint PricePoint `json:"start_point"`
	EndPoint   PricePoint `json:"end_point"`
	Slope      float64    `json:"slope"`
	Touches    int        `json:"touches"`
	Type       string     `json:"type"` // "support", "resistance"
	Strength   int        `json:"strength"`
}
