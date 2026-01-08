# Pine Script Logical Sanity Checks v1.2

## Purpose & Scope

This document defines **first-order logic validation** rules for Pine Script strategies and indicators. These checks catch **bugs, logic inversions, and API misuse** — NOT strategy quality or profitability.

### What This IS:
- ✅ Bug detection (broken logic, impossible conditions, API misuse)
- ✅ "Upside-down logic" detection (stops on wrong side, inverted conditions)
- ✅ Technical correctness validation
- ✅ First-order sanity checking

### What This IS NOT:
- ❌ Strategy evaluation (profitability, win rate, parameter optimization)
- ❌ Trading advice (whether stops are "too tight" or entries are "good")
- ❌ Market analysis (timeframe selection, symbol suitability)
- ❌ Business logic assessment (risk management quality)

### Principle:
**These checks validate that your code does what you intend it to do, not whether what you intend is a good trading idea.**

---

## Severity Definitions

| Level | Meaning | Action |
|-------|---------|--------|
| **CRITICAL** | Code is broken or will behave unexpectedly | Must fix before committing |
| **HIGH** | Likely has bugs or logic errors | Should fix; if intentional, document why |
| **MEDIUM** | May indicate issues; review recommended | Flag for review |
| **WARNING** | Not an error but suspicious or worth noting | User awareness; no action required |

---

## How to Use This Document

### For Daily Reviews:
Use the **Category 9 checklist** in `.cursorrules` for quick validation.

### For Deep Dives:
Reference this document when:
- Creating complex strategies
- Debugging unexpected behavior
- Learning Pine Script best practices
- Resolving flagged issues

### Treatment Guidelines:
- **A, B, C, D, E (CRITICAL):** Must pass or code is broken
- **F (HIGH/MEDIUM):** Must review; fix if confirmed
- **G (WARNING):** Review recommended but not required
- **H (Dev Practice):** Strongly recommended during development

---

## A) Mathematical & Data Invariants (CRITICAL)

These are "should never happen" checks for mathematical impossibilities.

### A1. OHLC Coherence

**Check:** No logic assumes impossible OHLC relationships without explicit documentation.

**Mathematical constraints:**
- `high >= max(open, close)`
- `low <= min(open, close)`
- `high >= low`

**Exception:** If using synthetic bars (Heikin-Ashi, custom calculations), explicitly document this.

**BAD:**
```pine
// ❌ CRITICAL: close can never be > high on standard bars
if close > high
  strategy.entry("Long", strategy.long)

// ❌ CRITICAL: Impossible condition
if high < low
  alert("Alert!")
```

**GOOD:**
```pine
// ✅ If using custom bars, document explicitly
// NOTE: Using Heikin-Ashi bars where close can differ from OHLC
float haClose = (open + high + low + close) / 4

// ✅ Valid comparison with synthetic value
if close > haClose
  strategy.entry("Long", strategy.long)
```

---

### A2. Division Safety

**Check:** No division by values that can be zero or `na` without guards.

**Common risks:** Previous close, ATR, range, volume, denominator calculations.

**BAD:**
```pine
// ❌ CRITICAL: rthClose can be na or 0
gapPct = (open - rthClose) / rthClose

// ❌ CRITICAL: ATR can be 0 on first bars
normalized = price / ta.atr(14)

// ❌ CRITICAL: Volume can be 0
volRatio = volume / volume[1]
```

**GOOD:**
```pine
// ✅ Guard with na check and non-zero
float gapPct = na
if not na(rthClose) and rthClose != 0
  gapPct := (open - rthClose) / rthClose

// ✅ Alternative: Use built-in nz() with safe default
float atrValue = nz(ta.atr(14), 1.0)
float normalized = price / atrValue

// ✅ Guard with conditional
float volRatio = volume[1] != 0 ? volume / volume[1] : na
```

---

### A3. Period Validity

**Check:** All lengths, periods, and lookbacks are positive integers and bounded.

**BAD:**
```pine
// ❌ CRITICAL: Negative period
rsiLength = -14
rsi = ta.rsi(close, rsiLength)

// ❌ CRITICAL: Zero period (will error)
maLength = 0
ma = ta.sma(close, maLength)

// ❌ CRITICAL: Unbounded lookback (can exceed max_bars_back)
lookback = bar_index  // Could be 10,000+
value = close[lookback]
```

**GOOD:**
```pine
// ✅ Enforce minimum with input constraint
int rsiLengthInput = input.int(14, "RSI Length", minval=1)

// ✅ Bound to reasonable range
int lookbackInput = input.int(100, "Lookback", minval=1, maxval=500)

// ✅ Explicit bounds in code
int safeLookback = math.min(bar_index, 200)
float value = close[safeLookback]
```

---

### A4. Percent/Ratio Sanity

**Check:** Percent inputs are bounded (0-100%) unless explicitly documented as allowing >100%.

**BAD:**
```pine
// ❌ CRITICAL: Unbounded percentage (user could enter 500%)
gapPct = input.float(0.5, "Gap Percent")

// ❌ WARNING: 150% commission seems like a mistake
commission_value = 150.0
```

**GOOD:**
```pine
// ✅ Bounded percentage input
float gapPctInput = input.float(0.5, "Gap Percent %", 
  minval=0.0, maxval=100.0, step=0.1)

// ✅ If allowing >100%, document why
float leverageInput = input.float(100.0, "Max Leverage %",
  minval=0.0, maxval=500.0,
  tooltip="Allows >100% for leveraged strategies")

// ✅ Reasonable commission
const float COMMISSION_PER_CONTRACT = 2.01
```

---

### A5. Time/Unit Arithmetic Sanity

**Check:** Time calculations use consistent units; no "magic numbers" for time conversion.

**Common issue:** Mixing milliseconds and minutes without named constants.

**BAD:**
```pine
// ❌ CRITICAL: Magic number 60 (is this seconds? minutes?)
timeSince = (time - rthOpen) / 60

// ❌ CRITICAL: Magic number 60000 (hard to verify correctness)
minutesSince = (time - rthOpen) / 60000

// ❌ CRITICAL: Mixed units without clear conversion
if time > rthOpen + 30  // 30 what? ms? minutes?
```

**GOOD:**
```pine
// ✅ Named constant makes units explicit
const float MILLISECONDS_PER_MINUTE = 60000.0
const float MINUTES_PER_HOUR = 60.0

float minutesSinceOpen = not na(rthOpen) ? 
  (time - rthOpen) / MILLISECONDS_PER_MINUTE : na

// ✅ Guard na and document units
int windowMinutes = 30
int windowMs = windowMinutes * int(MILLISECONDS_PER_MINUTE)
bool inWindow = not na(rthOpen) and time <= (rthOpen + windowMs)
```

---

## B) Pine Semantics & API Correctness (CRITICAL)

These checks validate correct use of Pine Script's built-in functions and constants.

### B1. strategy.entry() Direction Correctness

**Check:** Only uses `strategy.long` or `strategy.short` constants (never inverted or wrong constants).

**BAD:**
```pine
// ❌ CRITICAL: Wrong constant (this is a qty type, not direction)
strategy.entry("Long", strategy.percent_of_equity)

// ❌ CRITICAL: Inverted direction
if bullishSignal
  strategy.entry("Long", strategy.short)  // Wrong direction!

// ❌ CRITICAL: Undefined/typo
strategy.entry("Long", strategy.buy)  // No such constant
```

**GOOD:**
```pine
// ✅ Correct constants
if bullishSignal
  strategy.entry("Long", strategy.long)

if bearishSignal
  strategy.entry("Short", strategy.short)
```

---

### B2. strategy.exit() Coherence

**Check:** Stop/limit parameters are not swapped; no `na` prices without guards.

**BAD:**
```pine
// ❌ CRITICAL: Stop and limit may be swapped (depends on position)
strategy.exit("Exit", stop=targetPrice, limit=stopPrice)

// ❌ CRITICAL: Can pass na as stop price
float stopPrice = overnightLow  // Could be na
strategy.exit("Exit", stop=stopPrice)

// ❌ CRITICAL: Both missing (exit does nothing)
strategy.exit("Exit")
```

**GOOD:**
```pine
// ✅ Clear naming and correct parameter usage
if strategy.position_size > 0  // Long position
  float stopPrice = overnightLow
  float limitPrice = rthClose
  
  if not na(stopPrice) and not na(limitPrice)
    strategy.exit("Exit Long", stop=stopPrice, limit=limitPrice)

// ✅ Alternative: Guard at exit level
float stopPrice = nz(overnightLow, low)
float limitPrice = nz(rthClose, close)
strategy.exit("Exit", stop=stopPrice, limit=limitPrice)
```

---

### B3. Type Compatibility

**Check:** Functions receive correct types; no implicit bool/int confusion.

**BAD:**
```pine
// ❌ CRITICAL: ta.barssince() requires bool, not int
bars = ta.barssince(1)

// ❌ CRITICAL: Comparing bool to int
if (close > open) == 1  // close > open is bool, not int

// ❌ HIGH: Potential type coercion issue
var count = 0  // int
if close > open
  count := true  // Assigning bool to int variable
```

**GOOD:**
```pine
// ✅ Correct: ta.barssince() with boolean
bool isFirstBar = isRth and not isRth[1]
int barsSince = ta.barssince(isFirstBar)

// ✅ Correct: Boolean comparison
if close > open
  // Use boolean directly
  
// ✅ Explicit type declarations avoid confusion
var int count = 0
if close > open
  count := count + 1
```

---

### B4. request.security() Explicitness & Data Persistence

**Check:** `lookahead` parameter is explicit; `gaps` behavior is intentional; data persistence/alignment is handled.

**The Risk - Part 1: Lookahead and Gaps**
Without explicit parameters, `request.security()` can cause repainting and unexpected behavior.

**BAD:**
```pine
// ❌ HIGH: Lookahead not explicit (may cause repainting)
tickValue = request.security("NYSE:TICK", timeframe.period, close)

// ❌ HIGH: Gaps behavior not handled
extValue = request.security("SYMBOL", "D", close)
// What happens if daily bar hasn't closed yet?
```

**The Risk - Part 2: Data Persistence & Alignment**
External security calls can return `na` during:
- First bar of the day
- Market holidays
- Data feed interruptions
- Misaligned trading hours

If your strategy logic doesn't handle these `na` values, the **entire strategy logic can "freeze"** or make incorrect decisions.

**BAD:**
```pine
// ❌ CRITICAL: No fallback for na data
float tickValue = request.security("NYSE:TICK", timeframe.period, close,
  barmerge.gaps_off, barmerge.lookahead_off)

// If TICK data blips, tickValue becomes na
if tickValue > 700  // na > 700 = false (silent failure!)
  // Veto intended but not applied

// ❌ CRITICAL: Arithmetic with na propagates
float tickRatio = tickValue / 1000  // na / 1000 = na
if tickRatio > 0.7  // Condition silently fails

// ❌ CRITICAL: Strategy logic depends on external data without guard
float vixValue = request.security("VIX", timeframe.period, close)
bool highVol = vixValue > 20  // If na, becomes false - wrong assumption!

if not highVol  // Trades during data outage, thinking vol is low!
  strategy.entry("Long", strategy.long)
```

**GOOD (Comprehensive Data Handling):**
```pine
// ✅ Part 1: Explicit parameters
float tickValue = request.security(
  "NYSE:TICK", 
  timeframe.period, 
  close,
  barmerge.gaps_off,     // Explicit
  barmerge.lookahead_off  // Explicit
)

// ✅ Part 2: Explicit na handling with fallback
bool tickValid = not na(tickValue)
bool tickVeto = tickValid ? (tickValue > 700) : true  // Fail-closed

// ✅ Alternative: Use nz() with conservative default
float tickSafe = nz(tickValue, 1500)  // Assume extreme if missing
bool tickVeto = tickSafe > 700

// ✅ Strategy 3: Track last valid value
var float lastValidTick = na
float currentTick = request.security("NYSE:TICK", timeframe.period, close,
  barmerge.gaps_off, barmerge.lookahead_off)

if not na(currentTick)
  lastValidTick := currentTick

// Use last valid value as fallback
float tickForLogic = not na(lastValidTick) ? lastValidTick : na
bool tickValid = not na(tickForLogic)

// ✅ Strategy 4: Fail-safe mode with logging
float vixValue = request.security("VIX", timeframe.period, close,
  barmerge.gaps_off, barmerge.lookahead_off)

bool vixValid = not na(vixValue)
if not vixValid
  log.warning("VIX data unavailable - using fail-safe defaults")

// Explicit decision: fail-closed (conservative) or fail-open (permissive)
bool highVol = vixValid ? (vixValue > 20) : false  // Default: not high vol
// OR
bool highVol = vixValid ? (vixValue > 20) : true   // Default: assume high vol
```

**Detection Criteria:**
- `request.security()` calls without explicit `lookahead` parameter (HIGH)
- `request.security()` calls without explicit `gaps` parameter (HIGH)  
- External data used in logic without `na` checks (CRITICAL)
- No fallback or default values for external data (CRITICAL)
- External data used in arithmetic without guards (CRITICAL)

**Best Practice Pattern:**
```pine
// ✅ Complete data persistence pattern
// Step 1: Declare with explicit parameters
float extData = request.security(
  "SYMBOL", 
  timeframe.period, 
  close,
  barmerge.gaps_off,
  barmerge.lookahead_off
)

// Step 2: Track validity
bool extDataValid = not na(extData)

// Step 3: Maintain last known good value
var float lastValidExtData = na
if extDataValid
  lastValidExtData := extData

// Step 4: Use with fallback logic
float dataForLogic = extDataValid ? extData : 
  not na(lastValidExtData) ? lastValidExtData : 
  close  // Ultimate fallback

// Step 5: Log data health
if not extDataValid
  log.warning("External data unavailable on bar " + str.tostring(bar_index))
```

**Session Alignment Issues:**
```pine
// ❌ CRITICAL: Different trading hours cause na gaps
// Your chart: ES futures (nearly 24h)
// External: NYSE:TICK (RTH only 9:30-16:00)
float tickValue = request.security("NYSE:TICK", timeframe.period, close)
// Returns na outside NYSE hours!

// ✅ Explicit handling of session misalignment
float tickValue = request.security("NYSE:TICK", timeframe.period, close,
  barmerge.gaps_off, barmerge.lookahead_off)

bool isRthSession = not na(time(timeframe.period, "0930-1600:23456", "America/New_York"))
bool tickValid = not na(tickValue)

// Only use TICK filter during RTH when data is available
bool tickVeto = isRthSession and tickValid and (tickValue > 700)
```

---

### B5. var Initialization Discipline

**Check:** All `var` declarations have explicit initial values; types are explicit when ambiguous.

**BAD:**
```pine
// ❌ HIGH: Implicit na without type clarity
var rthClose  // Type ambiguous, relying on first assignment

// ❌ MEDIUM: Unclear if na is intentional
var entryBar

// ❌ HIGH: Type will be inferred from first assignment (fragile)
var stop
if condition
  stop := high  // Now it's float, but what if condition never true?
```

**GOOD:**
```pine
// ✅ Explicit type and intentional na
var float rthClose = na
var int entryBar = na

// ✅ Explicit initialization with value
var float stopPrice = 0.0
var bool isActive = false
var int tradeCount = 0

// ✅ Clear intent even when na
var float overnightHigh = na  // Will be set in overnight session
```

---

### B6. Pyramiding Logic Coherence (HIGH)

**Check:** Entry logic aligns with pyramiding settings; position checks when pyramiding=0.

**Common issues:**
- Multiple entry calls with same ID when pyramiding=0 (default) - second+ entries silently ignored
- Logic allows multiple conditions to trigger without checking position size
- Pyramiding enabled but no apparent intent to add to position
- Entry ID changes while in position causing unintended flips

**BAD:**
```pine
// ❌ HIGH: pyramiding=0 (default) but multiple entries possible
strategy("My Strategy", overlay=true)  // pyramiding=0 by default

if ta.crossover(fastMA, slowMA)
  strategy.entry("Long", strategy.long)

// Later in code...
if rsi < 30  // Both conditions can be true simultaneously!
  strategy.entry("Long", strategy.long)  // Will be IGNORED if already long
  
// ❌ HIGH: pyramiding enabled but unclear if adding to position is intended
strategy("My Strategy", pyramiding=5, overlay=true)

if bullishSignal
  strategy.entry("Long", strategy.long)  // Can fire 5 times, adding each time
// Is this intended or an oversight?

// ❌ MEDIUM: Using same ID for different entry logic
if breakoutUp
  strategy.entry("Entry", strategy.long)
if rsi < 30
  strategy.entry("Entry", strategy.long)  // Same ID but different logic
```

**GOOD:**
```pine
// ✅ pyramiding=0 with explicit position checks
strategy("My Strategy", overlay=true)

if ta.crossover(fastMA, slowMA) and strategy.position_size == 0
  strategy.entry("Long", strategy.long)

if rsi < 30 and strategy.position_size == 0
  strategy.entry("Long", strategy.long)

// ✅ pyramiding enabled with clear intent documented
// PYRAMIDING: Strategy adds to position up to 3x when signal strengthens
strategy("My Strategy", pyramiding=3, overlay=true)

int maxEntries = 3
var int entryCount = 0

if bullishSignal and entryCount < maxEntries
  strategy.entry("Long_" + str.tostring(entryCount), strategy.long)
  entryCount += 1

if strategy.position_size == 0
  entryCount := 0  // Reset counter when flat

// ✅ Different IDs for different entry logic
if breakoutUp and strategy.position_size == 0
  strategy.entry("Breakout", strategy.long)
  
if rsi < 30 and strategy.position_size == 0
  strategy.entry("Oversold", strategy.long)
```

**Guidance:**
- If pyramiding=0 (default), always add `strategy.position_size == 0` checks to entry conditions
- If pyramiding > 0, document that multiple entries are intentional and why
- Use different entry IDs for different entry logic to avoid confusion
- Track entry count explicitly if you need to limit additions to position

---

### B7. Repainting Risk Patterns (WARNING/HIGH)

**Check:** Flag patterns known to cause historical vs. real-time discrepancies.

**What is repainting?**
Repainting occurs when indicator values or strategy signals change on historical bars after they've been calculated, causing backtests to show unrealistic results that don't match live trading.

**Severity:**
- HIGH if unintentional (causes backtest vs. live mismatch)
- WARNING if intentional and documented (e.g., for alerts, education)

#### Pattern 1: calc_on_every_tick with Bar-State-Dependent Functions

**WARNING:**
```pine
// ⚠️ WARNING: Repainting risk - intra-bar recalculation
strategy("My Strategy", calc_on_every_tick=true, overlay=true)

// These functions behave differently during bar vs. on bar close:
value = ta.valuewhen(condition, close, 0)  // Changes throughout the bar
lastCross = ta.barssince(ta.crossover(ma1, ma2))  // Updates intra-bar
pivotHigh = ta.pivothigh(high, 5, 5)  // Only confirms 5 bars later

if someCondition
  strategy.entry("Long", strategy.long)
```

**GOOD:**
```pine
// ✅ Avoid repainting: calculate on bar close only
strategy("My Strategy", calc_on_every_tick=false, overlay=true)  // Explicit

// ✅ Or document intentional intra-bar execution with warnings
// EXECUTION MODEL: calc_on_every_tick=true intentional for tick-level fills
// WARNING: Backtest results may not match live trading due to intra-bar recalculation
// This is acceptable for this strategy because [reason]
strategy("My Strategy", calc_on_every_tick=true, overlay=true)

// Use barstate.isconfirmed for critical logic
if barstate.isconfirmed and someCondition
  strategy.entry("Long", strategy.long)
```

#### Pattern 2: request.security Without Explicit Lookahead

**HIGH:**
```pine
// ❌ HIGH: Repainting - may use future data on historical bars
float dailyClose = request.security(syminfo.tickerid, "D", close)
// Historical bars: Sees the completed daily bar (future data leak!)
// Real-time bars: Daily bar is still forming, value updates

// ❌ HIGH: Ambiguous gaps handling
value = request.security(symbol, "60", close)
// Missing explicit lookahead and gaps parameters

if close > dailyClose
  strategy.entry("Long", strategy.long)  // Unrealistic on historical data
```

**GOOD:**
```pine
// ✅ Explicit lookahead_off prevents future leak
float dailyClose = request.security(
  syminfo.tickerid, 
  "D", 
  close,
  barmerge.gaps_off,
  barmerge.lookahead_off  // Explicit - no future data
)

// ✅ Use previous completed bar for confirmed data
float dailyClosePrev = request.security(
  syminfo.tickerid,
  "D",
  close[1],  // Previous completed daily bar
  barmerge.gaps_off,
  barmerge.lookahead_off
)

// ✅ Document if using current bar is intentional
// NOTE: Using current forming daily bar - aware of real-time behavior difference
float dailyCloseCurrent = request.security(
  syminfo.tickerid,
  "D", 
  close,
  barmerge.gaps_off,
  barmerge.lookahead_off
)
```

#### Pattern 3: Offset References in Real-Time Signals

**MEDIUM:**
```pine
// ⚠️ MEDIUM: Timing issues with offsets
strategy("Test", calc_on_every_tick=true)

if close > high[1]  // Uses previous bar's high
  strategy.entry("Long", strategy.long)
// Historical: Previous bar is complete and known
// Real-time: If calc_on_every_tick, previous bar may still be updating
```

**GOOD:**
```pine
// ✅ Confirm bar close before using offsets
strategy("Test", overlay=true)

if barstate.isconfirmed and close > high[1]
  strategy.entry("Long", strategy.long)

// ✅ Or use calc_on_order_fills for realistic execution
strategy("Test", calc_on_order_fills=true, overlay=true)
```

#### Pattern 4: Strategy Closed Trades Properties

**WARNING:**
```pine
// ⚠️ WARNING: Closed trades info behaves differently
if strategy.closedtrades > 0
  float lastProfit = strategy.closedtrades.profit(strategy.closedtrades - 1)
  // Historical: Sees all past completed trades
  // Real-time: Only trades completed up to current moment
  
  // Using this for entry logic can cause discrepancies
  if lastProfit < 0
    // Skip next trade (works great in backtest, may differ live)
```

**GOOD:**
```pine
// ✅ Document if using closed trades for logic
// AWARE: Using closed trades history affects backtest vs. live consistency
// This is acceptable because strategy logic is path-dependent by design

// ✅ Or avoid using closed trades history for entry logic
// Use external state tracking instead
var float lastTradeProfit = na
if strategy.position_size == 0 and strategy.position_size[1] != 0
  lastTradeProfit := strategy.netprofit - strategy.netprofit[1]
```

**Detection Criteria:**
- Flag `calc_on_every_tick=true` combined with: `ta.valuewhen()`, `ta.barssince()`, `ta.pivothigh()`, `ta.pivotlow()`, `ta.change()`
- Flag `request.security()` without explicit `barmerge.lookahead_off`
- Flag strategy declaration without explicit `calc_on_every_tick` parameter (ambiguous)
- Flag use of `strategy.closedtrades` properties in entry/exit logic

**Best Practices:**
- Use `calc_on_every_tick=false` (bar close) unless you specifically need tick-level execution
- Always use explicit `barmerge.lookahead_off` in `request.security()`
- Document if repainting is intentional (e.g., for alerts, not trading decisions)
- Test strategy on real-time bars, not just historical data
- Use `barstate.isconfirmed` to wait for bar close before executing logic
- Consider `calc_on_order_fills=true` for more realistic order execution modeling

---

### B8. Memory Consistency - ta. Functions in Conditionals (CRITICAL)

**Check:** Functions starting with `ta.` are called on every bar, not wrapped inside conditional logic that might skip bars.

**The Risk:**
Pine Script's `ta.*` functions (technical analysis functions) maintain internal state across bars. If these functions are called conditionally (inside `if` statements), their state may not update correctly, leading to:
- Incorrect historical references
- State desynchronization
- Unexpected `na` values
- Logic that works on some bars but fails on others

**BAD:**
```pine
// ❌ CRITICAL: ATR only calculated when condition is true
if isRth
  float atr = ta.atr(14)  // State not maintained outside RTH!
  
// Later in code (also in RTH):
if someCondition
  // atr may be stale or na if previous bar wasn't RTH
  stopDist = 2 * atr  // Broken reference!

// ❌ CRITICAL: RSI calculation skipped on some bars
var float rsi = na
if tradingEnabled
  rsi := ta.rsi(close, 14)  // Only updates when enabled!
  
// Problem: RSI internal state corrupted when tradingEnabled is false

// ❌ CRITICAL: SMA in loop with conditional
for i = 0 to 10
  if condition[i]
    float ma = ta.sma(close, 50)  // Called conditionally in loop!
    // State inconsistent across iterations

// ❌ HIGH: Moving average only calculated during specific session
bool calculateMA = isRth and not na(time)
if calculateMA
  float fastMA = ta.ema(close, 12)  // State breaks outside session
  float slowMA = ta.ema(close, 26)

// ❌ CRITICAL: Barssince with conditional recalculation
if strategy.position_size != 0
  int barsInTrade = ta.barssince(strategy.position_size == 0)
  // Only updates while in position - state corrupted when flat!
```

**GOOD:**
```pine
// ✅ Calculate ta. functions UNCONDITIONALLY at global scope
float atr = ta.atr(14)         // Called every bar
float rsi = ta.rsi(close, 14)  // Called every bar
float fastMA = ta.ema(close, 12)
float slowMA = ta.ema(close, 26)

// THEN use the values in conditional logic
if isRth
  float stopDist = 2 * atr  // Value always fresh
  
if tradingEnabled and rsi > 70
  // RSI state is consistent

// ✅ For position-dependent calculations, use var to track
var int entryBar = na
if strategy.position_size != 0 and strategy.position_size[1] == 0
  entryBar := bar_index  // Capture entry

int barsInTrade = not na(entryBar) ? (bar_index - entryBar) : 0

// ✅ If you MUST calculate conditionally, document and accept limitations
// AWARE: Conditional ATR calculation - state will be inconsistent
// This is acceptable because we only use it immediately after calculation
if isFirstBar
  float openingRangeATR = ta.atr(14)
  // Used immediately, not stored for later
  log.info("Opening ATR: " + str.tostring(openingRangeATR))

// ✅ For conditional use, calculate globally then filter
float currentATR = ta.atr(14)  // Always calculate

if isRth
  float rthATR = currentATR  // Use the value conditionally
  stopDist = 2 * rthATR

// ✅ Pattern for session-specific calculations
// Calculate globally, store when condition is true
float rsiValue = ta.rsi(close, 14)  // Every bar
var float rthOpenRSI = na

if isFirstBar  // First bar of RTH
  rthOpenRSI := rsiValue  // Capture the value
```

**Why This Matters:**
```pine
// Example showing the problem:
strategy("Broken State", overlay=true)

// ❌ BAD: Conditional calculation
var float maValue = na
if dayofweek == dayofweek.monday
  maValue := ta.sma(close, 50)  // Only updates on Mondays!

// On Tuesday-Friday, maValue is stale (still Monday's value)
// But worse: ta.sma internal state is corrupted because it wasn't called

// ✅ GOOD: Always calculate, conditionally use
float maValue = ta.sma(close, 50)  // Every bar

if dayofweek == dayofweek.monday
  // Use the value only on Mondays
  plot(maValue, "Monday MA", color.blue)
```

**Detection Criteria:**
- `ta.*` function calls inside `if` blocks (CRITICAL)
- `ta.*` function calls inside loops with conditional logic (CRITICAL)
- `ta.*` function calls with `:=` assignment inside conditionals (CRITICAL)
- `ta.*` functions that are only called during specific sessions (HIGH)

**Exceptions (Document These):**
1. **Immediate Use**: If `ta.*` is calculated and used immediately without storage, it may be acceptable
2. **Initialization Only**: One-time calculations on first bar may be acceptable if documented
3. **Intentional Reset**: If you explicitly want state to reset (rare), document why

**Best Practice:**
```pine
// ————— Calculations (at global scope)
// Calculate ALL technical indicators here, unconditionally
float atr = ta.atr(14)
float rsi = ta.rsi(close, 14)
float macd = ta.macd(close, 12, 26, 9)
int barsSinceHigh = ta.barssince(high == ta.highest(high, 100))

// ————— Strategy Calls (conditional logic)
// Now use the pre-calculated values in conditional logic
if isRth and atr > minATR
  if rsi < 30
    strategy.entry("Long", strategy.long)
```

**Related Checks:**
- See section 2.8 in PINE_SCRIPT_STANDARDS.md for proper script organization
- Calculations section should contain all `ta.*` calls at global scope
- Strategy calls section contains conditional logic using those values

---

## C) Directionality & Polarity Sanity (CRITICAL/HIGH)

This is the main "upside-down logic" detector.

### C1. Stop-Loss Direction Matches Position (CRITICAL)

**Check:** Long stops are below entry; short stops are above entry.

**BAD:**
```pine
// ❌ CRITICAL: Stop for long position is ABOVE entry
if strategy.position_size > 0  // Long position
  float stopPrice = strategy.position_avg_price + 10
  strategy.exit("Stop", stop=stopPrice)  // Will exit immediately!

// ❌ CRITICAL: Using same stop logic for both directions
stopPrice = high + 5  // Always above current price
strategy.exit("Exit", stop=stopPrice)  // Wrong for longs!
```

**GOOD:**
```pine
// ✅ Stop direction matches position
if strategy.position_size > 0  // Long position
  float stopPrice = overnightLow  // Below entry (loss side)
  strategy.exit("Stop Long", stop=stopPrice)

if strategy.position_size < 0  // Short position
  float stopPrice = overnightHigh  // Above entry (loss side)
  strategy.exit("Stop Short", stop=stopPrice)

// ✅ Conditional stop based on position direction
float stopPrice = strategy.position_size > 0 ? 
  overnightLow :   // Long: stop below
  overnightHigh    // Short: stop above
strategy.exit("Exit", stop=stopPrice)
```

---

### C2. Take-Profit Direction Matches Position (CRITICAL)

**Check:** Long TP above entry; short TP below entry.

**BAD:**
```pine
// ❌ CRITICAL: Take-profit for long is BELOW entry
if strategy.position_size > 0  // Long position
  float tpPrice = strategy.position_avg_price - 50
  strategy.exit("TP", limit=tpPrice)  // Wrong direction!

// ❌ CRITICAL: Mean reversion target on wrong side
if strategy.position_size > 0
  float target = low - 10  // Below current price for long!
  strategy.exit("Exit", limit=target)
```

**GOOD:**
```pine
// ✅ Target direction matches position
if strategy.position_size > 0  // Long position
  float tpPrice = rthClose  // Above entry (profit side)
  strategy.exit("TP Long", limit=tpPrice)

if strategy.position_size < 0  // Short position
  float tpPrice = rthClose  // Below entry (profit side)
  strategy.exit("TP Short", limit=tpPrice)

// ✅ Conditional target based on position
float targetPrice = strategy.position_size > 0 ?
  (strategy.position_avg_price + 20) :  // Long: target above
  (strategy.position_avg_price - 20)     // Short: target below
strategy.exit("Exit", limit=targetPrice)
```

---

### C3. No Silent Sign Flips (CRITICAL)

**Check:** Values used as stop/target don't become `na` or swap meaning without explicit fallback.

**BAD:**
```pine
// ❌ CRITICAL: rthClose can be na in first session
strategy.exit("Exit", limit=rthClose)  // May be na!

// ❌ CRITICAL: overnightHigh resets, stop becomes invalid
if not isRth
  overnightHigh := na  // Resetting during position!
  
// In position code:
strategy.exit("Stop", stop=overnightHigh)  // Now na!
```

**GOOD:**
```pine
// ✅ Guard na with fallback
float targetPrice = na(rthClose) ? close : rthClose
strategy.exit("Exit", limit=targetPrice)

// ✅ Don't reset state variables while in position
if not isRth and strategy.position_size == 0
  overnightHigh := na  // Only reset when flat

// ✅ Capture reference at entry
var float entryStopRef = na
if strategy.position_size != 0 and strategy.position_size[1] == 0
  entryStopRef := overnightHigh  // Locked in at entry

strategy.exit("Stop", stop=entryStopRef)
```

---

### C5. Price Reference Validity (CRITICAL/HIGH)

**Check:** Stops/targets reference the correct entry context; no stale references from prior session/position.

**BAD:**
```pine
// ❌ CRITICAL: Using current bar's calculation for historical position
if strategy.position_size > 0
  float atr = ta.atr(14)  // Current ATR, not entry ATR
  float stop = close - (2 * atr)  // Wrong reference!
  strategy.exit("Stop", stop=stop)

// ❌ HIGH: Reference from wrong session
var float entryPrice = na
if longCondition
  strategy.entry("Long", strategy.long)
  entryPrice := open  // But entry may fill at different price!
```

**GOOD:**
```pine
// ✅ Capture reference price on fill
var float entryRefPrice = na
var float entryAtr = na

if strategy.position_size != 0 and strategy.position_size[1] == 0
  // Position just opened
  entryRefPrice := strategy.position_avg_price
  entryAtr := ta.atr(14)  // Capture ATR at entry

// Use captured references for exits
if strategy.position_size > 0
  float stopPrice = entryRefPrice - (2 * entryAtr)
  strategy.exit("Stop", stop=stopPrice)

// ✅ Alternative: Use built-in position_avg_price
if strategy.position_size > 0
  float stopPrice = strategy.position_avg_price - 10
  strategy.exit("Stop", stop=stopPrice)
```

---

### C4. Naming Coherence (HIGH)

**Check:** Entry IDs and variable names align with direction unless documented as contrarian.

**BAD:**
```pine
// ❌ HIGH: ID says "Long" but using short direction
strategy.entry("Long", strategy.short)  // Confusing!

// ❌ HIGH: Variable name contradicts logic
bool longSignal = close < ma  // Name implies long, logic is bearish

// ❌ MEDIUM: Misleading naming
const string BUY_SIGNAL = "FadeShort"  // Confusing terminology
```

**GOOD:**
```pine
// ✅ ID matches direction
if bullish
  strategy.entry("Long", strategy.long)
if bearish
  strategy.entry("Short", strategy.short)

// ✅ Variable name matches logic
bool longSignal = close > ma  // Clear
bool shortSignal = close < ma

// ✅ For contrarian strategies, document explicitly
// CONTRARIAN FADE: Buying weakness, selling strength
bool fadeShortSignal = close > overnightHigh  // Documented
strategy.entry("FadeShort", strategy.short)
```

---

## D) Session, Reset, and State Integrity (CRITICAL)

Catches wrong-day / stale-state errors.

### D1. Every var Has a Reset Event (CRITICAL)

**Check:** All persistent variables have explicit reset logic.

**BAD:**
```pine
// ❌ CRITICAL: No reset logic - accumulates forever
var int tradesTotal = 0
if entryCondition
  tradesTotal += 1

// ❌ CRITICAL: Opening range never resets
var float orHigh = na
var float orLow = na
// No reset on new session!
```

**GOOD:**
```pine
// ✅ Reset at session boundary
var int tradesToday = 0

if isFirstBar  // New RTH session
  tradesToday := 0

// ✅ Reset when flat
var int entryBar = na
if strategy.position_size == 0
  entryBar := na

// ✅ Opening range with reset
var float orHigh = na
var float orLow = na

if isFirstBar
  orHigh := high
  orLow := low
```

---

### D2. Day/Session Boundary Matches Intent (CRITICAL)

**Check:** "Day" definition matches strategy intent (RTH close vs midnight).

**BAD:**
```pine
// ❌ CRITICAL: Using midnight for RTH-only strategy
bool isNewDay = ta.change(dayofmonth) != 0
if isNewDay
  tradesT oday := 0  // Wrong boundary for RTH strategy!

// ❌ HIGH: Overnight range captured at wrong boundary
if dayofmonth != dayofmonth[1]
  rthClose := close  // But RTH may not have closed yet!
```

**GOOD:**
```pine
// ✅ RTH session definition
const string RTH_SESSION = "0930-1600:1234567"
const string TIMEZONE = "America/New_York"
bool isRth = not na(time(timeframe.period, RTH_SESSION, TIMEZONE))
bool isFirstBar = isRth and not isRth[1]

// ✅ Reset at RTH session boundary
if isFirstBar
  tradesToday := 0

// ✅ Capture RTH close when exiting RTH
if not isRth and isRth[1]
  rthClose := close[1]  // Last RTH bar's close
```

---

### D3. Session Gating Centralized (HIGH)

**Check:** A single `canTrade` gate (or equivalent) controls entry conditions.

**BAD:**
```pine
// ❌ HIGH: Scattered session checks (easy to miss one)
if gapUp and failedHigh and isRth and inDateRange
  strategy.entry("Short", strategy.short)

if gapDown and failedLow and inDateRange  // Forgot isRth!
  strategy.entry("Long", strategy.long)
```

**GOOD:**
```pine
// ✅ Centralized gate
bool canTrade = isRth and inDateRange and orFrozen and 
  tradesToday < maxTrades

// All entries check same gate
if canTrade and shortCondition
  strategy.entry("Short", strategy.short)

if canTrade and longCondition
  strategy.entry("Long", strategy.long)
```

---

### D4. Entry Tracking State Resets (CRITICAL)

**Check:** Entry bar, trade counters, active flags reset when flat / new session.

**BAD:**
```pine
// ❌ CRITICAL: entryBar never resets when flat
var int entryBar = na
if strategy.position_size != 0 and strategy.position_size[1] == 0
  entryBar := bar_index

// Later: using stale entryBar from previous trade!
if bar_index - entryBar > maxHold
  strategy.close_all()

// ❌ CRITICAL: Trade counter never resets
var int tradesToday = 0
if filled
  tradesToday += 1
// Next day, counter still high!
```

**GOOD:**
```pine
// ✅ Reset when flat
var int entryBar = na

if strategy.position_size != 0 and strategy.position_size[1] == 0
  entryBar := bar_index

if strategy.position_size == 0
  entryBar := na  // Clear when flat

// ✅ Reset counter at session boundary
var int tradesToday = 0

if isFirstBar
  tradesToday := 0

if strategy.position_size != 0 and strategy.position_size[1] == 0
  tradesToday += 1
```

---

## E) External Data Integrity (CRITICAL/HIGH)

Catches silent degradations from external data sources.

### E1. Missing External Data Behavior is Explicit (CRITICAL)

**Check:** Decide per dependency: fail-closed (veto trades) or fail-open (ignore veto).

**BAD:**
```pine
// ❌ CRITICAL: What happens if TICK data unavailable?
tickValue = request.security("NYSE:TICK", timeframe.period, close)
tickVeto = tickValue > 700  // If na, this becomes false silently!

if longCondition and not tickVeto
  strategy.entry("Long", strategy.long)  // May trade when shouldn't!
```

**GOOD:**
```pine
// ✅ Explicit na handling - fail-closed (conservative)
float tickValue = request.security("NYSE:TICK", timeframe.period, close,
  barmerge.gaps_off, barmerge.lookahead_off)

bool tickAvailable = not na(tickValue)
bool tickVeto = tickAvailable ? (tickValue > 700) : true  // Veto if missing

if longCondition and not tickVeto
  strategy.entry("Long", strategy.long)

// ✅ Alternative: fail-open (trade anyway if data missing)
bool tickVeto = tickAvailable and tickValue > 700

// ✅ Document decision
// TICK DATA: Fail-closed - if TICK unavailable, veto all trades (conservative)
```

---

### E2. Session Alignment/Gaps Handled (CRITICAL)

**Check:** External series hours differ → handle gaps or guard for `na`.

**BAD:**
```pine
// ❌ CRITICAL: Daily data may have gaps on weekends/holidays
dailyClose = request.security(syminfo.tickerid, "D", close)
if close > dailyClose  // What if dailyClose is na?
  strategy.entry("Long", strategy.long)
```

**GOOD:**
```pine
// ✅ Explicit gaps handling and na guard
float dailyClose = request.security(
  syminfo.tickerid, 
  "D", 
  close,
  barmerge.gaps_off,  // Fill gaps with previous value
  barmerge.lookahead_off
)

if not na(dailyClose) and close > dailyClose
  strategy.entry("Long", strategy.long)

// ✅ Alternative: Track data freshness
var float lastValidDaily = na
float currentDaily = request.security(syminfo.tickerid, "D", close)

if not na(currentDaily)
  lastValidDaily := currentDaily

// Use last valid value
if not na(lastValidDaily) and close > lastValidDaily
  strategy.entry("Long", strategy.long)
```

---

### E3. External Dependencies Enumerated (HIGH)

**Check:** Header or metadata lists all external symbols used.

**GOOD:**
```pine
// ============================================================================
// EXTERNAL DATA REQUIREMENTS
// ============================================================================
// 1. NYSE:TICK - NYSE Tick Index (required for breadth filter)
//    Behavior if unavailable: Veto all trades (fail-closed)
//
// 2. SPY - S&P 500 ETF (optional for correlation check)
//    Behavior if unavailable: Ignore correlation filter (fail-open)
// ============================================================================
```

---

### E4. Symbol Availability & Requirement Level (HIGH)

**Check:** Each external symbol declared as required or optional; behavior if missing is explicit.

**BAD:**
```pine
// ❌ HIGH: Unclear if VIX is required
vixValue = request.security("VIX", timeframe.period, close)
// What if user doesn't have VIX data?
```

**GOOD:**
```pine
// ✅ Document requirement level and behavior
// NYSE:TICK - REQUIRED
// Strategy cannot function without breadth filter
// Fail-closed: No TICK data = no trades
float tickValue = request.security("NYSE:TICK", timeframe.period, close)
bool tickValid = not na(tickValue)

if not tickValid
  // Log or alert that strategy is disabled
  runtime.error("NYSE:TICK data required but unavailable")

// ✅ Optional dependency
// VIX - OPTIONAL  
// Used for volatility regime filter; if unavailable, assume normal vol
float vixValue = request.security("VIX", timeframe.period, close)
bool highVol = not na(vixValue) ? vixValue > 20 : false  // Default to false
```

---

## F) Reachability & Contradictions (HIGH/MEDIUM)

Catches dead code and impossible branches.

### F1. Mutually Exclusive Entries Controlled (HIGH)

**Check:** Long and short entries can't both fire on same bar unless explicitly intended.

**BAD:**
```pine
// ❌ HIGH: Both could be true simultaneously
if close > ma
  strategy.entry("Long", strategy.long)

if close < ma
  strategy.entry("Short", strategy.short)

// What if close == ma? Neither? That's OK.
// But if conditions overlap, which executes?

// ❌ HIGH: Overlapping conditions
if rsi < 40
  strategy.entry("Long", strategy.long)
if rsi < 50  // Overlaps with above!
  strategy.entry("Short", strategy.short)
```

**GOOD:**
```pine
// ✅ Mutually exclusive conditions
if close > ma
  strategy.entry("Long", strategy.long)
else if close < ma
  strategy.entry("Short", strategy.short)

// ✅ Or use elif pattern for complex conditions
bool longCond = gapUp and failedHigh and not tickVetoUp
bool shortCond = gapDown and failedLow and not tickVetoDown

if longCond
  strategy.entry("Long", strategy.long)
else if shortCond
  strategy.entry("Short", strategy.short)
```

---

### F2. No "Always True / Never True" Entry Logic (HIGH)

**Check:** Obvious tautologies or contradictions are flagged.

**BAD:**
```pine
// ❌ HIGH: Always true (meaningless gate)
if high >= low  // Always true!
  strategy.entry("Long", strategy.long)

// ❌ HIGH: Never true (dead code)
if close > high  // Impossible on standard bars
  strategy.entry("Long", strategy.long)

// ❌ HIGH: Contradictory
if close > ma and close < ma  // Can never both be true
  strategy.entry("Long", strategy.long)
```

**GOOD:**
```pine
// ✅ Meaningful condition
if close > ta.sma(close, 50)
  strategy.entry("Long", strategy.long)

// ✅ Valid range check
if rsi >= 30 and rsi <= 70  // Middle range
  strategy.entry("Long", strategy.long)
```

---

### F3. Duplicate Conditions with Different Actions (MEDIUM)

**Check:** Same predicate triggers two different actions without order control.

**BAD:**
```pine
// ❌ MEDIUM: Same condition, different actions
if close > ma
  strategy.entry("Long", strategy.long)

// ... 50 lines later ...

if close > ma  // Same condition!
  strategy.entry("Short", strategy.short)
// Which one executes? Both? Order-dependent?
```

**GOOD:**
```pine
// ✅ Distinct conditions
if close > maFast and maFast > maSlow
  strategy.entry("Long", strategy.long)

if close < maFast and maFast < maSlow
  strategy.entry("Short", strategy.short)

// ✅ Or intentional sequence
bool entryCondition = close > ma
if entryCondition and not inPosition
  strategy.entry("Long", strategy.long)
if entryCondition and inPosition
  // Different action for same condition is intentional
  addToPosition()
```

---

### F4. Exit Logic Reachability (HIGH)

**Check:** Exits can actually occur given max-hold, stop/target definitions, and session close logic.

**BAD:**
```pine
// ❌ HIGH: Time exit can't occur if target/stop always reached first
maxHoldBars = 5
// But target is 1 point away (always hits quickly)
targetPrice = strategy.position_avg_price + 1
strategy.exit("Exit", limit=targetPrice)

// Time exit is unreachable:
if bar_index - entryBar >= maxHoldBars
  strategy.close_all()  // Never executes

// ❌ HIGH: EOD exit can't occur if position closed before
if not isRth
  strategy.close_all("EOD")
// But earlier code:
if strategy.position_size != 0
  strategy.close_all("Force")  // Always closes before EOD
```

**GOOD:**
```pine
// ✅ Exit hierarchy is logical
strategy.exit("TP/SL", limit=targetPrice, stop=stopPrice)

// Time-based exit as fallback
if not na(entryBar) and (bar_index - entryBar) >= maxHoldBars
  strategy.close_all("Timeout")  // Can reach if TP/SL not hit

// EOD exit as final safety
if not isRth
  strategy.close_all("EOD")  // Catches any remaining positions
```

---

## G) Suspicious Pattern Warnings (WARNING)

Not errors — review prompts.

### G1. Unrealistic Friction Flagged

**Pattern:** Commission > ~10% of typical trade value (context dependent).

**WARNING:**
```pine
// ⚠️ WARNING: 150% commission seems unrealistic
commission_value = 150.0

// For ES ($50/point), this would be $150 per contract per side
// On a $250,000 contract value = 0.06% (OK)
// But on a $5/point instrument = 3000% (ERROR!)
```

**Guidance:** Commission should be proportional to contract/share value. Flag for manual review if suspicious.

---

### G2. Stop/Target Distance Suspicious

**Pattern:** Stop distance > X × ATR or >50% price move (asset-dependent).

**WARNING:**
```pine
// ⚠️ WARNING: Stop distance is 50 ES points (>10 ATR typical)
float stopDistance = 50.0

// Recommend ATR normalization for warnings
float atrValue = ta.atr(14)
float stopDistance = 2.0 * atrValue  // Normalized approach
if stopDistance > 4.0 * atrValue
  // WARNING: Stop extremely wide
```

**Guidance:** Start generic; add asset profiles later if needed.

---

### G3. Entry Frequency Suspicious

**Pattern:** "Almost always true" or "almost never true" (can be detected via backtest counts or basic static signals).

**WARNING:**
```pine
// ⚠️ WARNING: Condition is almost always true
if high >= low  // Always true on standard bars!
  strategy.entry("Long", strategy.long)

// ⚠️ WARNING: Condition likely never true (needs backtest verification)
if ta.crossover(close, close)  // Never crosses itself
  strategy.entry("Long", strategy.long)
```

**Guidance:** Flag mathematically obvious issues; recommend backtest review for others.

---

### G4. Bar Magnifier Logic (Within-Bar Execution Assumption)

**Pattern:** strategy.exit behavior within single bars when both stop and target can be hit.

**The Risk:**
Pine Script's strategy engine assumes the "best case scenario" within a single bar unless using the Bar Magnifier feature (premium). If a bar's range includes both your stop loss AND take profit, the backtest defaults to the **profitable outcome**.

**Real-world impact:**
- Backtest shows: Take profit hit first → Win
- Live trading: Stop hit first → Loss

This creates an **optimistic backtest bias**, especially on higher timeframes or volatile instruments.

**WARNING:**
```pine
// ⚠️ WARNING: Bar Magnifier assumption risk
strategy("My Strategy", overlay=true)

if longCondition
  strategy.entry("Long", strategy.long)

// Tight stops and targets on 5-minute bars
if strategy.position_size > 0
  stopPrice = strategy.position_avg_price - 2.0   // 2 point stop
  limitPrice = strategy.position_avg_price + 2.0  // 2 point target
  strategy.exit("Exit", stop=stopPrice, limit=limitPrice)

// On a volatile 5-min bar with 6-point range:
// - Backtest assumes: Target hit first (win)
// - Reality: Could hit stop first (loss)
```

**Detection Criteria:**
- Small stop/target distances relative to bar volatility (e.g., both within 1× ATR)
- Higher timeframes (5-min+) with tight exits
- Instruments with high intra-bar volatility

**GOOD (Mitigation Strategies):**
```pine
// ✅ Strategy 1: Test on lower timeframe
// Instead of 5-minute bars, backtest on 1-minute bars
// More granular execution reduces within-bar ambiguity

// ✅ Strategy 2: Conservative stop placement
// Ensure stop is significantly wider than typical bar range
float atr = ta.atr(14)
stopDist = 2.5 * atr  // Well outside typical bar range
limitDist = 1.5 * atr

// ✅ Strategy 3: Use "Worst Case" stop logic
// Place stop outside bar high/low to avoid within-bar ambiguity
if strategy.position_size > 0
  // Stop outside the bar range (more conservative)
  stopPrice = math.min(low, strategy.position_avg_price - stopDist)
  strategy.exit("Stop", stop=stopPrice)

// ✅ Strategy 4: Document assumption
// EXECUTION MODEL: This strategy assumes Bar Magnifier favorable execution.
// Live results may differ if stops hit before targets within same bar.
// Backtest on 1-minute bars validated; 5-minute used for speed.

// ✅ Strategy 5: Secondary validation
// Run parallel backtest on lower timeframe to validate results
// Document: "Strategy validated on 1m bars; 5m backtest for overview"
```

**Recommended Validation:**
1. Backtest strategy on current timeframe (e.g., 5-minute)
2. Re-run same strategy on lower timeframe (e.g., 1-minute)
3. Compare win rates and profit factors
4. If significant divergence (>10% win rate difference), document and use lower timeframe results

**When This Check is CRITICAL vs. WARNING:**
- **CRITICAL**: Small exits (<1× ATR) on timeframes ≥5 minutes
- **HIGH**: Moderate exits (1-2× ATR) on timeframes ≥15 minutes  
- **WARNING**: Wide exits (>3× ATR) or lower timeframes (<5 minutes)

**Guidance:** 
This is not a bug, but a **backtest assumption**. Always validate tight-exit strategies on lower timeframes or document the within-bar execution assumption explicitly.

---

## H) Observability (WARNING, Dev-Recommended)

Helps catch upside-down logic quickly in visual review.

### H1. Plot/Label Key State

**Practice:** Visualize session flag, OR levels, prior close, veto state, gap validity.

**GOOD:**
```pine
// Debug visualization (behind toggle)
bool debugModeInput = input.bool(false, "Debug Mode")

if debugModeInput
  // Plot key levels
  plot(rthClose, "Prior RTH Close", color=color.orange, linewidth=2)
  plot(orHigh, "OR High", color=color.green, style=plot.style_stepline)
  plot(orLow, "OR Low", color=color.red, style=plot.style_stepline)
  
  // Show state
  bgcolor(not isRth ? color.new(color.gray, 80) : na, title="Non-RTH")
  bgcolor(tickVeto ? color.new(color.red, 90) : na, title="TICK Veto Active")
```

---

### H2. Explain Veto Reasons

**Practice:** Even minimal: boolean plot or label when veto active.

**GOOD:**
```pine
if debugModeInput and tickVeto
  label.new(bar_index, high, "TICK VETO", 
    style=label.style_label_down, 
    color=color.red, 
    textcolor=color.white,
    size=size.small)
```

---

### H3. Debug Behind a Toggle

**Practice:** All observability plots/labels behind `input.bool(debugMode)`.

**GOOD:**
```pine
// ✅ Debug mode toggle
bool debugModeInput = input.bool(false, "Debug Mode", 
  tooltip="Enable visual debugging - plots key states and levels")

// All debug visuals check the flag
if debugModeInput
  // plots, labels, tables, etc.
  
// Disable for production without editing code
```

---

### H4. Pre-Flight Status Block (Metadata Logging)

**Practice:** Include a metadata block or status output that explicitly reports the state of critical checks, filters, and configuration.

**Purpose:**
When debugging screenshots, backtest reports, or live trading issues, having a "Pre-Flight" status display makes it immediately clear:
- Which filters are active
- What parameter values are being used
- Whether external data is valid
- Session state and boundaries

**Benefits:**
- **Debugging**: Screenshots instantly show configuration state
- **Validation**: Quickly verify strategy is running with correct parameters
- **Documentation**: Backtest screenshots self-document the configuration
- **Troubleshooting**: Identify why trades didn't fire (which veto was active)

**GOOD Examples:**

**Option 1: Table Display (Most Comprehensive)**
```pine
// ✅ Pre-flight status table
bool showStatusInput = input.bool(true, "Show Status Table", 
  tooltip="Display strategy configuration and current state")

if showStatusInput and barstate.islast
  var table statusTable = table.new(position.top_right, 2, 10, 
    bgcolor=color.new(color.gray, 85), frame_width=1, frame_color=color.gray)
  
  // Header
  table.cell(statusTable, 0, 0, "Parameter", bgcolor=color.gray, text_color=color.white)
  table.cell(statusTable, 1, 0, "Value", bgcolor=color.gray, text_color=color.white)
  
  // Configuration
  table.cell(statusTable, 0, 1, "ATR Filter")
  table.cell(statusTable, 1, 1, minAtrInput > 0 ? 
    "Active (" + str.tostring(minAtrInput, "#.##") + ")" : "Disabled")
  
  table.cell(statusTable, 0, 2, "Slippage")
  table.cell(statusTable, 1, 2, str.tostring(slippageInput, "#.##") + " pts")
  
  table.cell(statusTable, 0, 3, "Commission")
  table.cell(statusTable, 1, 3, "$" + str.tostring(commissionInput, "#.##"))
  
  // Current State
  table.cell(statusTable, 0, 4, "TICK Data")
  table.cell(statusTable, 1, 4, tickValid ? 
    str.tostring(tickValue, "#") : "UNAVAILABLE", 
    bgcolor=tickValid ? color.new(color.green, 80) : color.new(color.red, 80))
  
  table.cell(statusTable, 0, 5, "Session")
  table.cell(statusTable, 1, 5, isRth ? "RTH" : "Non-RTH",
    bgcolor=isRth ? color.new(color.blue, 80) : color.new(color.gray, 80))
  
  table.cell(statusTable, 0, 6, "Trades Today")
  table.cell(statusTable, 1, 6, str.tostring(tradesToday) + " / " + str.tostring(maxTradesInput))
  
  table.cell(statusTable, 0, 7, "Can Trade")
  table.cell(statusTable, 1, 7, canTrade ? "YES" : "NO",
    bgcolor=canTrade ? color.new(color.green, 80) : color.new(color.red, 80))
```

**Option 2: Pine Logs (Lightweight)**
```pine
// ✅ Pre-flight checks logged at session start
if isFirstBar
  log.info("═══ STRATEGY PRE-FLIGHT ═══")
  log.info("ATR Filter: " + (minAtrInput > 0 ? 
    "Active (min " + str.tostring(minAtrInput) + ")" : "Disabled"))
  log.info("TICK Veto: " + (useTickFilter ? 
    "Active (threshold " + str.tostring(tickThreshold) + ")" : "Disabled"))
  log.info("Max Trades/Day: " + str.tostring(maxTradesInput))
  log.info("Commission: $" + str.tostring(commissionInput) + " per side")
  log.info("Slippage: " + str.tostring(slippageInput) + " pts")
  log.info("═══════════════════════════")
```

**Option 3: Chart Label (Minimal)**
```pine
// ✅ Minimal status label on first bar
bool showStatusInput = input.bool(true, "Show Config Label")

if showStatusInput and bar_index == 0
  string statusText = "Config: " +
    "ATR>" + str.tostring(minAtrInput) + " | " +
    "MaxTrades=" + str.tostring(maxTradesInput) + " | " +
    "TICK " + (useTickFilter ? "ON" : "OFF")
  
  label.new(bar_index, high, statusText,
    style=label.style_label_down,
    color=color.new(color.blue, 70),
    textcolor=color.white,
    size=size.normal)
```

**Option 4: Comprehensive On-Chart Display**
```pine
// ✅ Full status with veto reasons
bool showStatusInput = input.bool(true, "Show Strategy Status")

if showStatusInput and barstate.islast
  var table statusTable = table.new(position.bottom_right, 2, 12)
  
  // Strategy Info
  table.cell(statusTable, 0, 0, "Strategy Status", 
    colspan=2, bgcolor=color.new(color.navy, 70), text_color=color.white)
  
  // Active Filters
  row = 1
  table.cell(statusTable, 0, row, "ATR Filter:", text_halign=text.align_left)
  table.cell(statusTable, 1, row, atr >= minAtrInput ? "✓ PASS" : "✗ VETO",
    text_color=atr >= minAtrInput ? color.green : color.red)
  
  row += 1
  table.cell(statusTable, 0, row, "TICK Filter:")
  table.cell(statusTable, 1, row, not tickVeto ? "✓ PASS" : "✗ VETO",
    text_color=not tickVeto ? color.green : color.red)
  
  row += 1  
  table.cell(statusTable, 0, row, "Trade Limit:")
  table.cell(statusTable, 1, row, 
    str.tostring(tradesToday) + "/" + str.tostring(maxTradesInput),
    text_color=tradesToday < maxTradesInput ? color.green : color.red)
  
  row += 1
  table.cell(statusTable, 0, row, "Session:")
  table.cell(statusTable, 1, row, isRth ? "RTH ✓" : "Non-RTH",
    text_color=isRth ? color.green : color.gray)
  
  // Overall Status
  row += 1
  table.cell(statusTable, 0, row, "CAN TRADE:", 
    colspan=2, bgcolor=canTrade ? color.new(color.green, 80) : color.new(color.red, 80),
    text_color=color.white, text_size=size.large)
```

**When to Use Each:**
- **Table Display**: Development, debugging, education, monitoring
- **Pine Logs**: Lightweight verification, parameter confirmation
- **Chart Label**: Minimal overhead, permanent config marker
- **Comprehensive Display**: Complex strategies, multiple filters, live monitoring

**Standard 8.4 Recommendation:**
Every strategy SHOULD include at least one of these pre-flight displays, togglable via `input.bool()`, to facilitate:
- Visual verification in screenshots
- Debugging configuration issues
- Confirming filter states during analysis
- Documentation of backtest parameters

**Detection:**
- **RECOMMENDED**: Strategy includes status table, log output, or label showing configuration
- **OPTIONAL**: Can be disabled for production, but encouraged during development

---

## Quick Reference Checklist

Use this condensed checklist for daily code reviews. See sections above for details.

### ✅ CRITICAL (Must Pass)

**A) Math & Data:**
- [ ] A1: No close > high, close < low, or high < low (unless documented synthetic bars)
- [ ] A2: All division guarded (no divide by 0 or na)
- [ ] A3: All periods/lengths >= 1 and bounded
- [ ] A4: Percents 0-100% (unless documented exception)
- [ ] A5: Time conversions use named constants (MILLISECONDS_PER_MINUTE)

**B) Pine API:**
- [ ] B1: strategy.entry uses only strategy.long/short
- [ ] B2: strategy.exit stop/limit not swapped; no na prices
- [ ] B3: Functions receive correct types (ta.barssince(bool), etc.)
- [ ] B4: request.security has explicit lookahead, gaps, AND data persistence handling
- [ ] B5: All var have explicit type and initial value
- [ ] B6: Pyramiding logic matches settings (position checks if pyramiding=0)
- [ ] B7: Repainting patterns flagged (calc_on_every_tick, lookahead)
- [ ] B8: All ta.* functions called unconditionally (not wrapped in if/loops)

**C) Directionality:**
- [ ] C1: Long stops below entry, short stops above entry
- [ ] C2: Long TP above entry, short TP below entry
- [ ] C3: Stop/target values don't become na during position
- [ ] C5: Price references captured at entry, not using stale values

**D) Session & State:**
- [ ] D1: Every var has reset logic (session boundary or flat state)
- [ ] D2: Session boundaries match intent (RTH vs midnight)
- [ ] D3: Centralized canTrade gate
- [ ] D4: Entry tracking (entryBar, counters) resets when flat

**E) External Data:**
- [ ] E1: Missing data behavior explicit (fail-open vs fail-closed)
- [ ] E2: request.security handles na and session gaps

### ⚠️ HIGH (Should Pass)

**C) Directionality:**
- [ ] C4: Entry IDs match direction ("Long" uses strategy.long)

**E) External Data:**
- [ ] E3: External symbols enumerated in header
- [ ] E4: Symbol requirements documented (required vs optional)

**F) Reachability:**
- [ ] F1: Long/short entries mutually exclusive (or explicit sequencing)
- [ ] F2: No always-true / never-true conditions
- [ ] F4: Exit logic reachable given time limits and session closes

### 🔍 WARNINGS (Review)

**G) Suspicious Patterns:**
- [ ] G1: Commission reasonable for asset
- [ ] G2: Stop distance reasonable (prefer ATR-normalized checks)
- [ ] G3: Entry conditions not always/never true
- [ ] G4: Bar Magnifier assumption documented (tight stops/targets on higher TF)

**H) Observability:**
- [ ] H1: Key states visualized during development
- [ ] H2: Veto reasons visible
- [ ] H3: Debug visuals behind input toggle
- [ ] H4: Pre-flight status block showing config/filter states (recommended)

---

## Validation Workflow

### When to Run These Checks:

**Always:**
- Before committing code
- After significant logic changes
- When debugging unexpected behavior

**Recommended:**
- During code review with peers
- When porting strategy to new symbol/timeframe
- After adding new features/filters

### How to Apply:

1. **Pass 1:** Run through CRITICAL checks (A, B, C, D, E)
   - Any failures → Fix before proceeding

2. **Pass 2:** Run through HIGH checks (C4, E3-E4, F1-F2-F4)
   - Review findings, fix or document as intentional

3. **Pass 3:** Review WARNINGS (G1-G3)
   - Note for awareness, verify intentional

4. **Pass 4:** Dev best practices (H1-H3)
   - Implement observability during development

---

## Document History

- **v1.0** - Initial release
- **v1.1** - Added Q&A section responses
- **v1.2** - Added A5 (time arithmetic), B5 (var init), C5 (price refs), E4 (symbol availability), H3 (debug toggle)
- **v1.3** - Added B4 expansion (data persistence), B8 (ta.* function scoping), G4 (Bar Magnifier), H4 (pre-flight status)

---

## Related Documentation

- `/docs/PINE_SCRIPT_STANDARDS.md` - Pine Script v5 coding standards
- `/docs/JSON_SCHEMA_GUIDE.md` - Metadata schema
- `/.cursorrules` - Complete code review checklist (Categories 1-9)

---

**Remember:** These checks validate that your code does what you intend. They do NOT evaluate whether your trading strategy is profitable or sound — that's your domain expertise.
