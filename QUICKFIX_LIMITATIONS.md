# QuickFix Capabilities & Limitations

## Overview

**QuickFix** is a regex-based automated fixer that handles **simple, mechanical fixes**. It **cannot** fix issues that require code restructuring or logic changes.

## ✅ What QuickFix CAN Fix

### 1. Version Upgrades
```pine
❌ //@version=5
✅ //@version=6
```

### 2. String Constant Spacing
```pine
❌ const string SESSION = "0930 - 1600:1234567"
✅ const string SESSION = "0930-1600:1234567"

❌ const string TIMEZONE = "America / New_York"
✅ const string TIMEZONE = "America/New_York"
```

### 3. Variable Declaration Spacing
```pine
❌ float rsiPivotLow=ta.pivotlow(rsiValue, lookback)
✅ float rsiPivotLow = ta.pivotlow(rsiValue, lookback)

❌ var float lastPivotHigh=na
✅ var float lastPivotHigh = na
```

### 4. Function Parameter Spacing
```pine
❌ input.float(0.20, step = 0.05, minval = 0.1)
✅ input.float(0.20, step=0.05, minval=0.1)

❌ strategy.entry("Long", strategy.long, stop = close)
✅ strategy.entry("Long", strategy.long, stop=close)
```

### 5. Comma Spacing
```pine
❌ ta.sma(close,14)
✅ ta.sma(close, 14)
```

### 6. request.security Parameters
```pine
❌ request.security("NYSE:TICK", timeframe.period, close)
✅ request.security("NYSE:TICK", timeframe.period, close, barmerge.gaps_off, barmerge.lookahead_off)
```

## ❌ What QuickFix CANNOT Fix

### 1. ta.* Function Scoping (CRITICAL) ⚠️

**Issue**: ta.* functions called inside if blocks break Pine Script's internal state.

**Current Code (WRONG):**
```pine
if ta.change(time) or na(pivotHighPrice)
    // logic

if ta.change(time) or na(pivotLowPrice)
    // logic
```

**Required Fix (needs code restructuring):**
```pine
// Move ta.* calls to global scope
timeChanged = ta.change(time)

// Now use the stored value
if timeChanged or na(pivotHighPrice)
    // logic

if timeChanged or na(pivotLowPrice)
    // logic
```

**Why QuickFix Can't Fix This:**
- Requires identifying ALL ta.* calls in if blocks
- Must create new global variables with appropriate names
- Must replace all references in if blocks
- Requires understanding code flow and context
- **This is a code restructuring task, not a text replacement**

### 2. Variable Reset Logic (HIGH)

**Issue**: `var` variables need reset logic at appropriate boundaries.

**Current Code (WRONG):**
```pine
var float lastPivotHigh = na
var float lastPivotLow = na
// No reset logic - persists forever
```

**Required Fix (needs logic analysis):**
```pine
var float lastPivotHigh = na
var float lastPivotLow = na

// Add reset at appropriate boundary
if isFirstBar or sessionChanged
    lastPivotHigh := na
    lastPivotLow := na
```

**Why QuickFix Can't Fix This:**
- Requires determining WHEN to reset (session? day? bar?)
- Depends on strategy intent (persistent vs session-based)
- Business logic decision, not mechanical fix
- Different variables need different reset conditions

### 3. Complex Logic Issues

QuickFix cannot fix:
- Entry/exit logic problems
- Stop loss/take profit direction issues
- Position sizing errors
- Strategy-specific bugs
- Performance optimizations requiring algorithm changes

## 🤖 Use Smart Fix Instead

For **CRITICAL** issues that QuickFix can't handle, use **Smart Fix** (LLM-powered):

1. Click **"Smart Fix"** button
2. Provide your OpenAI API key (if not configured on server)
3. Smart Fix will:
   - Analyze code structure
   - Move ta.* calls to global scope
   - Add variable reset logic
   - Restructure code while preserving strategy logic

## Expected Behavior

### When You Run QuickFix:

**If only simple issues exist:**
```
✅ Fixed 17 issue(s)! New version: 2.5.7
   - Upgraded version to v6
   - Fixed operator spacing (13 lines)
   - Fixed string constants (3 lines)
```

**If CRITICAL issues remain:**
```
✅ Fixed 13 issue(s)! New version: 2.5.7
⚠️  4 CRITICAL issue(s) require Smart Fix
   - ta.* Function Scoping (4 instances)
   
These issues need code restructuring.
Please use Smart Fix to resolve them.
```

## Summary Table

| Issue Type | Severity | QuickFix | Smart Fix |
|-----------|----------|----------|-----------|
| Version upgrade | WARNING | ✅ Yes | ✅ Yes |
| String spacing | ERROR | ✅ Yes | ✅ Yes |
| Operator spacing | WARNING | ✅ Yes | ✅ Yes |
| Parameter spacing | WARNING | ✅ Yes | ✅ Yes |
| ta.* Scoping | **CRITICAL** | ❌ No | ✅ Yes |
| Variable Reset | HIGH | ❌ No | ✅ Yes |
| Logic errors | CRITICAL | ❌ No | ✅ Yes |

## Recommendations

1. **Always run QuickFix first** - It's fast and fixes simple issues
2. **Check Code Review after QuickFix** - See what remains
3. **Use Smart Fix for CRITICAL issues** - Especially ta.* scoping
4. **Verify changes manually** - Always review before deploying

## Date
2026-01-08
