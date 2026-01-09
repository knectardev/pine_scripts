# RSI Divergence Detector

## Overview
Automatically detects bullish and bearish divergences between price action and RSI indicator. Identifies both regular (reversal) and hidden (continuation) divergence patterns.

## Current Version: v1.3.2

## Features
- **Regular Divergences**: Signals potential trend reversals
- **Hidden Divergences**: Signals trend continuation
- **Visual Alerts**: Clear labels on chart at divergence points
- **RSI Panel**: Optional separate RSI display with overbought/oversold zones
- **Multiple Timeframes**: Works on any timeframe

## Divergence Types

### Regular Divergences (Reversal Signals)
- **Bullish Regular**: Price makes lower low, RSI makes higher low → Potential upside reversal
- **Bearish Regular**: Price makes higher high, RSI makes lower high → Potential downside reversal

### Hidden Divergences (Continuation Signals)
- **Bullish Hidden**: Price makes higher low, RSI makes lower low → Uptrend continuation
- **Bearish Hidden**: Price makes lower high, RSI makes higher high → Downtrend continuation

## Parameters
- **RSI Length**: Period for RSI calculation (default: 14)
- **Pivot Lookback**: Bars to look back/forward for pivot detection (default: 5)
- **Show RSI Panel**: Display RSI in separate panel (default: true)

## Visual Elements
- **Green Label (Bull Div)**: Bullish regular divergence
- **Red Label (Bear Div)**: Bearish regular divergence
- **Blue Label (Bull HD)**: Bullish hidden divergence
- **Orange Label (Bear HD)**: Bearish hidden divergence
- **Purple Line**: RSI value (when panel enabled)
- **Red/Green Background**: Overbought/oversold zones

## Best Practices
- Most effective on higher timeframes (1H, 4H, Daily)
- Confirm signals with price action or other indicators
- Regular divergences more reliable at extreme RSI levels
- Hidden divergences work best in strong trends

## Alerts
- Bullish Regular Divergence detected
- Bearish Regular Divergence detected
- Bullish Hidden Divergence detected
- Bearish Hidden Divergence detected

## Usage
1. Apply to any chart and timeframe
2. Adjust RSI Length for faster/slower signals
3. Modify Pivot Lookback for more/fewer detections
4. Enable/disable RSI panel based on preference

## Version History
See `archive/` folder for historical versions.

## Notes
- Divergences are lagging indicators (detected after formation)
- Not all divergences result in reversals/continuations
- Use as confluence with other analysis methods
- Lower timeframes generate more signals but higher false positives

## Last Updated
2026-01-08
