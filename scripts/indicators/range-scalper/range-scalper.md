# Range Scalper Indicator

## Overview
Identifies range-bound price action and provides entry/exit signals for scalping opportunities within defined support/resistance zones.

## Current Version: v1.0.3

## Features
- **Dynamic Range Detection**: Uses pivot highs/lows to identify support/resistance
- **Range Strength**: Measures range tightness as percentage of price
- **Visual Cues**: Highlights range zones with colored backgrounds
- **Breakout Alerts**: Signals when price breaks range boundaries

## Parameters

### Range Detection
- **Pivot Length**: Lookback period for pivot calculation (default: 10)
- **Range Detection Bars**: Number of bars to analyze for range (default: 20)
- **Range Threshold %**: Maximum range size as % of price (default: 1.5%)

## How It Works
1. Calculates pivot highs and lows to establish resistance and support
2. Measures range size as percentage of current price
3. Highlights when price is trading in a tight range
4. Alerts on breakouts above resistance or below support

## Visual Elements
- **Green Line**: Support level (bottom of range)
- **Red Line**: Resistance level (top of range)
- **Blue Background**: Active range zone
- **Triangle Up**: Bullish breakout
- **Triangle Down**: Bearish breakout

## Best Use Cases
- Sideways/consolidating markets
- Pre-announcement price action
- Low-volatility sessions
- Mean-reversion trading

## Alerts
- **Breakout Up**: Price closes above resistance
- **Breakout Down**: Price closes below support

## Version History
See `archive/` folder for historical versions.

## Last Updated
2026-01-08
