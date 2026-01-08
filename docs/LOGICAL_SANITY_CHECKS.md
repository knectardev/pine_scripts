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

### B4. request.security() Explicitness

**Check:** `lookahead` parameter is explicit; `gaps` behavior is intentional.

**BAD:**
```pine
// ❌ HIGH: Lookahead not explicit (may cause repainting)
tickValue = request.security("NYSE:TICK", timeframe.period, close)

// ❌ HIGH: Gaps behavior not handled
extValue = request.security("SYMBOL", "D", close)
// What happens if daily bar hasn't closed yet?
```

**GOOD:**
```pine
// ✅ Explicit lookahead and gaps handling
float tickValue = request.security(
  "NYSE:TICK", 
  timeframe.period, 
  close,
  barmerge.gaps_off,
  barmerge.lookahead_off
)

// ✅ Handle na from external data
bool tickValid = not na(tickValue)
bool useTickFilter = tickValid and tickValue > 700
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
- [ ] B4: request.security has explicit lookahead and gaps handling
- [ ] B5: All var have explicit type and initial value

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

**H) Observability:**
- [ ] H1: Key states visualized during development
- [ ] H2: Veto reasons visible
- [ ] H3: Debug visuals behind input toggle

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

---

## Related Documentation

- `/docs/PINE_SCRIPT_STANDARDS.md` - Pine Script v5 coding standards
- `/docs/JSON_SCHEMA_GUIDE.md` - Metadata schema
- `/.cursorrules` - Complete code review checklist (Categories 1-9)

---

**Remember:** These checks validate that your code does what you intend. They do NOT evaluate whether your trading strategy is profitable or sound — that's your domain expertise.
