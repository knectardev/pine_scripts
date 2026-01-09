# Test: Standardized Header System

## Quick Test Procedure

### 1. Start the Server

```bash
cd c:\local_dev\pine_scripts
python server.py
```

### 2. Test RSI Divergence (Script Without Header)

1. **Open Web UI:** http://localhost:5000
2. **Find RSI Divergence Detector** in the grid
3. **Click "Review Code"**
4. **Click "Quick Fix"** button
5. **New version created:** v1.3.18 (or higher)

**Expected Result:**

The new version file should have a **complete standardized header**:

```pine
//@version=6
// =============================================================================
// INDICATOR: RSI Divergence Detector
// FILENAME: rsi-divergence-indicator_v1.3.18.pine
// Version: v1.3.18
// DATE:     2026-01-08
// =============================================================================
// CHANGE LOG:
//   v1.3.18 - Auto-fix: 14 issue(s) fixed
//
//   STRENGTHS: [To be documented]
//   WEAKNESSES: [To be documented]
// =============================================================================
indicator("RSI Divergence Detector", overlay=true)
```

**Verify:**
- ✅ Separator lines present (`====`)
- ✅ Script type shows `INDICATOR`
- ✅ Filename matches actual file
- ✅ Version number correct
- ✅ Date is today
- ✅ Changelog entry present

### 3. Test ES Professional Fade (Script With Header)

1. **Find ES Professional Fade Strategy** in the grid
2. **Click "Review Code"**
3. **Click "Quick Fix"** button
4. **New version created:** v2.5.10 (or higher)

**Expected Result:**

The header should be **updated** (not duplicated):

```pine
//@version=6
// =============================================================================
// STRATEGY: ES Professional Fade
// FILENAME: es-professional-fade-strategy_v2.5.10.pine  ← UPDATED
// Version: v2.5.10  ← UPDATED
// DATE:     2026-01-08  ← UPDATED
// =============================================================================
// CHANGE LOG:
//   v2.5.10 - Auto-fix: 37 issue(s) fixed  ← NEW ENTRY
//   v2.5.4 - Implemented 'Execution Penalty' logic (Slippage simulation).  ← PRESERVED
//          - Added time-decaying friction model (penalty expires after X mins).
//          - Migrated to STOP orders for more realistic fill simulation.
```

**Verify:**
- ✅ Only ONE header (not duplicated)
- ✅ Version updated to v2.5.10
- ✅ Filename updated
- ✅ Date updated
- ✅ New changelog entry at top
- ✅ Old changelog entries preserved

---

## Manual File Verification

### Check RSI Divergence File

```bash
# Navigate to the new version
cd scripts/indicators/rsi-divergence-indicator/archive

# Find the latest version (v1.3.18 or higher)
# Open it in your editor
```

### Check ES Fade File

```bash
# Navigate to ES Fade archive
cd scripts/strategies/es-professional-fade-strategy/es-professional-fade-strategy/v2.5.5/v2.5.6/archive/v2.5.6_v2.5.7/archive/v2.5.6_v2.5.8/archive

# Find the latest version
# Open it in your editor
```

---

## Success Criteria

### ✅ RSI Divergence Test Passes If:
1. New version file has complete header with all sections
2. Header format matches ES Fade format
3. INDICATOR type is correct
4. Changelog entry present
5. Code below header is unchanged

### ✅ ES Fade Test Passes If:
1. Header is updated (not duplicated)
2. Version number incremented
3. New changelog entry prepended
4. Old changelog entries preserved
5. All header fields updated correctly

---

## Troubleshooting

### Issue: No header appears
**Solution:** Check that `//@version=6` is on line 1 of the file

### Issue: Header duplicated
**Solution:** Function should detect existing header - check regex patterns

### Issue: Wrong script type
**Solution:** Verify `scripts.json` has correct `"type": "indicator"` or `"type": "strategy"`

### Issue: Filename doesn't match
**Solution:** Check `get_project_name_from_path()` function

---

## API Testing (Optional)

### Test via API

```bash
# Test RSI Divergence Auto-Fix
curl -X POST http://localhost:5000/api/scripts/example-rsi-divergence-indicator/autofix

# Check response for new version info
```

### Expected API Response

```json
{
  "success": true,
  "newVersion": "1.3.18",
  "fixesApplied": 14,
  "versionInfo": {
    "version": "1.3.18",
    "filePath": "scripts\\indicators\\rsi-divergence-indicator\\...",
    "changelog": "Auto-fix: 14 issue(s) fixed - ..."
  }
}
```

---

## Verification Checklist

- [ ] Server starts without errors
- [ ] Web UI loads correctly
- [ ] RSI Divergence Quick Fix runs
- [ ] RSI Divergence new version has full header
- [ ] ES Fade Quick Fix runs
- [ ] ES Fade header updated correctly
- [ ] No duplicate headers
- [ ] Changelog entries preserved
- [ ] Metadata in scripts.json updated
- [ ] File timestamps updated

---

## Rollback (If Needed)

If tests fail:

```bash
# Stop server
# Restore from backup
python server.py  # Will show restore option

# Or manually restore
cp data/backups/scripts_LATEST.json data/scripts.json
```

---

## Next Steps After Testing

1. ✅ Verify both scripts work
2. ✅ Test with more scripts
3. ✅ Document any issues
4. ✅ Update user guide if needed
5. ✅ Consider enhancements (strengths/weaknesses auto-fill)

---

**Note:** The system is backward compatible. Existing scripts will work normally and get headers on their next version.
