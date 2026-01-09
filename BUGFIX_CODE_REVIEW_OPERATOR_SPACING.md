# Bug Fix: Code Review False Positives for Operator Spacing

## Problem Report

User reported that after running QuickFix:
- QuickFix reports "fixes applied successfully"
- Code Review still shows operator spacing warnings
- Warnings appear on lines that **already have correct spacing**

Example false positives:
```pine
Line 44: const string RTH_SESSION = "0930-1600:1234567"  ⚠️ WARNING (incorrect)
Line 45: const string TIMEZONE = "America/New_York"      ⚠️ WARNING (incorrect)
Line 18: "ES Professional Fade v2.5.4 (...)", overlay=true ⚠️ WARNING (incorrect)
```

These lines all have **correct spacing** around `=` but were being flagged!

## Root Cause

The Code Review operator spacing checker was **matching operators inside string literals**:

```python
# OLD CODE (BUGGY)
if re.search(r'[a-zA-Z0-9_][+\-*/=<>!]+[a-zA-Z0-9_]', line):
    issues.append({'check': 'Operator Spacing', ...})
```

This regex would match:
- `"0930-1600"` → Matches `0-1` (dash operator)
- `"America/New_York"` → Matches `a/N` (slash operator)
- `"v2.5.4"` → Might match dot patterns

The checker didn't distinguish between:
- **Code**: `float x=5` ❌ (should flag)
- **String**: `"2025-10-01"` ✅ (should NOT flag)

## Solution

### Step 1: Strip String Literals Before Checking

```python
# Remove string literals to avoid false positives
line_without_strings = re.sub(r'"[^"]*"', '""', line)
line_without_strings = re.sub(r"'[^']*'", "''", line_without_strings)

# Now check for operators
if re.search(r'[a-zA-Z0-9_][+\-*/=<>!]+[a-zA-Z0-9_]', line_without_strings):
    # Only flag if it's in actual code, not strings
```

**Result**: `const string RTH_SESSION = "0930-1600:1234567"` becomes `const string RTH_SESSION = ""`  
Now the regex only sees `RTH_SESSION = ""` which has correct spacing! ✅

### Step 2: Skip Function Parameters

Function parameters **correctly** have no spaces:
```pine
input.float(0.20, step=0.05, minval=0.1)  ✅ CORRECT
```

Added check to skip parameters:
```python
# Skip lines with function parameters (after comma or paren)
if not re.search(r'[,(]\s*\w+=[^=]', line_without_strings):
    # Only then flag as issue
```

## Testing

**Test Input:**
```pine
const string RTH_SESSION = "0930-1600:1234567"          # Correct - should NOT flag
const string TIMEZONE = "America/New_York"               # Correct - should NOT flag
float gapMinPctInput = input.float(0.20, step=0.05)     # Correct - should NOT flag

float rsiPivotLow=ta.pivotlow(rsiValue, lookback)       # Incorrect - SHOULD flag
var float lastPivotHigh=na                              # Incorrect - SHOULD flag
```

**Test Results:**
```
✅ Correctly flagged lines WITH errors (no spaces)
✅ Did NOT flag lines with correct spacing
✅ Did NOT flag operators in strings
✅ Did NOT flag function parameters
```

## Impact

### Before Fix:
- ❌ False positives on every line with date strings
- ❌ False positives on timezone strings
- ❌ False positives on version strings
- ❌ Users confused why "fixed" code still shows warnings
- ❌ QuickFix appeared broken

### After Fix:
- ✅ Only flags actual spacing issues in code
- ✅ Ignores operators inside strings
- ✅ Ignores function parameters (correctly formatted)
- ✅ Code Review results match actual code quality
- ✅ QuickFix + Code Review work in harmony

## Files Modified

1. `server.py` - Fixed `perform_code_review()` operator spacing check (line ~883-906)

## Related Fixes

This is the **third fix** in the Code Review/QuickFix sync issues:
1. **Fix #1**: Code Review now reads from currentVersion (not main file)
2. **Fix #2**: Accept both Pine Script v5 and v6
3. **Fix #3**: Don't flag operators inside strings ← THIS FIX

## Date
2026-01-08
