package patterns

import (
	"fmt"
	"log"
	"math"
	"time"
)

// Detector is the main pattern detection engine
type Detector struct {
	chartDetector       *ChartPatternDetector
	candlestickDetector *CandlestickDetector
	supportResDetector  *SupportResistanceDetector
}

// NewDetector creates a new pattern detector
func NewDetector() *Detector {
	return &Detector{
		chartDetector:       NewChartPatternDetector(),
		candlestickDetector: NewCandlestickDetector(),
		supportResDetector:  NewSupportResistanceDetector(),
	}
}

// DetectPatterns detects all patterns in price data
func (d *Detector) DetectPatterns(symbol string, candles []Candle, timeframe string) (*PatternDetectionResult, error) {
	if len(candles) < 20 {
		return nil, fmt.Errorf("insufficient data: need at least 20 candles, got %d", len(candles))
	}

	log.Printf("🔍 [Patterns] Detecting patterns for %s (%s timeframe)", symbol, timeframe)

	result := &PatternDetectionResult{
		Symbol:    symbol,
		Timestamp: time.Now(),
	}

	// Detect chart patterns
	chartPatterns := d.chartDetector.DetectAll(candles, symbol, timeframe)
	result.ChartPatterns = chartPatterns
	log.Printf("📊 [Patterns] Found %d chart patterns", len(chartPatterns))

	// Detect candlestick patterns
	candlestickPatterns := d.candlestickDetector.DetectAll(candles, symbol, timeframe)
	result.CandlestickPatterns = candlestickPatterns
	log.Printf("🕯️  [Patterns] Found %d candlestick patterns", len(candlestickPatterns))

	// Determine overall signal
	result.OverallSignal, result.Confidence = d.calculateOverallSignal(chartPatterns, candlestickPatterns)
	result.Summary = d.generateSummary(result)

	log.Printf("✅ [Patterns] Overall signal: %s (Confidence: %d%%)", result.OverallSignal, result.Confidence)

	return result, nil
}

// DetectSupportResistance detects support and resistance levels
func (d *Detector) DetectSupportResistance(symbol string, candles []Candle) (*SupportResistance, error) {
	return d.supportResDetector.Detect(symbol, candles)
}

// calculateOverallSignal aggregates signals from all detected patterns
func (d *Detector) calculateOverallSignal(chartPatterns []Pattern, candlestickPatterns []CandlestickPattern) (PatternSignal, int) {
	if len(chartPatterns) == 0 && len(candlestickPatterns) == 0 {
		return Neutral, 0
	}

	// Weighted scoring
	var totalScore float64
	var totalWeight float64

	// Chart patterns (higher weight)
	for _, p := range chartPatterns {
		weight := float64(p.Confidence) / 100.0
		score := d.signalToScore(p.Signal)
		totalScore += score * weight * 1.5 // Chart patterns have 1.5x weight
		totalWeight += weight * 1.5
	}

	// Candlestick patterns (lower weight)
	for _, p := range candlestickPatterns {
		weight := float64(p.Confidence) / 100.0
		score := d.signalToScore(p.Signal)
		totalScore += score * weight
		totalWeight += weight
	}

	if totalWeight == 0 {
		return Neutral, 0
	}

	// Calculate average weighted score
	avgScore := totalScore / totalWeight

	// Convert score back to signal
	signal := d.scoreToSignal(avgScore)
	confidence := int(math.Abs(avgScore))

	return signal, confidence
}

// signalToScore converts signal to numeric score (-100 to +100)
func (d *Detector) signalToScore(signal PatternSignal) float64 {
	switch signal {
	case StrongBuy:
		return 100
	case Buy:
		return 50
	case Neutral:
		return 0
	case Sell:
		return -50
	case StrongSell:
		return -100
	default:
		return 0
	}
}

// scoreToSignal converts numeric score to signal
func (d *Detector) scoreToSignal(score float64) PatternSignal {
	switch {
	case score >= 70:
		return StrongBuy
	case score >= 30:
		return Buy
	case score >= -30 && score < 30:
		return Neutral
	case score >= -70:
		return Sell
	default:
		return StrongSell
	}
}

// generateSummary generates a text summary of pattern detection results
func (d *Detector) generateSummary(result *PatternDetectionResult) string {
	if len(result.ChartPatterns) == 0 && len(result.CandlestickPatterns) == 0 {
		return "未檢測到明顯的圖表或K線形態。"
	}

	summary := fmt.Sprintf("檢測到 %d 個圖表形態和 %d 個K線形態。",
		len(result.ChartPatterns), len(result.CandlestickPatterns))

	// Highlight most significant patterns
	if len(result.ChartPatterns) > 0 {
		// Find highest confidence chart pattern
		maxConf := 0
		var bestPattern Pattern
		for _, p := range result.ChartPatterns {
			if p.Confidence > maxConf {
				maxConf = p.Confidence
				bestPattern = p
			}
		}
		summary += fmt.Sprintf(" 最顯著的圖表形態: %s (%s, 信心度 %d%%)。",
			d.patternTypeName(bestPattern.Type), bestPattern.Signal, bestPattern.Confidence)
	}

	// Overall recommendation
	switch result.OverallSignal {
	case StrongBuy:
		summary += " 綜合分析：強烈看漲信號。"
	case Buy:
		summary += " 綜合分析：看漲信號。"
	case Neutral:
		summary += " 綜合分析：中立信號，建議觀望。"
	case Sell:
		summary += " 綜合分析：看跌信號。"
	case StrongSell:
		summary += " 綜合分析：強烈看跌信號。"
	}

	return summary
}

// patternTypeName returns Chinese name for pattern type
func (d *Detector) patternTypeName(pt PatternType) string {
	names := map[PatternType]string{
		HeadAndShoulders:       "頭肩頂",
		InverseHeadAndShoulders: "頭肩底",
		DoubleTop:              "雙頂",
		DoubleBottom:           "雙底",
		TripleTop:              "三重頂",
		TripleBottom:           "三重底",
		AscendingTriangle:      "上升三角形",
		DescendingTriangle:     "下降三角形",
		SymmetricalTriangle:    "對稱三角形",
		RisingWedge:            "上升楔形",
		FallingWedge:           "下降楔形",
		BullFlag:               "多頭旗形",
		BearFlag:               "空頭旗形",
		BullPennant:            "多頭三角旗",
		BearPennant:            "空頭三角旗",
		CupAndHandle:           "杯柄形態",
		Doji:                   "十字星",
		Hammer:                 "錘子線",
		InvertedHammer:         "倒錘子線",
		ShootingStar:           "流星線",
		HangingMan:             "吊頸線",
		BullishEngulfing:       "看漲吞沒",
		BearishEngulfing:       "看跌吞沒",
		MorningStar:            "早晨之星",
		EveningStar:            "黃昏之星",
		ThreeWhiteSoldiers:     "三個白兵",
		ThreeBlackCrows:        "三隻烏鴉",
		BullishHarami:          "看漲孕線",
		BearishHarami:          "看跌孕線",
	}

	if name, exists := names[pt]; exists {
		return name
	}
	return string(pt)
}

// Helper functions for candle analysis

// isBullish returns true if candle is bullish
func isBullish(c Candle) bool {
	return c.Close > c.Open
}

// isBearish returns true if candle is bearish
func isBearish(c Candle) bool {
	return c.Close < c.Open
}

// bodySize returns the size of candle body
func bodySize(c Candle) float64 {
	return math.Abs(c.Close - c.Open)
}

// upperShadow returns the size of upper shadow
func upperShadow(c Candle) float64 {
	return c.High - math.Max(c.Open, c.Close)
}

// lowerShadow returns the size of lower shadow
func lowerShadow(c Candle) float64 {
	return math.Min(c.Open, c.Close) - c.Low
}

// candleRange returns the total range of candle
func candleRange(c Candle) float64 {
	return c.High - c.Low
}

// findPeaks finds local peaks in price data
func findPeaks(candles []Candle, window int) []PricePoint {
	peaks := make([]PricePoint, 0)

	for i := window; i < len(candles)-window; i++ {
		isPeak := true
		currentHigh := candles[i].High

		// Check if this is a local maximum
		for j := i - window; j <= i+window; j++ {
			if j != i && candles[j].High >= currentHigh {
				isPeak = false
				break
			}
		}

		if isPeak {
			peaks = append(peaks, PricePoint{
				Time:  candles[i].Time,
				Price: candles[i].High,
				Label: "peak",
			})
		}
	}

	return peaks
}

// findValleys finds local valleys in price data
func findValleys(candles []Candle, window int) []PricePoint {
	valleys := make([]PricePoint, 0)

	for i := window; i < len(candles)-window; i++ {
		isValley := true
		currentLow := candles[i].Low

		// Check if this is a local minimum
		for j := i - window; j <= i+window; j++ {
			if j != i && candles[j].Low <= currentLow {
				isValley = false
				break
			}
		}

		if isValley {
			valleys = append(valleys, PricePoint{
				Time:  candles[i].Time,
				Price: candles[i].Low,
				Label: "valley",
			})
		}
	}

	return valleys
}
