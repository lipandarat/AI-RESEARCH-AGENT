package patterns

import (
	"math"
	"time"
)

// ChartPatternDetector detects chart patterns
type ChartPatternDetector struct{}

// NewChartPatternDetector creates a new chart pattern detector
func NewChartPatternDetector() *ChartPatternDetector {
	return &ChartPatternDetector{}
}

// DetectAll detects all chart patterns
func (cpd *ChartPatternDetector) DetectAll(candles []Candle, symbol, timeframe string) []Pattern {
	patterns := make([]Pattern, 0)

	// Detect various patterns
	if p := cpd.detectDoubleTop(candles, symbol, timeframe); p != nil {
		patterns = append(patterns, *p)
	}
	if p := cpd.detectDoubleBottom(candles, symbol, timeframe); p != nil {
		patterns = append(patterns, *p)
	}
	if p := cpd.detectHeadAndShoulders(candles, symbol, timeframe); p != nil {
		patterns = append(patterns, *p)
	}
	if p := cpd.detectTriangle(candles, symbol, timeframe); p != nil {
		patterns = append(patterns, *p)
	}
	if p := cpd.detectWedge(candles, symbol, timeframe); p != nil {
		patterns = append(patterns, *p)
	}
	if p := cpd.detectFlag(candles, symbol, timeframe); p != nil {
		patterns = append(patterns, *p)
	}

	return patterns
}

// detectDoubleTop detects double top pattern
func (cpd *ChartPatternDetector) detectDoubleTop(candles []Candle, symbol, timeframe string) *Pattern {
	if len(candles) < 30 {
		return nil
	}

	// Find peaks
	peaks := findPeaks(candles, 5)
	if len(peaks) < 2 {
		return nil
	}

	// Look for two peaks at similar heights
	for i := 0; i < len(peaks)-1; i++ {
		peak1 := peaks[i]
		peak2 := peaks[i+1]

		// Peaks should be within 2% of each other
		priceDiff := math.Abs(peak1.Price-peak2.Price) / peak1.Price
		if priceDiff > 0.02 {
			continue
		}

		// Find the valley between peaks
		valleys := findValleys(candles, 3)
		var neckline float64
		for _, v := range valleys {
			if v.Time.After(peak1.Time) && v.Time.Before(peak2.Time) {
				neckline = v.Price
				break
			}
		}

		if neckline == 0 {
			continue
		}

		// Calculate pattern metrics
		height := peak1.Price - neckline
		targetPrice := neckline - height

		return &Pattern{
			Type:          DoubleTop,
			Signal:        Sell,
			Confidence:    75,
			Symbol:        symbol,
			Timeframe:     timeframe,
			DetectedAt:    time.Now(),
			StartTime:     peak1.Time,
			EndTime:       peak2.Time,
			KeyPoints:     []PricePoint{peak1, peak2, {Price: neckline, Label: "neckline"}},
			BreakoutLevel: neckline,
			TargetPrice:   targetPrice,
			StopLoss:      peak2.Price * 1.02,
			Height:        height,
			Description:   "雙頂形態檢測到，看跌反轉信號",
			TradingAdvice: "等待價格跌破頸線確認，目標價位在頸線下方等距離",
		}
	}

	return nil
}

// detectDoubleBottom detects double bottom pattern
func (cpd *ChartPatternDetector) detectDoubleBottom(candles []Candle, symbol, timeframe string) *Pattern {
	if len(candles) < 30 {
		return nil
	}

	// Find valleys
	valleys := findValleys(candles, 5)
	if len(valleys) < 2 {
		return nil
	}

	// Look for two valleys at similar depths
	for i := 0; i < len(valleys)-1; i++ {
		valley1 := valleys[i]
		valley2 := valleys[i+1]

		// Valleys should be within 2% of each other
		priceDiff := math.Abs(valley1.Price-valley2.Price) / valley1.Price
		if priceDiff > 0.02 {
			continue
		}

		// Find the peak between valleys (neckline)
		peaks := findPeaks(candles, 3)
		var neckline float64
		for _, p := range peaks {
			if p.Time.After(valley1.Time) && p.Time.Before(valley2.Time) {
				neckline = p.Price
				break
			}
		}

		if neckline == 0 {
			continue
		}

		// Calculate pattern metrics
		height := neckline - valley1.Price
		targetPrice := neckline + height

		return &Pattern{
			Type:          DoubleBottom,
			Signal:        Buy,
			Confidence:    75,
			Symbol:        symbol,
			Timeframe:     timeframe,
			DetectedAt:    time.Now(),
			StartTime:     valley1.Time,
			EndTime:       valley2.Time,
			KeyPoints:     []PricePoint{valley1, valley2, {Price: neckline, Label: "neckline"}},
			BreakoutLevel: neckline,
			TargetPrice:   targetPrice,
			StopLoss:      valley2.Price * 0.98,
			Height:        height,
			Description:   "雙底形態檢測到，看漲反轉信號",
			TradingAdvice: "等待價格突破頸線確認，目標價位在頸線上方等距離",
		}
	}

	return nil
}

// detectHeadAndShoulders detects head and shoulders pattern
func (cpd *ChartPatternDetector) detectHeadAndShoulders(candles []Candle, symbol, timeframe string) *Pattern {
	if len(candles) < 40 {
		return nil
	}

	peaks := findPeaks(candles, 5)
	if len(peaks) < 3 {
		return nil
	}

	// Look for three peaks: left shoulder, head, right shoulder
	for i := 0; i < len(peaks)-2; i++ {
		leftShoulder := peaks[i]
		head := peaks[i+1]
		rightShoulder := peaks[i+2]

		// Head should be higher than shoulders
		if head.Price <= leftShoulder.Price || head.Price <= rightShoulder.Price {
			continue
		}

		// Shoulders should be at similar heights (within 3%)
		shoulderDiff := math.Abs(leftShoulder.Price-rightShoulder.Price) / leftShoulder.Price
		if shoulderDiff > 0.03 {
			continue
		}

		// Find neckline (valleys between peaks)
		valleys := findValleys(candles, 3)
		var neckline float64
		necklineCount := 0
		for _, v := range valleys {
			if v.Time.After(leftShoulder.Time) && v.Time.Before(rightShoulder.Time) {
				neckline += v.Price
				necklineCount++
			}
		}

		if necklineCount == 0 {
			continue
		}
		neckline /= float64(necklineCount)

		// Calculate target
		height := head.Price - neckline
		targetPrice := neckline - height

		keyPoints := []PricePoint{
			{Price: leftShoulder.Price, Time: leftShoulder.Time, Label: "left_shoulder"},
			{Price: head.Price, Time: head.Time, Label: "head"},
			{Price: rightShoulder.Price, Time: rightShoulder.Time, Label: "right_shoulder"},
			{Price: neckline, Label: "neckline"},
		}

		return &Pattern{
			Type:          HeadAndShoulders,
			Signal:        StrongSell,
			Confidence:    85,
			Symbol:        symbol,
			Timeframe:     timeframe,
			DetectedAt:    time.Now(),
			StartTime:     leftShoulder.Time,
			EndTime:       rightShoulder.Time,
			KeyPoints:     keyPoints,
			BreakoutLevel: neckline,
			TargetPrice:   targetPrice,
			StopLoss:      head.Price * 1.02,
			Height:        height,
			Description:   "頭肩頂形態，強烈看跌反轉信號",
			TradingAdvice: "等待價格跌破頸線後做空，目標為頭部到頸線的等距離",
		}
	}

	return nil
}

// detectTriangle detects triangle patterns (ascending, descending, symmetrical)
func (cpd *ChartPatternDetector) detectTriangle(candles []Candle, symbol, timeframe string) *Pattern {
	if len(candles) < 30 {
		return nil
	}

	peaks := findPeaks(candles, 4)
	valleys := findValleys(candles, 4)

	if len(peaks) < 2 || len(valleys) < 2 {
		return nil
	}

	// Calculate trend of highs and lows
	highsSlope := (peaks[len(peaks)-1].Price - peaks[0].Price) / float64(len(peaks))
	lowsSlope := (valleys[len(valleys)-1].Price - valleys[0].Price) / float64(len(valleys))

	// Determine triangle type
	var patternType PatternType
	var signal PatternSignal
	var description string

	if math.Abs(highsSlope) < 0.001 && lowsSlope > 0.001 {
		// Flat top, rising bottom = Ascending Triangle
		patternType = AscendingTriangle
		signal = Buy
		description = "上升三角形，看漲突破形態"
	} else if highsSlope < -0.001 && math.Abs(lowsSlope) < 0.001 {
		// Falling top, flat bottom = Descending Triangle
		patternType = DescendingTriangle
		signal = Sell
		description = "下降三角形，看跌突破形態"
	} else if highsSlope < 0 && lowsSlope > 0 {
		// Both converging = Symmetrical Triangle
		patternType = SymmetricalTriangle
		signal = Neutral
		description = "對稱三角形，等待方向突破"
	} else {
		return nil
	}

	currentPrice := candles[len(candles)-1].Close
	resistance := peaks[len(peaks)-1].Price
	support := valleys[len(valleys)-1].Price

	return &Pattern{
		Type:          patternType,
		Signal:        signal,
		Confidence:    70,
		Symbol:        symbol,
		Timeframe:     timeframe,
		DetectedAt:    time.Now(),
		StartTime:     peaks[0].Time,
		EndTime:       candles[len(candles)-1].Time,
		BreakoutLevel: resistance,
		TargetPrice:   currentPrice + (resistance - support), // Approximate target
		StopLoss:      support * 0.98,
		Height:        resistance - support,
		Description:   description,
		TradingAdvice: "等待價格突破阻力位或跌破支撐位後入場",
	}
}

// detectWedge detects rising and falling wedge patterns
func (cpd *ChartPatternDetector) detectWedge(candles []Candle, symbol, timeframe string) *Pattern {
	// Similar to triangle but both lines slope in same direction
	// Rising wedge: both slope up (bearish)
	// Falling wedge: both slope down (bullish)

	if len(candles) < 30 {
		return nil
	}

	peaks := findPeaks(candles, 4)
	valleys := findValleys(candles, 4)

	if len(peaks) < 2 || len(valleys) < 2 {
		return nil
	}

	highsSlope := (peaks[len(peaks)-1].Price - peaks[0].Price) / float64(len(peaks))
	lowsSlope := (valleys[len(valleys)-1].Price - valleys[0].Price) / float64(len(valleys))

	var patternType PatternType
	var signal PatternSignal

	if highsSlope > 0.001 && lowsSlope > 0.001 && highsSlope > lowsSlope {
		// Rising Wedge (bearish)
		patternType = RisingWedge
		signal = Sell
	} else if highsSlope < -0.001 && lowsSlope < -0.001 && highsSlope > lowsSlope {
		// Falling Wedge (bullish)
		patternType = FallingWedge
		signal = Buy
	} else {
		return nil
	}

	return &Pattern{
		Type:       patternType,
		Signal:     signal,
		Confidence: 65,
		Symbol:     symbol,
		Timeframe:  timeframe,
		DetectedAt: time.Now(),
	}
}

// detectFlag detects bull and bear flag patterns
func (cpd *ChartPatternDetector) detectFlag(candles []Candle, symbol, timeframe string) *Pattern {
	if len(candles) < 20 {
		return nil
	}

	// Flag = sharp move (pole) + small consolidation (flag)
	// Look for strong trend followed by tight range

	// Calculate recent trend strength
	trendStart := len(candles) - 20
	trendEnd := len(candles) - 5
	priceChange := (candles[trendEnd].Close - candles[trendStart].Close) / candles[trendStart].Close

	// Need strong trend (>5%)
	if math.Abs(priceChange) < 0.05 {
		return nil
	}

	// Check consolidation in last 5 candles
	consolidationStart := len(candles) - 5
	consolidationHigh := candles[consolidationStart].High
	consolidationLow := candles[consolidationStart].Low

	for i := consolidationStart; i < len(candles); i++ {
		if candles[i].High > consolidationHigh {
			consolidationHigh = candles[i].High
		}
		if candles[i].Low < consolidationLow {
			consolidationLow = candles[i].Low
		}
	}

	consolidationRange := (consolidationHigh - consolidationLow) / consolidationLow

	// Consolidation should be tight (<3%)
	if consolidationRange > 0.03 {
		return nil
	}

	var patternType PatternType
	var signal PatternSignal

	if priceChange > 0 {
		// Bull Flag
		patternType = BullFlag
		signal = Buy
	} else {
		// Bear Flag
		patternType = BearFlag
		signal = Sell
	}

	return &Pattern{
		Type:       patternType,
		Signal:     signal,
		Confidence: 70,
		Symbol:     symbol,
		Timeframe:  timeframe,
		DetectedAt: time.Now(),
	}
}
