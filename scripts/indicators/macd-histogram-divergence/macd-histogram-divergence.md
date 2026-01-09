# MACD Histogram Divergence

## Overview
Sample indicator demonstrating the recommended folder structure. Detects divergences between price action and MACD histogram.

## Current Version: v1.0.0

## Features
- Standard MACD calculation (12/26/9)
- Pivot-based divergence detection
- Visual histogram coloring
- Divergence alerts

## Parameters
- **Fast Length**: Fast EMA period (default: 12)
- **Slow Length**: Slow EMA period (default: 26)
- **Signal Length**: Signal line smoothing (default: 9)
- **Pivot Length**: Lookback for divergence detection (default: 5)

## How It Works
1. Calculates MACD line, signal line, and histogram
2. Identifies pivot highs/lows in price and histogram
3. Compares pivot patterns to detect divergences
4. Alerts when potential divergence patterns form

## Divergence Types
- **Bullish**: Price makes lower low, histogram makes higher low
- **Bearish**: Price makes higher high, histogram makes lower high

## Usage Notes
This is a **DEMO/TEST script** to illustrate the recommended folder structure:

```
scripts/
└── indicators/
    └── macd-histogram-divergence/
        ├── macd-histogram-divergence.pine    <-- Live file
        ├── macd-histogram-divergence.md      <-- This documentation
        └── archive/                          <-- Version history
            └── (future versions here)
```

## Last Updated
2026-01-08
