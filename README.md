# 📈 Pine Script Library

A comprehensive project for organizing, tracking, and managing Pine Script files for the TradingView platform. Includes a beautiful web-based interface to view all your scripts with their metadata and backtest performance metrics.

## 🎯 Project Overview

This project provides a complete solution for managing your TradingView Pine Scripts, including:
- Organized directory structure for indicators, strategies, and studies
- JSON-based data storage (no database required)
- Interactive web grid for browsing and searching scripts
- Backtest performance tracking and metrics
- Version control and metadata management

## 📁 Directory Structure

```
pine_scripts/
├── scripts/                 # All Pine Script files
│   ├── indicators/         # Technical indicators (RSI, MACD, etc.)
│   ├── strategies/         # Trading strategies with entry/exit logic
│   └── studies/            # Other analysis tools
├── data/                   # JSON data files
│   ├── scripts.json        # Main database of all scripts
│   └── schema.json         # JSON schema definition
├── web/                    # Web interface
│   ├── index.html         # Main HTML page
│   ├── css/
│   │   └── styles.css     # Styling
│   └── js/
│       └── app.js         # Application logic
├── docs/                   # Documentation and screenshots
├── tests/                  # Test files (optional)
├── .cursorrules           # Cursor AI rules for this project
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## 🚀 Getting Started

### 1. Clone or Initialize Repository
```bash
git init
```

### 2. View the Web Interface
Simply open `web/index.html` in your web browser:
```bash
# Windows
start web/index.html

# macOS
open web/index.html

# Linux
xdg-open web/index.html
```

Or use a local server (recommended):
```bash
# Python 3
python -m http.server 8000

# Node.js (with http-server)
npx http-server -p 8000

# Then navigate to: http://localhost:8000/web/
```

### 3. Add Your Pine Scripts

1. Save your Pine Script files in the appropriate directory:
   - Indicators → `scripts/indicators/`
   - Strategies → `scripts/strategies/`
   - Studies → `scripts/studies/`

2. Add metadata to `data/scripts.json` (see schema below)

3. Refresh the web interface to see your new scripts

## 📊 JSON Schema

The `data/scripts.json` file stores all metadata about your scripts. Here's the structure:

### Required Fields
- `id`: Unique identifier (e.g., "rsi-divergence-indicator")
- `name`: Display name
- `type`: "indicator", "strategy", or "study"
- `version`: Version number (e.g., "1.0.0")
- `filePath`: Relative path to the .pine file
- `dateCreated`: ISO 8601 timestamp

### Optional Fields
- `description`: What the script does
- `author`: Your name
- `tags`: Array of searchable tags
- `timeframes`: Recommended timeframes (e.g., ["1h", "4h"])
- `parameters`: Input parameters with defaults
- `backtest`: Performance metrics (see below)
- `status`: "active", "testing", "deprecated", or "archived"
- `notes`: Additional information

### Backtest Object (for strategies)
```json
{
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
  "notes": "Additional context"
}
```

## 🎨 Web Interface Features

### Main Grid
- **Sortable columns**: Click headers to sort by any metric
- **Search**: Find scripts by name, description, or tags
- **Filters**: Filter by type, status
- **Stats Dashboard**: Overview of your script collection
- **Color-coded metrics**: Green (good), yellow (neutral), red (poor)

### Metrics Displayed
- Win Rate (%)
- Profit Factor
- Net Profit (%)
- Max Drawdown (%)
- Total Trades
- Last Modified Date

### Actions
- **View**: See full details in a modal popup
- **Copy Path**: Copy file path to clipboard

## 🔧 Adding a New Script

### Step 1: Create the Pine Script
Create your script file in the appropriate folder:
```
scripts/strategies/my-strategy.pine
```

### Step 2: Add Metadata Entry
Add an entry to `data/scripts.json`:

```json
{
  "id": "my-strategy",
  "name": "My Trading Strategy",
  "type": "strategy",
  "version": "1.0.0",
  "pineVersion": 5,
  "description": "A description of what this strategy does",
  "filePath": "scripts/strategies/my-strategy.pine",
  "dateCreated": "2026-01-08T12:00:00Z",
  "dateModified": "2026-01-08T12:00:00Z",
  "author": "Your Name",
  "tags": ["trend", "momentum"],
  "timeframes": ["1h", "4h"],
  "status": "active",
  "parameters": [
    {
      "name": "length",
      "type": "int",
      "default": 14,
      "description": "Period length"
    }
  ],
  "backtest": {
    "symbol": "BTCUSD",
    "timeframe": "4h",
    "startDate": "2024-01-01",
    "endDate": "2025-12-31",
    "initialCapital": 10000,
    "netProfit": 1500,
    "netProfitPercent": 15,
    "totalTrades": 30,
    "winningTrades": 20,
    "losingTrades": 10,
    "winRate": 66.67,
    "profitFactor": 2.1,
    "maxDrawdown": -8.5,
    "avgTrade": 50
  }
}
```

### Step 3: Test in TradingView
1. Open your script file
2. Copy the code
3. Paste into TradingView Pine Editor
4. Run backtest and record results
5. Update the backtest object in `scripts.json`

## 📝 Pine Script Best Practices

### File Naming
- Use lowercase with hyphens: `my-indicator.pine`
- Be descriptive: `rsi-divergence-detector.pine`
- Include type if not in a subfolder: `strategy-ema-cross.pine`

### Script Header Template
```pine
//@version=5
strategy("My Strategy Name", 
     overlay=true,
     default_qty_type=strategy.percent_of_equity,
     default_qty_value=10)

// ============================================================================
// DESCRIPTION
// ============================================================================
// Brief description of what this script does
//
// AUTHOR: Your Name
// VERSION: 1.0.0
// DATE: 2026-01-08
//
// PARAMETERS:
// - length: Description of parameter
// - threshold: Description of parameter
//
// USAGE:
// Explain how to use this script
// ============================================================================

// Your code here...
```

### Version Control
- Use semantic versioning: `MAJOR.MINOR.PATCH`
- Increment MAJOR for breaking changes
- Increment MINOR for new features
- Increment PATCH for bug fixes
- Update both the script file and `scripts.json`

## 🔍 Searching and Filtering

The web interface supports:
- **Text search**: Searches name, description, and tags
- **Type filter**: Show only indicators, strategies, or studies
- **Status filter**: Show only active, testing, deprecated, or archived scripts
- **Sorting**: By name, date modified, or any performance metric

## 📈 Backtest Metrics Guide

### Key Metrics to Track

1. **Win Rate**: Percentage of winning trades
   - Good: >60%
   - Average: 50-60%
   - Poor: <50%

2. **Profit Factor**: Gross profit / Gross loss
   - Excellent: >2.0
   - Good: 1.5-2.0
   - Average: 1.0-1.5
   - Poor: <1.0

3. **Max Drawdown**: Largest peak-to-trough decline
   - Good: <10%
   - Average: 10-20%
   - Poor: >20%

4. **Sharpe Ratio**: Risk-adjusted return
   - Excellent: >2.0
   - Good: 1.0-2.0
   - Average: 0.5-1.0
   - Poor: <0.5

## 🛠️ Customization

### Adding New Metadata Fields

1. Update `data/schema.json` with the new field
2. Add the field to your script entries in `data/scripts.json`
3. Modify `web/js/app.js` to display the field
4. Update `web/index.html` if adding a new column

### Styling

All styles are in `web/css/styles.css`. The design uses CSS custom properties (variables) for easy theming:

```css
:root {
    --primary-color: #2962ff;
    --secondary-color: #00bcd4;
    --success-color: #4caf50;
    /* ... etc ... */
}
```

## 🤝 Contributing

When adding scripts to this repository:
1. Follow the directory structure
2. Add complete metadata
3. Include backtest results for strategies
4. Use descriptive tags
5. Document your code
6. Test in TradingView before committing

## 📄 License

This project structure is free to use and modify for personal or commercial purposes.

## 🆘 Troubleshooting

### Web Interface Not Loading Scripts
- Check that `data/scripts.json` exists and is valid JSON
- Use a local server instead of opening the HTML file directly
- Check browser console for errors

### Scripts Not Appearing
- Verify the JSON entry is inside the "scripts" array
- Check that all required fields are present
- Validate JSON syntax

### Backtest Data Not Showing
- Ensure the script type is "strategy"
- Verify the backtest object has the required fields
- Check that numeric values are numbers, not strings

## 🎓 Resources

- [Pine Script Documentation](https://www.tradingview.com/pine-script-docs/)
- [TradingView Pine Script Reference](https://www.tradingview.com/pine-script-reference/v5/)
- [Pine Script Style Guide](https://www.tradingview.com/pine-script-docs/en/v5/writing/Style_guide.html)

---

**Happy Trading! 📊📈**
