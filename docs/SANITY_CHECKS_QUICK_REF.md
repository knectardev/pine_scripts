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
- [ ] **B4:** `request.security()` has explicit `lookahead` and `gaps` handling
- [ ] **B5:** All `var` declarations have explicit type and initial value

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

#### H) Observability (Dev Best Practice)
- [ ] **H1:** Key states visualized during dev (OR levels, veto flags, session boundaries)
- [ ] **H2:** Veto reasons visible (labels/plots when veto active)
- [ ] **H3:** Debug visuals behind `input.bool(debugMode)` toggle

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

**Version:** 1.2 | **Last Updated:** January 8, 2026
