package patterns

import (
	"math"
	"sort"
	"time"
)

// SupportResistanceDetector detects support and resistance levels
type SupportResistanceDetector struct{}

// NewSupportResistanceDetector creates a new S/R detector
func NewSupportResistanceDetector() *SupportResistanceDetector {
	return &SupportResistanceDetector{}
}

// Detect detects support and resistance levels
func (srd *SupportResistanceDetector) Detect(symbol string, candles []Candle) (*SupportResistance, error) {
	if len(candles) < 20 {
		return nil, nil
	}

	currentPrice := candles[len(candles)-1].Close

	// Find support and resistance levels
	support := srd.findSupportLevels(candles, currentPrice)
	resistance := srd.findResistanceLevels(candles, currentPrice)

	return &SupportResistance{
		Symbol:       symbol,
		Support:      support,
		Resistance:   resistance,
		CurrentPrice: currentPrice,
	}, nil
}

// findSupportLevels finds support price levels
func (srd *SupportResistanceDetector) findSupportLevels(candles []Candle, currentPrice float64) []PriceLevel {
	// Find local lows
	valleys := findValleys(candles, 5)

	// Only consider valleys below current price
	var relevantValleys []PricePoint
	for _, v := range valleys {
		if v.Price < currentPrice {
			relevantValleys = append(relevantValleys, v)
		}
	}

	// Cluster nearby price levels
	levels := srd.clusterPriceLevels(relevantValleys, "support")

	// Calculate strength for each level
	for i := range levels {
		levels[i].Strength = srd.calculateLevelStrength(levels[i], candles)
	}

	// Sort by price (descending - closest to current price first)
	sort.Slice(levels, func(i, j int) bool {
		return levels[i].Price > levels[j].Price
	})

	// Return top 5 levels
	if len(levels) > 5 {
		levels = levels[:5]
	}

	return levels
}

// findResistanceLevels finds resistance price levels
func (srd *SupportResistanceDetector) findResistanceLevels(candles []Candle, currentPrice float64) []PriceLevel {
	// Find local highs
	peaks := findPeaks(candles, 5)

	// Only consider peaks above current price
	var relevantPeaks []PricePoint
	for _, p := range peaks {
		if p.Price > currentPrice {
			relevantPeaks = append(relevantPeaks, p)
		}
	}

	// Cluster nearby price levels
	levels := srd.clusterPriceLevels(relevantPeaks, "resistance")

	// Calculate strength for each level
	for i := range levels {
		levels[i].Strength = srd.calculateLevelStrength(levels[i], candles)
	}

	// Sort by price (ascending - closest to current price first)
	sort.Slice(levels, func(i, j int) bool {
		return levels[i].Price < levels[j].Price
	})

	// Return top 5 levels
	if len(levels) > 5 {
		levels = levels[:5]
	}

	return levels
}

// clusterPriceLevels clusters nearby price points into levels
func (srd *SupportResistanceDetector) clusterPriceLevels(points []PricePoint, levelType string) []PriceLevel {
	if len(points) == 0 {
		return []PriceLevel{}
	}

	// Sort points by price
	sort.Slice(points, func(i, j int) bool {
		return points[i].Price < points[j].Price
	})

	levels := make([]PriceLevel, 0)
	currentCluster := []PricePoint{points[0]}

	// Cluster threshold: 1% of price
	threshold := points[0].Price * 0.01

	for i := 1; i < len(points); i++ {
		if points[i].Price-currentCluster[len(currentCluster)-1].Price <= threshold {
			// Add to current cluster
			currentCluster = append(currentCluster, points[i])
		} else {
			// Create level from current cluster
			level := srd.createLevelFromCluster(currentCluster, levelType)
			levels = append(levels, level)

			// Start new cluster
			currentCluster = []PricePoint{points[i]}
		}
	}

	// Don't forget the last cluster
	if len(currentCluster) > 0 {
		level := srd.createLevelFromCluster(currentCluster, levelType)
		levels = append(levels, level)
	}

	return levels
}

// createLevelFromCluster creates a price level from a cluster of points
func (srd *SupportResistanceDetector) createLevelFromCluster(cluster []PricePoint, levelType string) PriceLevel {
	// Calculate average price
	var totalPrice float64
	var latestTime time.Time

	for _, p := range cluster {
		totalPrice += p.Price
		if p.Time.After(latestTime) {
			latestTime = p.Time
		}
	}

	avgPrice := totalPrice / float64(len(cluster))

	return PriceLevel{
		Price:     avgPrice,
		Touches:   len(cluster),
		LastTouch: latestTime,
		Type:      levelType,
	}
}

// calculateLevelStrength calculates strength of a support/resistance level
func (srd *SupportResistanceDetector) calculateLevelStrength(level PriceLevel, candles []Candle) int {
	strength := 0

	// More touches = stronger level (up to +40 points)
	touchesScore := level.Touches * 10
	if touchesScore > 40 {
		touchesScore = 40
	}
	strength += touchesScore

	// Recent touch = stronger (up to +30 points)
	daysSinceTouch := time.Since(level.LastTouch).Hours() / 24
	if daysSinceTouch < 7 {
		strength += 30
	} else if daysSinceTouch < 30 {
		strength += 20
	} else if daysSinceTouch < 90 {
		strength += 10
	}

	// Volume at level = stronger (up to +30 points)
	// Count candles that touched this level with above-average volume
	var totalVolume float64
	var volumeCount int
	highVolumeCount := 0

	for _, c := range candles {
		totalVolume += c.Volume
		volumeCount++
	}

	avgVolume := totalVolume / float64(volumeCount)
	threshold := level.Price * 0.005 // 0.5% threshold

	for _, c := range candles {
		// Check if candle touched the level
		if math.Abs(c.Low-level.Price) < threshold || math.Abs(c.High-level.Price) < threshold {
			if c.Volume > avgVolume*1.2 {
				highVolumeCount++
			}
		}
	}

	volumeScore := highVolumeCount * 10
	if volumeScore > 30 {
		volumeScore = 30
	}
	strength += volumeScore

	// Cap at 100
	if strength > 100 {
		strength = 100
	}

	return strength
}

// FindNearestSupport finds the nearest support level below current price
func (srd *SupportResistanceDetector) FindNearestSupport(sr *SupportResistance) *PriceLevel {
	if len(sr.Support) == 0 {
		return nil
	}

	// Support levels are already sorted by distance from current price
	return &sr.Support[0]
}

// FindNearestResistance finds the nearest resistance level above current price
func (srd *SupportResistanceDetector) FindNearestResistance(sr *SupportResistance) *PriceLevel {
	if len(sr.Resistance) == 0 {
		return nil
	}

	// Resistance levels are already sorted by distance from current price
	return &sr.Resistance[0]
}
