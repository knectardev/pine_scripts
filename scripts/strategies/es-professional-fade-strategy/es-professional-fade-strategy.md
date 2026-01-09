# ES Professional Fade Strategy

## Overview
A mean-reversion strategy that trades overnight gaps on the ES futures contract, fading extreme moves at market open.

## Current Version: v2.5.4

## Strategy Logic
- Identifies significant overnight gaps (configurable threshold)
- Waits for opening range formation
- Fades failed attempts to maintain overnight highs/lows
- Uses $TICK breadth indicator as trend veto
- Includes execution penalty modeling for realistic slippage at market open

## Key Parameters

### Gap Detection
- **Min Gap %**: Minimum overnight gap size (default: 0.20%)
- **Opening Range**: Length in minutes (5/15/30 min options)
- **ATR Filter**: Normalizes gap size against volatility

### Risk Management
- **Max Hold Bars**: Maximum position duration in 5-minute bars (default: 24)
- **Max Trades Per Day**: Limits daily trade count (default: 2)
- **Target**: Return to prior RTH close
- **Stop**: Overnight high/low

### Breadth Filter
- **TICK Filter**: $TICK extreme threshold (default: ±700)
- **TICK Lookback**: Number of bars to check for extremes (default: 5)
- **TICK Veto Count**: Required extreme readings to veto trade (default: 3)

### Execution Model
- **Exec Penalty**: Points added to entry price near open (default: 0.50)
- **Penalty Window**: Time window after open for penalty (default: 30 mins)

## Session Settings
- **RTH Session**: 09:30 - 16:00 ET
- **Timezone**: America/New_York

## Backtest Configuration
- **Initial Capital**: $50,000
- **Position Size**: 1 contract
- **Commission**: $2.01 per contract

## Version History
See `archive/` folder for historical versions with detailed change logs.

## Performance Notes
- Best in high-volatility, mean-reverting markets
- Struggles on strong trend days (mitigated by $TICK veto)
- Opening slippage modeling improves backtest realism

## Usage
1. Copy the `.pine` file contents to TradingView Pine Editor
2. Apply to ES1! chart (5-minute timeframe recommended)
3. Adjust parameters based on market regime
4. Review backtest results before live trading

## Last Updated
2026-01-08
