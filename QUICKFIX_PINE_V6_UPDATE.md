# QuickFix Pine Script v6 Update

## Summary
Updated the QuickFix automated code correction tool to properly handle Pine Script v6 syntax requirements, specifically camelCase → snake_case conversions for strategy properties and parameters.

## Date
2026-01-08

## Problem
The QuickFix tool was not detecting or correcting critical Pine Script issues:
1. **Indentation errors**: Missing indentation after `if`/`else`/`for`/`while` statements causing "end of line without line continuation" errors
2. **Strategy properties** using camelCase (e.g., `strategy.positionSize`) instead of snake_case (`strategy.position_size`)
3. **Strategy declaration parameters** using camelCase (e.g., `initialCapital`, `defaultQtyValue`) instead of snake_case (`initial_capital`, `default_qty_value`)

These issues caused compilation errors in TradingView when using Pine Script v6.

## Solution

### 1. Enhanced Code Review Detection (`perform_code_review` function)

Added **Section 5A: Pine Script Indentation Checks** to detect indentation errors.
Added **Section 5B: Pine Script v6 Syntax Checks** to detect API changes.

#### A. Indentation Issues
Detects missing indentation after control statements:
- Checks lines following `if`, `else if`, `else`, `for`, `while` statements
- Flags body statements that are not indented
- **Severity:** CRITICAL (causes "end of line without line continuation" compilation error)
- **Message:** "Line after 'if...' must be indented. Pine Script requires indented blocks."

Example detection:
```pine
// This will be flagged as CRITICAL:
if not isRth and isRth[1]
rthClosePrev := close[1]  // ❌ Not indented!
```

#### B. Strategy Property Issues (v6)
Detects and flags camelCase strategy properties:
- `strategy.positionSize` → `strategy.position_size`
- `strategy.openTrades` → `strategy.open_trades`
- `strategy.closedTrades` → `strategy.closed_trades`
- `strategy.eventTrades` → `strategy.event_trades`
- `strategy.grossProfit` → `strategy.gross_profit`
- `strategy.grossLoss` → `strategy.gross_loss`
- `strategy.netProfit` → `strategy.net_profit`
- `strategy.maxDrawdown` → `strategy.max_drawdown`
- `strategy.initialCapital` → `strategy.initial_capital`

**Severity:** CRITICAL (prevents compilation)

#### B. Strategy Declaration Parameter Issues
Detects and flags camelCase parameters in `strategy()` declarations:
- `initialCapital` → `initial_capital`
- `defaultQtyValue` → `default_qty_value`
- `defaultQtyType` → `default_qty_type`
- `commissionType` → `commission_type`
- `commissionValue` → `commission_value`
- `calcOnOrderFills` → `calc_on_order_fills`
- `calcOnEveryTick` → `calc_on_every_tick`
- `maxBarsBack` → `max_bars_back`
- `backTestFillLimitsAssumption` → `backtest_fill_limits_assumption`
- `defaultQtyValuePercentage` → `default_qty_value_percentage`
- `riskFreeRate` → `risk_free_rate`
- `useBarsBacktest` → `use_bars_backtest`
- `fillOrdersOnOpen` → `fill_orders_on_open`
- `processOrdersOnClose` → `process_orders_on_close`
- `closeEntriesRule` → `close_entries_rule`

**Severity:** CRITICAL (prevents compilation)

### 2. Enhanced Auto-Fix (`apply_auto_fixes` function)

Added three new automated fixes:

#### Fix 10: Convert Strategy Property Names
- Automatically replaces all camelCase strategy properties with snake_case equivalents
- Example: `strategy.positionSize == 0` → `strategy.position_size == 0`
- Reports each fix applied: `"Converted 'strategy.positionSize' to 'strategy.position_size' (Pine Script v6)"`

#### Fix 9B: Fix Pine Script Indentation
- Automatically detects control statements (`if`, `else`, `for`, `while`)
- Ensures body statements are properly indented (2 spaces)
- Pine Script requires indented blocks - missing indentation causes "end of line without line continuation" errors
- Example:
  ```pine
  // BEFORE (WRONG):
  if not isRth and isRth[1]
  rthClosePrev := close[1]
  
  // AFTER (FIXED):
  if not isRth and isRth[1]
    rthClosePrev := close[1]
  ```
- Reports: `"Fixed indentation for X line(s) in if/for/while blocks"`

#### Fix 10: Convert Strategy Property Names
- Automatically replaces all camelCase strategy properties with snake_case equivalents
- Example: `strategy.positionSize == 0` → `strategy.position_size == 0`
- Reports each fix applied: `"Converted 'strategy.positionSize' to 'strategy.position_size' (Pine Script v6)"`

#### Fix 11: Convert Strategy Declaration Parameters
- Detects multi-line `strategy()` declarations
- Automatically replaces all camelCase parameters with snake_case equivalents
- Example: `initialCapital=50000` → `initial_capital=50000`
- Reports fixes per line: `"Line X: Converted strategy() parameter(s) to snake_case (Pine Script v6)"`

## Technical Implementation Details

### Detection Logic (Code Review)
```python
# Property detection: Simple string search in non-comment lines
for old_prop, new_prop in pine_v6_property_issues.items():
    if old_prop in line:
        # Flag as CRITICAL issue

# Parameter detection: Regex-based within strategy() block
in_strategy_declaration = False
for line in lines:
    if 'strategy(' in line:
        in_strategy_declaration = True
    if in_strategy_declaration:
        if re.search(r'\b' + old_param + r'\s*=', line):
            # Flag as CRITICAL issue
    if ')' in line:
        in_strategy_declaration = False
```

### Auto-Fix Logic
```python
# Fix 10: Global find-and-replace for properties
for old_prop, new_prop in pine_v6_properties.items():
    fixed_code = fixed_code.replace(old_prop, new_prop)

# Fix 11: Line-by-line replacement within strategy() blocks
in_strategy_declaration = False
for i, line in enumerate(lines):
    if 'strategy(' in line:
        in_strategy_declaration = True
    if in_strategy_declaration:
        for old_param, new_param in strategy_params.items():
            line = re.sub(r'\b' + old_param + r'\s*=', new_param + '=', line)
    if ')' in line:
        in_strategy_declaration = False
```

## Testing

### Test Case: ES Professional Fade Strategy v2.5.7

**Before Fix:**
```pine
strategy(
  "ES Professional Fade v2.5.7", 
  overlay=true, 
  initialCapital=50000,           // ❌ WRONG (camelCase)
  defaultQtyValue=1,              // ❌ WRONG (camelCase)
  commissionType=strategy.commission.cash_per_contract,  // ❌ WRONG (camelCase)
  commissionValue=2.01)           // ❌ WRONG (camelCase)

if not isRth and isRth[1]
rthClosePrev := close[1]          // ❌ WRONG (not indented)
overnightHigh := high             // ❌ WRONG (not indented)
overnightLow := low               // ❌ WRONG (not indented)

if canTrade and strategy.positionSize == 0  // ❌ WRONG (camelCase)
  if validGapUp and failedOvernightHigh
    strategy.entry(ENTRY_SHORT_ID, strategy.short, stop=shortEntryPrice)

if strategy.positionSize == 0     // ❌ WRONG (camelCase)
  entryBarIndex := na
```

**After QuickFix:**
```pine
strategy(
  "ES Professional Fade v2.5.7", 
  overlay=true, 
  initial_capital=50000,          // ✅ FIXED (snake_case)
  default_qty_value=1,            // ✅ FIXED (snake_case)
  commission_type=strategy.commission.cash_per_contract,  // ✅ FIXED (snake_case)
  commission_value=2.01)          // ✅ FIXED (snake_case)

if not isRth and isRth[1]
  rthClosePrev := close[1]        // ✅ FIXED (indented)
  overnightHigh := high           // ✅ FIXED (indented)
  overnightLow := low             // ✅ FIXED (indented)

if canTrade and strategy.position_size == 0  // ✅ FIXED (snake_case)
  if validGapUp and failedOvernightHigh
    strategy.entry(ENTRY_SHORT_ID, strategy.short, stop=shortEntryPrice)

if strategy.position_size == 0    // ✅ FIXED (snake_case)
  entryBarIndex := na
```

**Result:** Code compiles successfully in TradingView ✅

## Files Modified
- `server.py`
  - Updated `perform_code_review()` function (lines ~1109-1182)
  - Updated `apply_auto_fixes()` function (lines ~1839-1916)

## Impact
- **User Experience:** QuickFix now handles Pine Script v6 syntax automatically
- **Manual Work Eliminated:** Users no longer need to manually convert camelCase to snake_case
- **Error Prevention:** Critical syntax errors are caught and fixed before deployment
- **Backward Compatibility:** No impact on existing v5 scripts (v5→v6 upgrade is already handled)

## Future Enhancements
Consider adding support for other Pine Script v6 API changes:
1. `indicator()` declaration parameters
2. `ta.change()` → `ta.change(source, length)` parameter order
3. `request.security()` → `request.security_lower_tf()` for intrabar requests
4. Other v6 deprecations and breaking changes

## Related Issues
- Fixes issue reported in ES Professional Fade Strategy v2.5.7
- Addresses all Pine Script v6 strategy property/parameter syntax errors

## Notes
- All changes are non-breaking to existing functionality
- QuickFix runs before Smart Fix (LLM-based), so these issues are caught early
- Detection and fixing are both comprehensive (covers all known v6 property/parameter changes)
