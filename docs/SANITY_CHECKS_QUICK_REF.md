# Logical Sanity Checks - Quick Reference Card

**Purpose:** First-order logic validation — catches BUGS, not strategy quality.

**Full Documentation:** `/docs/LOGICAL_SANITY_CHECKS.md`

---

## Before Committing Pine Script Code:

### ✅ CRITICAL (Must Pass) — Fix Before Proceeding

#### A) Mathematical & Data Invariants
- [ ] **A1:** No `close > high`, `close < low`, `high < low` (unless synthetic bars documented)
- [ ] **A2:** No division by zero or `na` without guards (ATR, volume, prior close, range)
- [ ] **A3:** All periods/lengths >= 1 and bounded (no negative, zero, or unbounded lookbacks)
- [ ] **A4:** Percentages bounded 0-100% (unless documented exception)
- [ ] **A5:** Time conversions use named constants (`MILLISECONDS_PER_MINUTE = 60000.0`)

#### B) Pine Script Semantics & API
- [ ] **B1:** `strategy.entry()` uses only `strategy.long` or `strategy.short`
- [ ] **B2:** `strategy.exit()` stop/limit not swapped; no `na` prices without guards
- [ ] **B3:** Type compatibility (`ta.barssince(bool)`, no bool/int confusion)
- [ ] **B4:** `request.security()` has explicit `lookahead`, `gaps`, AND data persistence (na fallbacks)
- [ ] **B5:** All `var` declarations have explicit type and initial value
- [ ] **B6:** Pyramiding logic matches settings (check `strategy.position_size == 0` if pyramiding=0)
- [ ] **B7:** Repainting patterns explicit (`calc_on_every_tick`, `request.security` lookahead)
- [ ] **B8:** All `ta.*` functions called unconditionally (not inside `if` blocks or loops)

#### C) Directionality & Polarity
- [ ] **C1:** Long stops **below** entry, short stops **above** entry ← **Critical upside-down check**
- [ ] **C2:** Long TP **above** entry, short TP **below** entry ← **Critical upside-down check**
- [ ] **C3:** Stop/target values don't become `na` during position (no silent sign flips)
- [ ] **C5:** Price references captured at entry (use `strategy.position_avg_price` or capture on fill)

#### D) Session, Reset, State Integrity
- [ ] **D1:** Every `var` has explicit reset logic (session boundary or flat state)
- [ ] **D2:** Session boundaries match intent (RTH close vs midnight)
- [ ] **D3:** Centralized `canTrade` gate controls all entries
- [ ] **D4:** Entry tracking (`entryBar`, counters, flags) resets when flat

#### E) External Data Integrity
- [ ] **E1:** Missing external data behavior explicit (fail-open vs fail-closed)
- [ ] **E2:** `request.security()` handles `na` and session gaps with `barmerge.gaps_off`

---

### ⚠️ HIGH (Should Pass) — Review & Fix or Document

#### B) Pine Script Semantics
- [ ] **B6:** Pyramiding logic coherent (if pyramiding=0, check position before entry; if enabled, document intent)
- [ ] **B7:** Repainting risks documented (`calc_on_every_tick` with bar functions, `request.security` lookahead)

#### C) Directionality
- [ ] **C4:** Entry IDs match direction (ID "Long" uses `strategy.long`, not `strategy.short`)

#### E) External Data
- [ ] **E3:** All external symbols enumerated in header/metadata
- [ ] **E4:** Symbol requirements documented (required vs optional; fail-open vs fail-closed)

#### F) Reachability & Contradictions
- [ ] **F1:** Long/short entries are mutually exclusive (or explicit sequencing)
- [ ] **F2:** No always-true (`high >= low`) or never-true (`close > high`) conditions
- [ ] **F4:** Exit logic reachable given time limits, stops, and session closes

---

### 🔍 WARNINGS (Review Recommended) — Note for Awareness

#### G) Suspicious Patterns
- [ ] **G1:** Commission < ~10% of typical trade value (context-dependent)
- [ ] **G2:** Stop distance reasonable for asset (prefer ATR-normalized: `stopDist > 4*ATR` → warning)
- [ ] **G3:** Entry frequency not suspicious (not almost-always or almost-never true)
- [ ] **G4:** Bar Magnifier assumption documented (tight stops/targets validated on lower TF)

#### H) Observability (Dev Best Practice)
- [ ] **H1:** Key states visualized during dev (OR levels, veto flags, session boundaries)
- [ ] **H2:** Veto reasons visible (labels/plots when veto active)
- [ ] **H3:** Debug visuals behind `input.bool(debugMode)` toggle
- [ ] **H4:** Pre-flight status block (table/logs showing config and filter states)

---

## Common "Upside-Down Logic" Bugs

These are the **most frequent logic inversions** caught by these checks:

### 1. Stop Loss Wrong Direction (C1)
```pine
// ❌ BAD: Stop for long is ABOVE entry (exits immediately!)
if strategy.position_size > 0
  stop = strategy.position_avg_price + 10  // WRONG!
  strategy.exit("Stop", stop=stop)

// ✅ GOOD: Stop for long is BELOW entry
if strategy.position_size > 0
  stop = strategy.position_avg_price - 10
  strategy.exit("Stop", stop=stop)
```

### 2. Entry Direction Mismatch (B1, C4)
```pine
// ❌ BAD: ID says "Long" but using short direction
strategy.entry("Long", strategy.short)  // WRONG!

// ✅ GOOD: ID matches direction
strategy.entry("Long", strategy.long)
```

### 3. Stale Price Reference (C5)
```pine
// ❌ BAD: Using current ATR for historical position
if strategy.position_size > 0
  stop = close - (2 * ta.atr(14))  // Wrong reference!

// ✅ GOOD: Capture ATR at entry
var float entryAtr = na
if position opened
  entryAtr := ta.atr(14)
stop = entryRefPrice - (2 * entryAtr)
```

### 4. No State Reset (D1, D4)
```pine
// ❌ BAD: Counter never resets
var int tradesToday = 0
if filled
  tradesToday += 1  // Accumulates forever!

// ✅ GOOD: Reset at session boundary
var int tradesToday = 0
if isFirstBar
  tradesToday := 0
```

### 5. Division by Zero (A2)
```pine
// ❌ BAD: rthClose can be na or zero
gapPct = (open - rthClose) / rthClose  // CRASH!

// ✅ GOOD: Guard with check
gapPct = (not na(rthClose) and rthClose != 0) ?
  (open - rthClose) / rthClose : na
```

### 6. Pyramiding Logic Mismatch (B6)
```pine
// ❌ BAD: pyramiding=0 but multiple entry attempts
strategy("Test", overlay=true)  // pyramiding=0 by default

if crossover(ma1, ma2)
  strategy.entry("Long", strategy.long)
if rsi < 30
  strategy.entry("Long", strategy.long)  // Silently ignored if already long!

// ✅ GOOD: Check position before entry
if crossover(ma1, ma2) and strategy.position_size == 0
  strategy.entry("Long", strategy.long)
```

### 7. Repainting Risk (B7)
```pine
// ❌ BAD: request.security without explicit lookahead
dailyClose = request.security(syminfo.tickerid, "D", close)
// Historical: sees future (completed bar)
// Real-time: bar still forming

// ✅ GOOD: Explicit lookahead_off
dailyClose = request.security(syminfo.tickerid, "D", close,
  barmerge.gaps_off, barmerge.lookahead_off)
```

### 8. ta. Functions in Conditionals (B8)
```pine
// ❌ BAD: ATR only calculated conditionally
if isRth
  float atr = ta.atr(14)  // State breaks outside RTH!

// Later: atr is stale or na

// ✅ GOOD: Calculate unconditionally, use conditionally
float atr = ta.atr(14)  // Every bar

if isRth
  stopDist = 2 * atr  // Use the value
```

### 9. External Data Persistence (B4 expanded)
```pine
// ❌ BAD: No fallback for na data
tickValue = request.security("NYSE:TICK", timeframe.period, close)
if tickValue > 700  // na > 700 = false (silent failure!)
  // Veto intended but not applied

// ✅ GOOD: Explicit na handling
tickValue = request.security("NYSE:TICK", timeframe.period, close,
  barmerge.gaps_off, barmerge.lookahead_off)
tickValid = not na(tickValue)
tickVeto = tickValid ? (tickValue > 700) : true  // Fail-closed
```

### 10. Bar Magnifier Assumption (G4)
```pine
// ⚠️ WARNING: Tight stops on 5-min bars
// If bar range includes both stop AND target,
// backtest assumes target hit first (optimistic!)

// Solution: Validate on 1-min bars or document assumption
// EXECUTION MODEL: Bar Magnifier favorable execution assumed
// Strategy validated on 1m timeframe; 5m used for overview
```

---

## Validation Workflow

### Pass 1: CRITICAL Checks (A, B, C1-C3/C5, D, E1-E2)
- Any failures → **Block** and fix immediately

### Pass 2: HIGH Checks (C4, E3-E4, F1-F2-F4)
- Findings → Review and fix, or document as intentional

### Pass 3: WARNINGS (G1-G3)
- Note for user awareness
- Verify intentional

### Pass 4: Dev Practices (H1-H3)
- Implement observability during development
- Disable for production via toggle

---

## Severity Quick Guide

| Symbol | Level | Meaning |
|--------|-------|---------|
| 🔴 | **CRITICAL** | Code is broken; must fix |
| 🟡 | **HIGH** | Likely bug; should fix or document |
| 🟠 | **MEDIUM** | May be issue; review recommended |
| 🔵 | **WARNING** | Suspicious but not error; note for awareness |

---

## When to Use This Checklist

**Always:**
- Before committing code
- After significant logic changes
- When debugging unexpected behavior

**Recommended:**
- Code review with peers
- Porting strategy to new symbol/timeframe
- Adding new features/filters

**Not Required:**
- For strategy evaluation (profitability, optimization)
- For parameter tuning
- For backtest analysis (win rate, profit factor, etc.)

---

## Key Principle

> **These checks validate that your code does what you intend it to do.**
> 
> **They do NOT evaluate whether what you intend is a good trading idea.**

Strategy logic and trading decisions remain **entirely your domain expertise**.

---

## Examples of Scope

### ✅ AI WILL Check:
- "Your long stop is above entry price — this will exit immediately" (BUG)
- "You're dividing by `rthClose` which can be `na`" (BUG)
- "Entry ID is 'Long' but using `strategy.short`" (BUG)

### ❌ AI WILL NOT Check:
- "Your stop is too tight for this volatility" (STRATEGY EVALUATION)
- "Your win rate is low; try different parameters" (STRATEGY EVALUATION)
- "This indicator combination doesn't work well" (STRATEGY EVALUATION)

---

**Full Documentation:** `/docs/LOGICAL_SANITY_CHECKS.md` (1,027 lines with code examples)

**Related:** 
- `/docs/PINE_SCRIPT_STANDARDS.md` — Coding standards (Categories 1-8)
- `/.cursorrules` — Complete code review checklist (Categories 1-9)

**Version:** 1.3 | **Last Updated:** January 8, 2026
