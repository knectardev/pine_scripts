# Quick Start Guide

## Installation (One-Time Setup)

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate it (Windows PowerShell):
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt
```

## Daily Usage

```bash
# 1. Activate virtual environment (Windows PowerShell):
.\venv\Scripts\Activate.ps1

# 2. Start the Flask server
python server.py
```

## 3. Open Your Browser

Navigate to: **http://localhost:5000**

## What You Can Do

### ✅ Create Scripts
- Click "**+ Create New Script**" button
- Fill in the form
- Save

### ✅ Edit Scripts  
- Click "**Edit**" on any row
- Modify fields
- Save changes

### ✅ Delete Scripts
- Click "**Delete**" on any row
- Confirm deletion

### ✅ View Details
- Click "**View**" to see full information
- Including backtest metrics and parameters

### ✅ Search & Filter
- Use the search box for keywords
- Filter by Type (Strategy/Indicator/Study)
- Filter by Status (Active/Testing/etc)
- Sort by any column

## Backups

Every change automatically creates a backup in `data/backups/`

## Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.

---

**That's it! You're ready to manage your Pine Scripts!** 📈
