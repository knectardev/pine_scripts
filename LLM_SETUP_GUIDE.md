# 🤖 LLM Smart Auto-Fix Setup Guide

## Overview

The Smart Auto-Fix feature uses AI (OpenAI GPT-4) to intelligently fix complex Pine Script issues that simple regex-based fixes cannot handle, including:

- **B8**: `ta.*` function scoping issues (refactors code to move functions to global scope)
- **D1**: Variable reset logic (adds appropriate reset conditions)
- **B6**: Pyramiding logic mismatches (adds position size checks)
- And other complex logical issues

## Quick Setup (3 Steps)

### Step 1: Install Dependencies

```bash
# Activate your virtual environment if not already active
.\venv\Scripts\activate  # Windows PowerShell
# Or: source venv/bin/activate  # Linux/Mac

# Install new dependencies
pip install -r requirements.txt
```

### Step 2: Configure API Key

**Option A: Server-Side Key (Recommended for personal use)**

1. Copy the example environment file:
   ```bash
   # You'll need to create .env file manually since it's gitignored
   # Use the env.example as a template
   ```

2. Create a new file named `.env` in the project root (same directory as `server.py`)

3. Add your OpenAI API key to `.env`:
   ```env
   OPENAI_API_KEY=sk-your-actual-api-key-here
   DEFAULT_LLM_PROVIDER=openai
   OPENAI_MODEL=gpt-4
   ```

4. Get your API key from: https://platform.openai.com/api-keys

**Option B: Client-Side Key (For shared servers)**

1. Start the Flask server normally
2. Open the web interface
3. Click the **⚙️ Settings** button in the top-right
4. Enter your OpenAI API key
5. Click **Save Settings**

Your API key is stored only in your browser's localStorage and never saved to any server or database.

### Step 3: Restart the Server

```bash
# Stop the current server (Ctrl+C) and restart
python server.py
```

## Using Smart Auto-Fix

1. Open any Pine Script in the web interface
2. Click **🔍 Code Review**
3. If there are CRITICAL or HIGH issues, you'll see two buttons:
   - **🔧 Quick Fix**: Regex-based fixes (fast, free, handles formatting)
   - **✨ Smart Fix (LLM)**: AI-powered fixes (slower, requires API, handles complex logic)

4. Click **✨ Smart Fix (LLM)**
5. Wait 5-15 seconds for the AI to analyze and fix the code
6. Review the changes and new version created

## Cost & Performance

| Aspect | Quick Fix | Smart Fix (LLM) |
|--------|-----------|-----------------|
| **Speed** | <100ms | 5-15 seconds |
| **Cost** | Free | ~$0.01-0.10 per fix |
| **Issues Fixed** | Formatting, spacing, simple patterns | Complex logic, scoping, variable management |
| **Code Quality** | Pattern-based | Context-aware |

## Security & Privacy

✅ **Your API key is secure:**
- Server-side keys are stored in `.env` (gitignored, never committed)
- Client-side keys are stored in browser localStorage only
- Keys are transmitted only to OpenAI via HTTPS
- No keys are saved to databases or log files

✅ **Your code is secure:**
- Code is sent to OpenAI API for analysis only
- OpenAI's data usage policy: https://openai.com/policies/api-data-usage-policies
- No code is stored or logged by this application

## Troubleshooting

### "No API key configured" error

- **If using server-side key**: Make sure `.env` file exists with `OPENAI_API_KEY=sk-...`
- **If using client-side key**: Open Settings and enter your API key

### "LLM fix failed: API key not configured"

- Server-side key is not set, and client didn't provide a key
- Either create `.env` file or uncheck "Use server-configured API key" in Settings

### "Error: Invalid API key"

- Check that your API key starts with `sk-`
- Verify the key is active at https://platform.openai.com/api-keys
- Make sure you have credits/billing set up in your OpenAI account

### Smart Fix button doesn't appear

- Smart Fix only appears when there are CRITICAL or HIGH severity issues
- Try Quick Fix first if you only have warnings or formatting issues

## Advanced Configuration

### Change LLM Model

Edit `.env`:
```env
# Use GPT-4 Turbo (faster, cheaper)
OPENAI_MODEL=gpt-4-turbo-preview

# Use GPT-3.5 (much cheaper, less accurate)
OPENAI_MODEL=gpt-3.5-turbo
```

### Use Different Provider (Future)

Anthropic Claude support is planned:
```env
DEFAULT_LLM_PROVIDER=claude
CLAUDE_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

## Need Help?

- Check the OpenAI API status: https://status.openai.com/
- Review your API usage: https://platform.openai.com/usage
- Check the Flask server logs for detailed error messages
