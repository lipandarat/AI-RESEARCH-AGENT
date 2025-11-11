package patterns

import (
	"math"
	"time"
)

// CandlestickDetector detects candlestick patterns
type CandlestickDetector struct{}

// NewCandlestickDetector creates a new candlestick pattern detector
func NewCandlestickDetector() *CandlestickDetector {
	return &CandlestickDetector{}
}

// DetectAll detects all candlestick patterns
func (cd *CandlestickDetector) DetectAll(candles []Candle, symbol, timeframe string) []CandlestickPattern {
	patterns := make([]CandlestickPattern, 0)

	if len(candles) < 3 {
		return patterns
	}

	// Single candle patterns
	if p := cd.detectDoji(candles, symbol, timeframe); p != nil {
		patterns = append(patterns, *p)
	}
	if p := cd.detectHammer(candles, symbol, timeframe); p != nil {
		patterns = append(patterns, *p)
	}
	if p := cd.detectShootingStar(candles, symbol, timeframe); p != nil {
		patterns = append(patterns, *p)
	}

	// Two candle patterns
	if p := cd.detectEngulfing(candles, symbol, timeframe); p != nil {
		patterns = append(patterns, *p)
	}
	if p := cd.detectHarami(candles, symbol, timeframe); p != nil {
		patterns = append(patterns, *p)
	}

	// Three candle patterns
	if p := cd.detectMorningStar(candles, symbol, timeframe); p != nil {
		patterns = append(patterns, *p)
	}
	if p := cd.detectEveningStar(candles, symbol, timeframe); p != nil {
		patterns = append(patterns, *p)
	}
	if p := cd.detectThreeWhiteSoldiers(candles, symbol, timeframe); p != nil {
		patterns = append(patterns, *p)
	}
	if p := cd.detectThreeBlackCrows(candles, symbol, timeframe); p != nil {
		patterns = append(patterns, *p)
	}

	return patterns
}

// detectDoji detects doji candlestick pattern
func (cd *CandlestickDetector) detectDoji(candles []Candle, symbol, timeframe string) *CandlestickPattern {
	if len(candles) == 0 {
		return nil
	}

	lastCandle := candles[len(candles)-1]

	// Doji: open and close are very close (within 0.1% of range)
	body := bodySize(lastCandle)
	totalRange := candleRange(lastCandle)

	if totalRange == 0 {
		return nil
	}

	bodyRatio := body / totalRange

	if bodyRatio < 0.05 {
		return &CandlestickPattern{
			Pattern: Pattern{
				Type:          Doji,
				Signal:        Neutral,
				Confidence:    60,
				Symbol:        symbol,
				Timeframe:     timeframe,
				DetectedAt:    time.Now(),
				StartTime:     lastCandle.Time,
				EndTime:       lastCandle.Time,
				Description:   "十字星形態，表示市場猶豫不決",
				TradingAdvice: "觀望為主，等待方向確認",
			},
			Candles: []Candle{lastCandle},
		}
	}

	return nil
}

// detectHammer detects hammer candlestick pattern
func (cd *CandlestickDetector) detectHammer(candles []Candle, symbol, timeframe string) *CandlestickPattern {
	if len(candles) == 0 {
		return nil
	}

	lastCandle := candles[len(candles)-1]

	// Hammer criteria:
	// 1. Small body at top of range
	// 2. Long lower shadow (at least 2x body)
	// 3. Little to no upper shadow

	body := bodySize(lastCandle)
	lower := lowerShadow(lastCandle)
	upper := upperShadow(lastCandle)
	totalRange := candleRange(lastCandle)

	if totalRange == 0 || body == 0 {
		return nil
	}

	// Lower shadow should be at least 2x the body
	// Upper shadow should be small
	// Body should be in upper half of range
	if lower >= 2*body && upper < body*0.3 {
		return &CandlestickPattern{
			Pattern: Pattern{
				Type:          Hammer,
				Signal:        Buy,
				Confidence:    70,
				Symbol:        symbol,
				Timeframe:     timeframe,
				DetectedAt:    time.Now(),
				StartTime:     lastCandle.Time,
				EndTime:       lastCandle.Time,
				Description:   "錘子線形態，看漲反轉信號",
				TradingAdvice: "等待下一根K線確認後做多",
			},
			Candles: []Candle{lastCandle},
		}
	}

	return nil
}

// detectShootingStar detects shooting star candlestick pattern
func (cd *CandlestickDetector) detectShootingStar(candles []Candle, symbol, timeframe string) *CandlestickPattern {
	if len(candles) == 0 {
		return nil
	}

	lastCandle := candles[len(candles)-1]

	body := bodySize(lastCandle)
	lower := lowerShadow(lastCandle)
	upper := upperShadow(lastCandle)
	totalRange := candleRange(lastCandle)

	if totalRange == 0 || body == 0 {
		return nil
	}

	// Shooting star: opposite of hammer
	// Long upper shadow, small body at bottom, little lower shadow
	if upper >= 2*body && lower < body*0.3 {
		return &CandlestickPattern{
			Pattern: Pattern{
				Type:          ShootingStar,
				Signal:        Sell,
				Confidence:    70,
				Symbol:        symbol,
				Timeframe:     timeframe,
				DetectedAt:    time.Now(),
				StartTime:     lastCandle.Time,
				EndTime:       lastCandle.Time,
				Description:   "流星線形態，看跌反轉信號",
				TradingAdvice: "等待下一根K線確認後做空",
			},
			Candles: []Candle{lastCandle},
		}
	}

	return nil
}

// detectEngulfing detects bullish/bearish engulfing pattern
func (cd *CandlestickDetector) detectEngulfing(candles []Candle, symbol, timeframe string) *CandlestickPattern {
	if len(candles) < 2 {
		return nil
	}

	prev := candles[len(candles)-2]
	curr := candles[len(candles)-1]

	// Bullish Engulfing: bearish candle followed by larger bullish candle
	if isBearish(prev) && isBullish(curr) {
		if curr.Open < prev.Close && curr.Close > prev.Open {
			return &CandlestickPattern{
				Pattern: Pattern{
					Type:          BullishEngulfing,
					Signal:        Buy,
					Confidence:    75,
					Symbol:        symbol,
					Timeframe:     timeframe,
					DetectedAt:    time.Now(),
					StartTime:     prev.Time,
					EndTime:       curr.Time,
					Description:   "看漲吞沒形態，強烈看漲信號",
					TradingAdvice: "做多信號，設置止損在前一根K線最低點",
				},
				Candles: []Candle{prev, curr},
			}
		}
	}

	// Bearish Engulfing: bullish candle followed by larger bearish candle
	if isBullish(prev) && isBearish(curr) {
		if curr.Open > prev.Close && curr.Close < prev.Open {
			return &CandlestickPattern{
				Pattern: Pattern{
					Type:          BearishEngulfing,
					Signal:        Sell,
					Confidence:    75,
					Symbol:        symbol,
					Timeframe:     timeframe,
					DetectedAt:    time.Now(),
					StartTime:     prev.Time,
					EndTime:       curr.Time,
					Description:   "看跌吞沒形態，強烈看跌信號",
					TradingAdvice: "做空信號，設置止損在前一根K線最高點",
				},
				Candles: []Candle{prev, curr},
			}
		}
	}

	return nil
}

// detectHarami detects bullish/bearish harami pattern
func (cd *CandlestickDetector) detectHarami(candles []Candle, symbol, timeframe string) *CandlestickPattern {
	if len(candles) < 2 {
		return nil
	}

	prev := candles[len(candles)-2]
	curr := candles[len(candles)-1]

	prevBody := bodySize(prev)
	currBody := bodySize(curr)

	// Harami: large candle followed by small candle inside its body
	if currBody < prevBody*0.5 {
		// Bullish Harami: large bearish candle + small bullish candle
		if isBearish(prev) && isBullish(curr) &&
			curr.Open > prev.Close && curr.Close < prev.Open {
			return &CandlestickPattern{
				Pattern: Pattern{
					Type:          BullishHarami,
					Signal:        Buy,
					Confidence:    65,
					Symbol:        symbol,
					Timeframe:     timeframe,
					DetectedAt:    time.Now(),
					StartTime:     prev.Time,
					EndTime:       curr.Time,
					Description:   "看漲孕線形態，溫和看漲信號",
					TradingAdvice: "等待確認後做多",
				},
				Candles: []Candle{prev, curr},
			}
		}

		// Bearish Harami: large bullish candle + small bearish candle
		if isBullish(prev) && isBearish(curr) &&
			curr.Open < prev.Close && curr.Close > prev.Open {
			return &CandlestickPattern{
				Pattern: Pattern{
					Type:          BearishHarami,
					Signal:        Sell,
					Confidence:    65,
					Symbol:        symbol,
					Timeframe:     timeframe,
					DetectedAt:    time.Now(),
					StartTime:     prev.Time,
					EndTime:       curr.Time,
					Description:   "看跌孕線形態，溫和看跌信號",
					TradingAdvice: "等待確認後做空",
				},
				Candles: []Candle{prev, curr},
			}
		}
	}

	return nil
}

// detectMorningStar detects morning star pattern (bullish reversal)
func (cd *CandlestickDetector) detectMorningStar(candles []Candle, symbol, timeframe string) *CandlestickPattern {
	if len(candles) < 3 {
		return nil
	}

	c1 := candles[len(candles)-3] // Large bearish candle
	c2 := candles[len(candles)-2] // Small candle (star)
	c3 := candles[len(candles)-1] // Large bullish candle

	// Morning Star criteria:
	// 1. First candle: large bearish
	// 2. Second candle: small body (gap down)
	// 3. Third candle: large bullish closing above midpoint of first

	if !isBearish(c1) || !isBullish(c3) {
		return nil
	}

	body1 := bodySize(c1)
	body2 := bodySize(c2)
	body3 := bodySize(c3)

	// Star should be small
	if body2 > body1*0.3 || body2 > body3*0.3 {
		return nil
	}

	// Third candle should close above midpoint of first
	midpoint := (c1.Open + c1.Close) / 2
	if c3.Close > midpoint {
		return &CandlestickPattern{
			Pattern: Pattern{
				Type:          MorningStar,
				Signal:        StrongBuy,
				Confidence:    80,
				Symbol:        symbol,
				Timeframe:     timeframe,
				DetectedAt:    time.Now(),
				StartTime:     c1.Time,
				EndTime:       c3.Time,
				Description:   "早晨之星形態，強烈看漲反轉信號",
				TradingAdvice: "做多信號，設置止損在形態最低點",
			},
			Candles: []Candle{c1, c2, c3},
		}
	}

	return nil
}

// detectEveningStar detects evening star pattern (bearish reversal)
func (cd *CandlestickDetector) detectEveningStar(candles []Candle, symbol, timeframe string) *CandlestickPattern {
	if len(candles) < 3 {
		return nil
	}

	c1 := candles[len(candles)-3] // Large bullish candle
	c2 := candles[len(candles)-2] // Small candle (star)
	c3 := candles[len(candles)-1] // Large bearish candle

	if !isBullish(c1) || !isBearish(c3) {
		return nil
	}

	body1 := bodySize(c1)
	body2 := bodySize(c2)
	body3 := bodySize(c3)

	// Star should be small
	if body2 > body1*0.3 || body2 > body3*0.3 {
		return nil
	}

	// Third candle should close below midpoint of first
	midpoint := (c1.Open + c1.Close) / 2
	if c3.Close < midpoint {
		return &CandlestickPattern{
			Pattern: Pattern{
				Type:          EveningStar,
				Signal:        StrongSell,
				Confidence:    80,
				Symbol:        symbol,
				Timeframe:     timeframe,
				DetectedAt:    time.Now(),
				StartTime:     c1.Time,
				EndTime:       c3.Time,
				Description:   "黃昏之星形態，強烈看跌反轉信號",
				TradingAdvice: "做空信號，設置止損在形態最高點",
			},
			Candles: []Candle{c1, c2, c3},
		}
	}

	return nil
}

// detectThreeWhiteSoldiers detects three white soldiers pattern (bullish)
func (cd *CandlestickDetector) detectThreeWhiteSoldiers(candles []Candle, symbol, timeframe string) *CandlestickPattern {
	if len(candles) < 3 {
		return nil
	}

	c1 := candles[len(candles)-3]
	c2 := candles[len(candles)-2]
	c3 := candles[len(candles)-1]

	// All three candles should be bullish
	if !isBullish(c1) || !isBullish(c2) || !isBullish(c3) {
		return nil
	}

	// Each candle should close higher than the previous
	if c2.Close <= c1.Close || c3.Close <= c2.Close {
		return nil
	}

	// Each candle should have significant body
	avgBody := (bodySize(c1) + bodySize(c2) + bodySize(c3)) / 3
	minBody := avgBody * 0.7

	if bodySize(c1) < minBody || bodySize(c2) < minBody || bodySize(c3) < minBody {
		return nil
	}

	return &CandlestickPattern{
		Pattern: Pattern{
			Type:          ThreeWhiteSoldiers,
			Signal:        StrongBuy,
			Confidence:    85,
			Symbol:        symbol,
			Timeframe:     timeframe,
			DetectedAt:    time.Now(),
			StartTime:     c1.Time,
			EndTime:       c3.Time,
			Description:   "三個白兵形態，強烈看漲延續信號",
			TradingAdvice: "做多信號，趨勢強勁",
		},
		Candles: []Candle{c1, c2, c3},
	}
}

// detectThreeBlackCrows detects three black crows pattern (bearish)
func (cd *CandlestickDetector) detectThreeBlackCrows(candles []Candle, symbol, timeframe string) *CandlestickPattern {
	if len(candles) < 3 {
		return nil
	}

	c1 := candles[len(candles)-3]
	c2 := candles[len(candles)-2]
	c3 := candles[len(candles)-1]

	// All three candles should be bearish
	if !isBearish(c1) || !isBearish(c2) || !isBearish(c3) {
		return nil
	}

	// Each candle should close lower than the previous
	if c2.Close >= c1.Close || c3.Close >= c2.Close {
		return nil
	}

	// Each candle should have significant body
	avgBody := (bodySize(c1) + bodySize(c2) + bodySize(c3)) / 3
	minBody := avgBody * 0.7

	if bodySize(c1) < minBody || bodySize(c2) < minBody || bodySize(c3) < minBody {
		return nil
	}

	return &CandlestickPattern{
		Pattern: Pattern{
			Type:          ThreeBlackCrows,
			Signal:        StrongSell,
			Confidence:    85,
			Symbol:        symbol,
			Timeframe:     timeframe,
			DetectedAt:    time.Now(),
			StartTime:     c1.Time,
			EndTime:       c3.Time,
			Description:   "三隻烏鴉形態，強烈看跌延續信號",
			TradingAdvice: "做空信號，趨勢強勁",
		},
		Candles: []Candle{c1, c2, c3},
	}
}
