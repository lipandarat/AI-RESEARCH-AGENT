# 🧪 Testing Guide for NOFX Trading System

## Overview

This guide explains how to run tests for the NOFX trading system to ensure code quality and catch regressions.

---

## 🚀 Quick Start

### Run All Tests

```bash
# Run all tests
go test ./...

# Run with verbose output
go test -v ./...

# Run with coverage
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

---

## 📦 Test Organization

Tests are organized by package:

```
nofx/
├── api/            - API endpoint tests
│   ├── server_test.go
│   └── utils_test.go
├── config/         - Configuration tests
│   └── database_test.go
├── trader/         - Trading logic tests
│   ├── auto_trader_test.go
│   ├── binance_futures_test.go
│   ├── hyperliquid_trader_test.go
│   └── aster_trader_test.go
├── market/         - Market data tests
│   └── data_test.go
├── crypto/         - Encryption tests
│   └── encryption_test.go
└── analytics/      - Analytics module tests (new)
    ├── sentiment/
    └── patterns/
```

---

## 🎯 Running Specific Tests

### By Package

```bash
# API tests
go test ./api/...

# Trader tests
go test ./trader/...

# Database tests
go test ./config/...

# Analytics tests (new modules)
go test ./analytics/sentiment/...
go test ./analytics/patterns/...
```

### By Test Name

```bash
# Run specific test
go test -run TestServerInitialization ./api/...

# Run tests matching pattern
go test -run ^TestTrader ./trader/...
```

### With Race Detection

```bash
# Detect race conditions
go test -race ./...

# Specific package with race detection
go test -race ./trader/...
```

---

## 📊 Coverage Analysis

### Generate Coverage Report

```bash
# Generate coverage profile
go test -coverprofile=coverage.out ./...

# View coverage in terminal
go tool cover -func=coverage.out

# Generate HTML report
go tool cover -html=coverage.out -o coverage.html

# Open in browser
open coverage.html  # macOS
xdg-open coverage.html  # Linux
start coverage.html  # Windows
```

### Coverage by Package

```bash
# API coverage
go test -cover ./api/...

# Trader coverage
go test -cover ./trader/...

# Overall coverage summary
go test -cover ./... | grep coverage
```

---

## 🔍 Test Categories

### Unit Tests

Test individual functions and methods in isolation.

```bash
# Example: Database operations
go test -v -run TestDatabase ./config/...
```

### Integration Tests

Test interaction between components.

```bash
# Example: API + Database
go test -v -run TestIntegration ./api/...
```

### End-to-End Tests

Test complete workflows.

```bash
# Example: Complete trading cycle
go test -v -run TestE2E ./trader/...
```

---

## 🐛 Debugging Failing Tests

### Verbose Output

```bash
# Show all test output
go test -v ./path/to/package/...

# Show only failures
go test ./... 2>&1 | grep -A 10 FAIL
```

### Run Single Test

```bash
# Run one test for debugging
go test -v -run TestSpecificFunction ./package/...

# With timeout
go test -v -run TestSpecificFunction -timeout 30s ./package/...
```

### Test with Environment Variables

```bash
# Set test database path
TEST_DB_PATH=/tmp/test.db go test ./config/...

# Enable debug logging
DEBUG=true go test -v ./...
```

---

## 📝 Writing Tests

### Test File Naming

```go
// For file: trader.go
// Test file: trader_test.go
```

### Basic Test Structure

```go
package trader

import (
    "testing"
)

func TestTraderInitialization(t *testing.T) {
    // Arrange
    config := &TraderConfig{
        InitialBalance: 1000.0,
        Leverage:       5,
    }

    // Act
    trader, err := NewTrader(config)

    // Assert
    if err != nil {
        t.Fatalf("Failed to create trader: %v", err)
    }

    if trader.Balance != 1000.0 {
        t.Errorf("Expected balance 1000.0, got %.2f", trader.Balance)
    }
}
```

### Table-Driven Tests

```go
func TestCalculateProfit(t *testing.T) {
    tests := []struct {
        name     string
        entry    float64
        exit     float64
        quantity float64
        expected float64
    }{
        {"Profit Long", 100, 110, 1.0, 10.0},
        {"Loss Long", 100, 90, 1.0, -10.0},
        {"Profit Short", 110, 100, 1.0, 10.0},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            result := CalculateProfit(tt.entry, tt.exit, tt.quantity)
            if result != tt.expected {
                t.Errorf("Expected %.2f, got %.2f", tt.expected, result)
            }
        })
    }
}
```

---

## 🔄 Continuous Integration

### GitHub Actions

Tests run automatically on every PR:

```yaml
# .github/workflows/pr-go-test-coverage.yml
name: Go Test Coverage

on: [pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-go@v4
        with:
          go-version: '1.21'
      - run: go test -race -coverprofile=coverage.out ./...
      - run: go tool cover -func=coverage.out
```

### Coverage Thresholds

Minimum coverage requirements:
- **Overall**: 70%
- **Critical packages** (trader, decision): 80%
- **API endpoints**: 75%

---

## 🛠️ Test Utilities

### Mock Data

```go
// test_utils.go
func CreateMockTrader() *Trader {
    return &Trader{
        ID:      "test_trader",
        Balance: 1000.0,
        Leverage: 5,
    }
}

func CreateMockCandles() []Candle {
    return []Candle{
        {Time: time.Now(), Open: 50000, High: 51000, Low: 49500, Close: 50500},
        // ... more candles
    }
}
```

### Test Database

```go
func setupTestDB(t *testing.T) *Database {
    db, err := NewDatabase(":memory:")  // SQLite in-memory
    if err != nil {
        t.Fatalf("Failed to create test DB: %v", err)
    }
    t.Cleanup(func() { db.Close() })
    return db
}
```

---

## 📋 Test Checklist

Before submitting PR, ensure:

- [ ] All tests pass: `go test ./...`
- [ ] No race conditions: `go test -race ./...`
- [ ] Coverage meets minimum: `go test -cover ./...`
- [ ] New features have tests
- [ ] Edge cases covered
- [ ] Error cases tested
- [ ] Integration tests pass
- [ ] CI/CD checks pass

---

## 🚨 Common Test Failures

### 1. Database Connection Errors

```bash
# Solution: Use test database
TEST_DB_PATH=":memory:" go test ./config/...
```

### 2. Network Timeouts

```bash
# Solution: Increase timeout
go test -timeout 60s ./...
```

### 3. Race Conditions

```bash
# Solution: Run with race detector to identify
go test -race -run TestSpecific ./package/...
```

### 4. Missing Test Dependencies

```bash
# Solution: Install dependencies
go mod download
go mod tidy
```

---

## 📈 Performance Testing

### Benchmarks

```bash
# Run benchmarks
go test -bench=. ./...

# With memory profiling
go test -bench=. -benchmem ./...

# Specific benchmark
go test -bench=BenchmarkCalculateProfit ./trader/...
```

### Writing Benchmarks

```go
func BenchmarkPatternDetection(b *testing.B) {
    detector := patterns.NewDetector()
    candles := CreateMockCandles(100)

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        detector.DetectPatterns("BTCUSDT", candles, "4h")
    }
}
```

---

## 🔗 Additional Resources

- [Go Testing Package Documentation](https://pkg.go.dev/testing)
- [Table Driven Tests in Go](https://dave.cheney.net/2019/05/07/prefer-table-driven-tests)
- [Go Test Comments](https://github.com/golang/go/wiki/TestComments)

---

**Last Updated**: 2025-11-11
**Maintainer**: NOFX Development Team
