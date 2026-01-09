# 📈 Pine Script Library

A comprehensive project for organizing, tracking, and managing Pine Script files for the TradingView platform. Includes a beautiful web-based interface to view all your scripts with their metadata and backtest performance metrics.

## 🎯 Project Overview

This project provides a **production-quality solution** for managing your TradingView Pine Scripts, including:

### Management & Organization
- ✅ Organized directory structure for indicators, strategies, and studies
- ✅ JSON-based data storage (no database required)
- ✅ Interactive web interface for full CRUD operations
- ✅ Backtest performance tracking and metrics
- ✅ Advanced search and filtering

### Version Control & Code Quality
- ✅ **Automatic version control** with changelog tracking
- ✅ **Comprehensive code review** based on official TradingView standards
- ✅ **Auto-fix system** for common code quality issues
- ✅ **LLM-powered fixes** using OpenAI or Claude
- ✅ **Logic validation** to catch bugs and errors

### Safety & Reliability
- ✅ **Automatic backups** (keeps last 10, with timestamps)
- ✅ **Version history** with restore capability
- ✅ **Data integrity** checks and validation
- ✅ **Error recovery** mechanisms

> **📖 New Users:** Start with [QUICKSTART.md](QUICKSTART.md) for a 2-minute setup guide!  
> **📚 Developers:** See [API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md) for complete API reference  
> **🔍 Code Review:** Check out [CODE_REVIEW_REPORT.md](docs/CODE_REVIEW_REPORT.md) for project assessment

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

### 1. Set Up Virtual Environment (Recommended)

Create and activate a virtual environment to isolate project dependencies:

```bash
# Create virtual environment
python -m venv venv

# Activate it:
# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Windows CMD:
venv\Scripts\activate.bat

# macOS/Linux:
source venv/bin/activate

# You should see (venv) in your terminal prompt
```

### 2. Install Dependencies

Install the required Python packages (with virtual environment activated):

```bash
pip install -r requirements.txt
```

### 2.5. (Optional) Configure LLM Features

For AI-powered code fixes, create a `.env` file in the project root:

```bash
# .env file (create this file)
OPENAI_API_KEY=your_openai_api_key_here
DEFAULT_LLM_PROVIDER=openai
OPENAI_MODEL=gpt-4

# OR use Claude:
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
# DEFAULT_LLM_PROVIDER=anthropic
# CLAUDE_MODEL=claude-3-5-sonnet-20241022
```

> **Note:** LLM features are optional. The app works perfectly without them for manual code reviews and quick-fixes.

### 3. Start the Flask Server

Make sure your virtual environment is activated, then start the server:

```bash
# Make sure (venv) is shown in your prompt, then:
python server.py
```

The server will start at `http://localhost:5000` and you'll see:
```
🚀 Pine Script Library API Server
📍 Server running at: http://localhost:5000
🌐 Open web interface: http://localhost:5000
```

### 4. Open the Web Interface

Navigate to `http://localhost:5000` in your web browser. The interface will automatically load your scripts and provide full Create, Read, Update, Delete functionality.

### 5. Managing Your Pine Scripts

You can now manage your scripts in two ways:

#### Option A: Using the Web Interface (Recommended)
1. Click "**+ Create New Script**" to add a new script
2. Fill in the form with script details and backtest metrics
3. Click "**Edit**" on any script to update its information
4. Click "**Delete**" to remove a script (with confirmation)
5. All changes are automatically saved to `data/scripts.json` with backups

#### Option B: Manual JSON Editing
1. Save Pine Script files in the appropriate directory:
   - Indicators → `scripts/indicators/`
   - Strategies → `scripts/strategies/`
   - Studies → `scripts/studies/`
2. Add metadata entries to `data/scripts.json` (see schema below)
3. Refresh the web interface to see your changes

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

### CRUD Operations
- **Create**: Click "+ Create New Script" to add new entries
- **Read**: Click "View" to see full details in a modal popup
- **Update**: Click "Edit" to modify script information
- **Delete**: Click "Delete" to remove scripts (with confirmation)

### Additional Features
- **Automatic Backups**: Every save creates a timestamped backup in `data/backups/`
- **Smart Backup Management**: Keeps last 10 backups, throttles to prevent spam
- **Validation**: Required fields enforced, data integrity checks
- **Notifications**: Visual feedback for all operations
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Code Review Reports**: Export to PDF or copy to clipboard for LLM analysis
- **Version Control**: Complete history with restore and compare capabilities
- **Auto-Fix**: One-click fixes for common code quality issues

## 🔧 Adding a New Script

### Method 1: Using the Web Interface (Easiest)

1. Click "**+ Create New Script**" button
2. Fill in the required fields:
   - Name (required)
   - Type: Indicator, Strategy, or Study (required)
   - Version (required, defaults to 1.0.0)
   - File Path (required, e.g., `scripts/indicators/my-script.pine`)
3. Add optional details:
   - Description, author, tags, timeframes
   - Backtest metrics (for strategies)
4. Click "**Save Script**"

The script will be automatically added to `data/scripts.json` with timestamps and a backup will be created.

### Method 2: Manual JSON Entry

### Step 1: Create the Pine Script
Create your script file in the appropriate folder:
```
scripts/strategies/my-strategy.pine
```

### Step 2: Add Metadata Entry
Add an entry to `data/scripts.json` or use the web interface:

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
5. Click "Edit" in the web interface and add/update backtest metrics

## 🔐 API Endpoints

The Flask server provides a comprehensive RESTful API. For complete documentation, see [API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md).

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/scripts` | List all scripts |
| GET | `/api/scripts/:id` | Get single script |
| POST | `/api/scripts` | Create new script |
| PUT | `/api/scripts/:id` | Update script |
| DELETE | `/api/scripts/:id` | Delete script |

### Code Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/scripts/:id/code` | Get script code (current or specific version) |
| GET | `/api/scripts/:id/review` | Perform code quality review |
| POST | `/api/scripts/:id/save-code` | Save edited code (creates new version) |
| POST | `/api/scripts/:id/autofix` | Auto-fix single issue |
| POST | `/api/scripts/:id/auto-fix-all` | Auto-fix all fixable issues |
| POST | `/api/scripts/:id/smart-autofix` | LLM-powered intelligent fixes |

### Version Control

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/scripts/:id/versions` | Get version history |
| POST | `/api/scripts/:id/versions/:v/restore` | Restore previous version |

### Backups

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/backups` | List available backups |
| POST | `/api/backups/:file` | Restore from backup |

### Example API Usage

```bash
# Get all scripts
curl http://localhost:5000/api/scripts

# Create a new script
curl -X POST http://localhost:5000/api/scripts \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Strategy",
    "type": "strategy",
    "version": "1.0.0",
    "filePath": "scripts/strategies/my-strategy.pine"
  }'

# Update a script
curl -X PUT http://localhost:5000/api/scripts/my-strategy-id \
  -H "Content-Type: application/json" \
  -d '{"version": "1.1.0"}'

# Delete a script
curl -X DELETE http://localhost:5000/api/scripts/my-strategy-id
```

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

## 💾 Backups & Data Safety

### Automatic Backups
- Every save operation creates a timestamped backup in `data/backups/`
- The system keeps the last 10 backups automatically
- Backups are named: `scripts_YYYYMMDD_HHMMSS.json`

### Manual Backup
```bash
# Create a manual backup
cp data/scripts.json data/scripts_backup_$(date +%Y%m%d).json
```

### Restore from Backup
Use the API endpoint to restore:
```bash
curl -X POST http://localhost:5000/api/backups/scripts_20260108_120000.json
```

Or manually copy:
```bash
cp data/backups/scripts_20260108_120000.json data/scripts.json
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root for optional configuration:

```bash
# LLM Provider Configuration (optional)
OPENAI_API_KEY=sk-...                           # OpenAI API key
DEFAULT_LLM_PROVIDER=openai                     # 'openai' or 'anthropic'
OPENAI_MODEL=gpt-4                              # OpenAI model name
CLAUDE_MODEL=claude-3-5-sonnet-20241022         # Claude model name

# Anthropic Alternative (optional)
ANTHROPIC_API_KEY=sk-ant-...                    # Anthropic API key
```

> **Security Note:** Never commit `.env` to version control. It's already in `.gitignore`.

### Checking API Configuration

Visit the settings page in the web interface or call:
```bash
curl http://localhost:5000/api/debug/api-key-status
```

## 🛠️ Customization

### Adding New Metadata Fields

1. Update `data/schema.json` with the new field
2. Update the form in `web/index.html` (edit modal)
3. Modify `web/js/app.js` to handle the new field
4. Update the table in `web/index.html` if adding a new column

### Theming

All styles are in `web/css/styles.css`. The design uses CSS custom properties (variables) for easy theming:

```css
:root {
    --primary-color: #2962ff;        /* Blue accent */
    --secondary-color: #00bcd4;      /* Cyan accent */
    --success-color: #4caf50;        /* Green (good metrics) */
    --warning-color: #ff9800;        /* Orange (warnings) */
    --danger-color: #f44336;         /* Red (errors) */
    --dark-bg: #1e1e1e;             /* Main background */
    --card-bg: #2d2d2d;             /* Card background */
    /* ... more variables ... */
}
```

**To create a light theme:** Just change these variables!

## 🚀 Production Deployment

For production use, consider using a production WSGI server:

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 server:app
```

Or use Waitress (Windows-friendly):
```bash
pip install waitress
waitress-serve --port=5000 server:app
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

### Flask Server Won't Start
- Make sure you've installed dependencies: `pip install -r requirements.txt`
- Check that port 5000 is not already in use
- Try a different port: `python server.py` (then edit server.py to change port)

### Web Interface Not Loading Scripts
- Ensure the Flask server is running at `http://localhost:5000`
- Check that `data/scripts.json` exists and is valid JSON
- Check browser console for errors (F12)
- Verify CORS is not blocking requests

### "Cannot create/update/delete scripts"
- Confirm Flask server is running
- Check file permissions on `data/scripts.json`
- Look at server console for error messages
- Ensure `data/backups/` directory exists and is writable

### Scripts Not Appearing After Creating
- Check the server console for errors
- Refresh the page (F5)
- Verify the script was saved in `data/scripts.json`

### Backtest Data Not Showing
- Ensure the script type is "strategy"
- Verify numeric values are entered correctly (not text)
- Check that backtest metrics are numbers, not strings

## 📚 Documentation

### Core Documentation
- **[README.md](README.md)** - This file (project overview and setup)
- **[QUICKSTART.md](QUICKSTART.md)** - Quick reference for daily use
- **[API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)** - Complete API reference
- **[CODE_REVIEW_REPORT.md](docs/CODE_REVIEW_REPORT.md)** - Comprehensive code review

### Pine Script Standards
- **[PINE_SCRIPT_STANDARDS.md](docs/PINE_SCRIPT_STANDARDS.md)** - Official TradingView standards
- **[LOGICAL_SANITY_CHECKS.md](docs/LOGICAL_SANITY_CHECKS.md)** - Logic validation rules
- **[SANITY_CHECKS_QUICK_REF.md](docs/SANITY_CHECKS_QUICK_REF.md)** - Quick reference checklist

### Additional Resources
- **[JSON_SCHEMA_GUIDE.md](docs/JSON_SCHEMA_GUIDE.md)** - Metadata schema documentation
- **[FILE_STRUCTURE_GUIDE.md](docs/FILE_STRUCTURE_GUIDE.md)** - Project organization guide
- **[SCRIPT_DOCUMENTATION_TEMPLATE.md](docs/SCRIPT_DOCUMENTATION_TEMPLATE.md)** - Template for script docs

### External Resources
- [Pine Script Documentation](https://www.tradingview.com/pine-script-docs/)
- [TradingView Pine Script Reference](https://www.tradingview.com/pine-script-reference/v5/)
- [Pine Script Style Guide](https://www.tradingview.com/pine-script-docs/en/v5/writing/Style_guide.html)

## ✨ Features

### Core Features
- ✅ **Full CRUD Operations** - Create, Read, Update, Delete scripts via web interface
- ✅ **Version Control** - Automatic versioning with changelog tracking
- ✅ **Automated Code Review** - Based on official TradingView standards
- ✅ **Auto-Fix System** - Quick fixes for common issues
- ✅ **LLM Integration** - Smart fixes powered by OpenAI/Claude
- ✅ **Backup System** - Automatic backups with restore capability
- ✅ **Search & Filter** - Find scripts by name, tags, type, status
- ✅ **Backtest Tracking** - Record and display strategy performance metrics
- ✅ **Export Capabilities** - PDF export and clipboard copy for code reviews

### Code Quality Features
- ✅ **Pine Script v5/v6 Support** - Both versions fully supported
- ✅ **Comprehensive Validation** - Checks structure, naming, formatting, logic
- ✅ **Performance Analysis** - Detects anti-patterns and optimization opportunities
- ✅ **Logic Sanity Checks** - Validates strategy logic for common errors
- ✅ **Platform Limitations** - Warns about plot limits, loop bounds, etc.

### User Experience
- ✅ **Modern Dark Theme** - Optimized for code viewing
- ✅ **Responsive Design** - Works on desktop, tablet, mobile
- ✅ **Real-time Updates** - Instant feedback on all operations
- ✅ **Syntax Highlighting** - Beautiful code display
- ✅ **Sortable Tables** - Sort by any metric
- ✅ **Visual Metrics** - Color-coded performance indicators

---

**Happy Trading! 📊📈**
