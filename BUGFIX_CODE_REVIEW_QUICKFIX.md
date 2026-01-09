# Bug Fix: Code Review & QuickFix Not Syncing

## Problem Report
User reported that:
1. QuickFix claims to make changes but Code Review still shows the same warnings
2. Version number warnings persist despite QuickFix upgrading to v6
3. Operator spacing warnings don't get fixed

## Root Cause Analysis

### Issue #1: Different Files Being Read/Written

**QuickFix Behavior:**
- Reads from `currentVersion` (e.g., v2.5.5)
- Applies fixes
- **Creates NEW version** (e.g., v2.5.6)
- Updates `currentVersion` to v2.5.6
- Saves fixed code to versioned file

**Code Review Behavior (BEFORE FIX):**
- **Always read from `filePath`** (the main .pine file)
- Ignored version system completely
- Never saw the fixes QuickFix made to versioned files!

**Result:** QuickFix and Code Review were operating on completely different files!

### Issue #2: Wrong Version Check

Code Review was checking for `//@version=5` only:
```python
if '//@version=5' not in code:
    issues.append({
        'severity': 'CRITICAL',
        'message': 'Script must use //@version=5 declaration'
```

But QuickFix upgrades to v6, so Code Review flagged it as missing!

## Fixes Applied

### Fix #1: Code Review Now Reads from CurrentVersion

**File:** `server.py`  
**Function:** `review_script_code()` (line 674)

**Before:**
```python
else:
    # Get current version
    file_path = script.get('filePath')
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()
```

**After:**
```python
else:
    # Get current version - PRIORITIZE versioned file if it exists
    current_version = script.get('currentVersion')
    
    if current_version and 'versions' in script:
        # Use the versioned file (from version system)
        code, error = get_version_code(script, current_version)
    else:
        # Fall back to main file if no version system
        file_path = script.get('filePath')
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
```

### Fix #2: Accept Both v5 and v6

**File:** `server.py`  
**Function:** `perform_code_review()` (line 722)

**Before:**
- Only accepted `//@version=5`
- Flagged v6 as CRITICAL error

**After:**
```python
has_version_5 = '//@version=5' in code
has_version_6 = '//@version=6' in code

if not has_version_5 and not has_version_6:
    # CRITICAL: Missing version
elif has_version_5:
    # WARNING: Consider upgrading to v6
else:  # has_version_6
    # PASS: Using v6 ✓
```

### Fix #3: GET /code Endpoint Also Reads CurrentVersion

**File:** `server.py`  
**Function:** `get_script_code()` (line 495)

Same fix applied to ensure consistency across all endpoints.

## Testing

### Before Fix:
- Code Review: ❌ "Script must use //@version=5" (CRITICAL)
- Code Review: ⚠️ Multiple operator spacing warnings
- QuickFix: ✅ Claims to fix issues
- Re-run Code Review: ❌ Same warnings appear (reading old file!)

### After Fix:
- Code Review: ✅ Reads from v2.5.6 (currentVersion)
- Code Review: ✅ "Using Pine Script v6 ✓"
- Code Review: ✅ No operator spacing warnings (v2.5.6 already fixed)
- QuickFix: ✅ Creates new version when needed
- Re-run Code Review: ✅ Sees the latest version

## Impact

- ✅ Code Review now syncs with QuickFix changes
- ✅ Version 6 scripts no longer flagged as errors
- ✅ Users can see fixes immediately after QuickFix
- ✅ Version system works correctly
- ✅ No more confusion about "where did my changes go?"

## Files Modified

1. `server.py` - Code Review endpoint (prioritize currentVersion)
2. `server.py` - GET code endpoint (prioritize currentVersion)
3. `server.py` - Version check (accept v5 and v6)

## Recommendations

1. **Clear Communication**: UI should show which version is being reviewed
2. **Version Indicator**: Display "Reviewing v2.5.6" in Code Review modal
3. **Sync Status**: Show if main file differs from current version
4. **Documentation**: Update user docs about version system

## Date
2026-01-08
