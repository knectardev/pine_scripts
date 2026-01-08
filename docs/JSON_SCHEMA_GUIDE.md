# JSON Schema Quick Reference

This guide provides quick reference for adding scripts to `data/scripts.json`.

## Minimal Required Entry

```json
{
  "id": "my-script",
  "name": "My Script",
  "type": "indicator",
  "version": "1.0.0",
  "filePath": "scripts/indicators/my-script.pine",
  "dateCreated": "2026-01-08T12:00:00Z"
}
```

## Complete Entry (All Fields)

```json
{
  "id": "complete-example",
  "name": "Complete Example Script",
  "type": "strategy",
  "version": "1.0.0",
  "pineVersion": 5,
  "description": "A complete example with all fields populated",
  "filePath": "scripts/strategies/complete-example.pine",
  "dateCreated": "2026-01-08T12:00:00Z",
  "dateModified": "2026-01-08T14:30:00Z",
  "author": "Your Name",
  "tags": ["trend", "momentum", "swing-trading"],
  "timeframes": ["1h", "4h", "1D"],
  "status": "active",
  "tradingviewUrl": "https://www.tradingview.com/script/...",
  "notes": "General notes about the script",
  "parameters": [
    {
      "name": "length",
      "type": "int",
      "default": 14,
      "description": "Period length for calculations"
    },
    {
      "name": "source",
      "type": "string",
      "default": "close",
      "description": "Price source to use"
    }
  ],
  "backtest": {
    "symbol": "BTCUSD",
    "timeframe": "4h",
    "startDate": "2023-01-01",
    "endDate": "2025-12-31",
    "initialCapital": 10000,
    "netProfit": 2450.50,
    "netProfitPercent": 24.51,
    "totalTrades": 45,
    "winningTrades": 28,
    "losingTrades": 17,
    "winRate": 62.22,
    "profitFactor": 1.85,
    "maxDrawdown": -12.5,
    "avgTrade": 54.46,
    "avgWinningTrade": 145.80,
    "avgLosingTrade": -85.20,
    "sharpeRatio": 1.42,
    "notes": "Backtest performed with default parameters"
  }
}
```

## Field Reference

### Core Fields (Required)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | string | Unique identifier (slug format) | `"rsi-divergence"` |
| `name` | string | Display name | `"RSI Divergence Detector"` |
| `type` | string | Script type | `"indicator"`, `"strategy"`, or `"study"` |
| `version` | string | Version number | `"1.0.0"` |
| `filePath` | string | Relative path to file | `"scripts/indicators/rsi.pine"` |
| `dateCreated` | string | ISO 8601 timestamp | `"2026-01-08T12:00:00Z"` |

### Optional Core Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `pineVersion` | integer | Pine Script version | `5` |
| `description` | string | Detailed description | `"Detects divergences..."` |
| `dateModified` | string | ISO 8601 timestamp | `"2026-01-08T14:30:00Z"` |
| `author` | string | Author name | `"John Doe"` |
| `status` | string | Current status | `"active"`, `"testing"`, `"deprecated"`, `"archived"` |
| `notes` | string | General notes | `"Works best in..."` |
| `tradingviewUrl` | string | Published script URL | `"https://..."` |

### Arrays

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `tags` | array[string] | Searchable tags | `["rsi", "divergence", "reversal"]` |
| `timeframes` | array[string] | Recommended timeframes | `["1h", "4h", "1D"]` |
| `parameters` | array[object] | Input parameters | See parameters section |

### Parameters Object

```json
{
  "name": "length",
  "type": "int",
  "default": 14,
  "description": "Period length"
}
```

### Backtest Object (Strategies)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `symbol` | string | Trading pair | `"BTCUSD"` |
| `timeframe` | string | Timeframe used | `"4h"` |
| `startDate` | string | Start date | `"2023-01-01"` |
| `endDate` | string | End date | `"2025-12-31"` |
| `initialCapital` | number | Starting capital | `10000` |
| `netProfit` | number | Total profit/loss | `2450.50` |
| `netProfitPercent` | number | Profit percentage | `24.51` |
| `totalTrades` | integer | Total closed trades | `45` |
| `winningTrades` | integer | Winning trades | `28` |
| `losingTrades` | integer | Losing trades | `17` |
| `winRate` | number | Win percentage | `62.22` |
| `profitFactor` | number | Profit/Loss ratio | `1.85` |
| `maxDrawdown` | number | Max drawdown % | `-12.5` |
| `avgTrade` | number | Avg profit per trade | `54.46` |
| `avgWinningTrade` | number | Avg winning trade | `145.80` |
| `avgLosingTrade` | number | Avg losing trade | `-85.20` |
| `sharpeRatio` | number | Risk-adjusted return | `1.42` |
| `notes` | string | Backtest notes | `"Default params"` |

## Common Tags

```
Trend: "trend", "trend-following", "breakout"
Momentum: "momentum", "rsi", "macd", "stochastic"
Moving Averages: "moving-average", "ema", "sma", "crossover"
Volatility: "volatility", "atr", "bollinger-bands"
Volume: "volume", "volume-profile", "obv"
Patterns: "patterns", "divergence", "support-resistance"
Strategy Types: "scalping", "day-trading", "swing-trading", "position"
Market Conditions: "trending", "ranging", "choppy"
Skill Level: "beginner", "intermediate", "advanced"
```

## Common Timeframes

```
"1m", "3m", "5m", "15m", "30m"      # Minutes
"1h", "2h", "4h", "6h", "12h"       # Hours
"1D", "3D", "1W", "1M"              # Days, Weeks, Months
```

## Validation Checklist

Before adding a script entry:
- [ ] Unique `id` (no duplicates)
- [ ] All required fields present
- [ ] Valid JSON syntax (no trailing commas)
- [ ] Valid ISO 8601 dates
- [ ] Status is one of: active, testing, deprecated, archived
- [ ] Type is one of: indicator, strategy, study
- [ ] File path actually exists
- [ ] Backtest metrics are numbers (not strings)
- [ ] Win rate is between 0-100

## Date Format

Always use ISO 8601 format with timezone:
```
"2026-01-08T12:00:00Z"  # UTC
"2026-01-08T12:00:00-05:00"  # EST
```

Quick way to get current timestamp:
```javascript
new Date().toISOString()
// Output: "2026-01-08T17:30:45.123Z"
```

## Adding Multiple Scripts

When adding multiple scripts, separate them with commas:

```json
{
  "scripts": [
    {
      "id": "script-1",
      ...
    },
    {
      "id": "script-2",
      ...
    },
    {
      "id": "script-3",
      ...
    }
  ]
}
```

**Important**: Don't forget the comma between script objects!
