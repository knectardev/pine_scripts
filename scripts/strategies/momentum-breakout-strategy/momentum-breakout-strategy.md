# Momentum Breakout Strategy

## Overview
Sample strategy demonstrating the recommended folder structure. Trades breakouts of Bollinger Band consolidations with volume confirmation.

## Current Version: v1.2.0

## Strategy Logic
- Waits for price to break above/below Bollinger Bands
- Requires volume spike (>1.5x average) for confirmation
- Fixed percentage targets and stops

## Key Parameters
- **BB Length**: Bollinger Band period (default: 20)
- **BB StdDev**: Standard deviation multiplier (default: 2.0)
- **Volume MA**: Moving average for volume baseline (default: 20)
- **Volume Multiplier**: Required volume surge (default: 1.5x)

## Risk Management
- **Long Target**: +2% from entry
- **Long Stop**: -1% from entry
- **Short Target**: -2% from entry
- **Short Stop**: +1% from entry

## Backtest Configuration
- **Initial Capital**: $25,000
- **Position Sizing**: Default (100% of equity)

## Usage Notes
This is a **DEMO/TEST script** to illustrate the recommended folder structure:

```
scripts/
└── strategies/
    └── momentum-breakout-strategy/
        ├── momentum-breakout-strategy.pine    <-- Live file (always current)
        ├── momentum-breakout-strategy.md      <-- This documentation
        └── archive/                           <-- Version history
            ├── momentum-breakout-strategy_v1.0.0.pine
            ├── momentum-breakout-strategy_v1.1.0_volume-filter.pine
            └── momentum-breakout-strategy_v1.2.0.pine
```

## Last Updated
2026-01-08
