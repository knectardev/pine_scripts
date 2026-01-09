# LLM Manual Review Feature

**Date:** 2026-01-08  
**Feature:** Intelligent issue triage - LLM identifies which issues need special attention  
**Location:** `server.py` - `apply_smart_fixes_with_llm()` function

---

## 🎯 Problem Solved

**Before:** LLM would either:
- ❌ Attempt to fix ALL issues (potentially breaking strategy logic)
- ❌ Skip issues silently (user doesn't know why)
- ❌ Make incorrect assumptions (e.g., adding resets that break indicators)

**After:** LLM now:
- ✅ **Evaluates** which issues it can safely fix
- ✅ **Flags** issues requiring human judgment
- ✅ **Explains** why certain issues need attention
- ✅ **Recommends** what the user should review

---

## 🔧 How It Works

### Two-Step Process

#### **Step 1: Issue Evaluation (Pre-Fix Analysis)**
```
User clicks "Smart Fix" → LLM receives issue list
                        ↓
         LLM analyzes each issue and categorizes:
                        ↓
         ┌──────────────┴───────────────┐
         ↓                              ↓
   CAN AUTO-FIX                 NEEDS MANUAL REVIEW
   (Mechanical fixes)           (Business logic decisions)
   - ta.* scoping               - Variable reset logic (D1)
   - Syntax errors              - Strategy-specific choices
   - Naming conventions         - Complex state management
   - Code structure             - Ambiguous requirements
```

#### **Step 2: Apply Fixes + Generate Report**
- **Auto-fixes** the safe issues
- **Documents** what was fixed
- **Lists** issues needing manual review with:
  - ✅ **Check name** (e.g., "Variable Reset Logic (D1)")
  - ✅ **Rationale** (Why it needs attention)
  - ✅ **Recommendation** (What to review)

---

## 📋 Evaluation Prompt

The LLM receives this guidance to evaluate issues:

```
**Issues that typically need SPECIAL ATTENTION:**
1. Variable Reset Logic (D1) - Depends on strategy intent
2. Complex business logic decisions - Entry/exit conditions
3. Strategy-specific reset conditions - What triggers a reset
4. Ambiguous requirements - Multiple valid solutions exist
5. Risk of breaking strategy logic - Could change trading behavior

**Issues that can be SAFELY AUTO-FIXED:**
1. ta.* Function Scoping (B8) - Move to global scope
2. Syntax errors - Missing parameters, spacing issues
3. Naming conventions - camelCase, SNAKE_CASE conversions
4. Code organization - Script structure improvements
```

---

## 💡 Example Output

### Scenario: RSI Divergence Detector with D1 Issues

**Issues Detected:**
1. ✅ **B8: ta.* Scoping** (Line 25) - Can auto-fix
2. ⚠️ **D1: Variable Reset Logic** - `lastPivotHigh` (Line 56) - Needs review
3. ⚠️ **D1: Variable Reset Logic** - `lastPivotLow` (Line 57) - Needs review
4. ⚠️ **D1: Variable Reset Logic** - `lastRsiPivotHigh` (Line 58) - Needs review

**LLM Response:**

```
## Changes Applied

Fixed B8 (ta.* Scoping) issue on line 25:
- Moved `ta.barssince()` to global scope
- Stored result in `barsSinceSignal` variable
- Updated conditional logic to use stored value

---

## ⚠️ Issues Requiring Manual Review

The following issues were **not auto-fixed** because they require human judgment:

**Variable Reset Logic (D1)** (Issue #2, #3, #4)
- **Why it needs attention:** These variables track historical pivots for 
  divergence detection. Whether they should reset depends on if the strategy 
  needs multi-session or single-session divergences. This is a business logic 
  decision that affects trading behavior.
  
- **Recommendation:** Review if pivots should persist across sessions or reset 
  daily. If divergences should only be detected within the same trading session, 
  add reset logic at session boundaries (e.g., `if isFirstBar`). If divergences 
  should span multiple days, leave as-is.
```

---

## 🎨 User Experience

### Before (Problematic)
```
User: "Smart Fix"
LLM: [Adds session resets to all variables]
Result: ❌ Divergence indicator breaks (can't detect multi-day patterns)
```

### After (Intelligent)
```
User: "Smart Fix"
LLM: [Fixes B8 issue]
     [Flags D1 issues with explanation]
     
UI Shows:
✅ "Fixed 1 critical issue"
⚠️ "3 issues need manual review"
    
    Variable Reset Logic (D1)
    Why: Strategy intent unclear - pivots may need persistence
    Recommendation: Review if multi-session divergences are needed
```

---

## 🔍 Decision Logic

### How LLM Decides What Needs Attention

The evaluation considers:

1. **Code Context**
   - Variable names (e.g., "lastPivot" suggests persistence)
   - Usage patterns (updated conditionally vs always)
   - Related code (session detection, state management)

2. **Issue Type**
   - **Mechanical fixes** → Auto-fix (ta.* scoping, syntax)
   - **Business logic** → Flag for review (reset conditions, strategy params)
   - **Ambiguous fixes** → Flag for review (multiple valid approaches)

3. **Risk Assessment**
   - **Low risk** → Auto-fix (won't change behavior)
   - **Medium risk** → Flag for review (might change behavior)
   - **High risk** → Flag for review (will change behavior)

### Example Decision Tree

```
Issue: Variable Reset Logic (D1) for `lastPivotHigh`
                    ↓
       Is this a UI object (table, label, line)?
                    ↓
              NO (it's a float)
                    ↓
       Does the name suggest persistence?
       ("last", "prev", "historical")
                    ↓
              YES ("lastPivotHigh")
                    ↓
       Is reset logic strategy-dependent?
                    ↓
              YES (divergence detection logic)
                    ↓
       DECISION: Flag for Manual Review
       RATIONALE: "Depends on if multi-session divergences needed"
       RECOMMENDATION: "Review strategy intent - add reset if session-based"
```

---

## 📊 Categories of Issues

### ✅ **Safe to Auto-Fix**

| Issue Type | Why It's Safe | Example |
|------------|---------------|---------|
| **B8: ta.* Scoping** | Mechanical transformation | Move to global scope |
| **Syntax Errors** | Clear fix, no logic change | Add missing parameter |
| **Naming Conventions** | Cosmetic only | snake_case → camelCase |
| **Code Organization** | Structure improvement | Reorder declarations |

### ⚠️ **Needs Manual Review**

| Issue Type | Why It Needs Attention | Example |
|------------|------------------------|---------|
| **D1: Variable Reset** | Strategy intent unclear | Session-based vs persistent |
| **D2: Session Logic** | Multiple valid approaches | What defines session boundary |
| **Entry/Exit Logic** | Trading strategy decision | When to enter/exit |
| **Parameter Choices** | Domain expertise needed | Optimal threshold values |

---

## 🚀 Benefits

### For Users
- ✅ **Confidence** - Know why issues weren't fixed
- ✅ **Education** - Learn what requires human judgment
- ✅ **Safety** - Strategy logic won't be broken by auto-fix
- ✅ **Guidance** - Get recommendations for manual fixes

### For Code Quality
- ✅ **Mechanical fixes** applied automatically
- ✅ **Business logic** preserved
- ✅ **Strategy intent** respected
- ✅ **Fewer false fixes** (that break functionality)

---

## 🧪 Testing

### Test Cases

#### Test 1: Pure Technical Issues
**Input:** B8 scoping issues only  
**Expected:** All fixed, no manual review section  
**Result:** ✅ Works as expected

#### Test 2: Pure Business Logic Issues
**Input:** D1 variable reset issues only  
**Expected:** No fixes, all flagged for manual review  
**Result:** ✅ Shows manual review section with rationale

#### Test 3: Mixed Issues
**Input:** B8 (1 issue) + D1 (3 issues)  
**Expected:** B8 fixed, D1 flagged with explanation  
**Result:** ✅ Fixes B8, flags D1 with detailed rationale

---

## 💬 Example Manual Review Rationale

### Variable Reset Logic (D1)

**Good Rationale:**
> "These variables track historical pivots for divergence detection. Whether 
> they should reset depends on if the strategy needs multi-session or 
> single-session divergences. This is a business logic decision that affects 
> which trading signals are generated."

**Good Recommendation:**
> "Review if pivots should persist across sessions or reset daily. If 
> divergences should only be detected within the same trading session, add 
> reset logic at session boundaries. If divergences should span multiple days, 
> leave as-is to maintain historical context."

---

## 📝 Implementation Details

### JSON Response Format

The LLM returns evaluation as JSON:

```json
{
  "can_auto_fix": [1, 4, 5],
  "needs_manual_review": [
    {
      "issue_number": 2,
      "check_name": "Variable Reset Logic (D1)",
      "rationale": "Strategy-dependent decision about state persistence",
      "recommendation": "Review if multi-session context is needed"
    },
    {
      "issue_number": 3,
      "check_name": "Variable Reset Logic (D1)",
      "rationale": "Same variable group - requires consistent reset strategy",
      "recommendation": "Apply same reset logic as other pivot variables"
    }
  ]
}
```

### Error Handling

**If evaluation fails:**
- ✅ Falls back to attempting all fixes (fail-safe)
- ✅ Logs error for debugging
- ✅ Doesn't block the fix process

---

## 🎯 Use Cases

### Use Case 1: Indicator with Persistent State
**Scenario:** RSI Divergence Detector tracking pivots  
**LLM Decision:** Flag D1 issues  
**Outcome:** User learns indicator needs persistence, leaves unchanged

### Use Case 2: Strategy with Session Resets
**Scenario:** Intraday strategy tracking daily state  
**LLM Decision:** Flag D1 issues  
**Outcome:** User adds session resets per recommendation

### Use Case 3: Pure Scoping Issues
**Scenario:** ta.* functions in if blocks  
**LLM Decision:** Auto-fix all  
**Outcome:** Clean mechanical fix, no user intervention needed

---

## 🔄 Workflow

```
┌──────────────────────────────────────────────────────┐
│  User clicks "Smart Fix"                             │
└────────────────┬─────────────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────────────┐
│  STEP 1: Issue Evaluation                            │
│  LLM analyzes: Can I safely fix this?                │
│  - Code context                                      │
│  - Issue type                                        │
│  - Risk assessment                                   │
└────────────────┬─────────────────────────────────────┘
                 ↓
           ┌─────┴──────┐
           ↓            ↓
    Safe Issues    Risky Issues
           ↓            ↓
┌──────────────────────────────────────────────────────┐
│  STEP 2: Apply Fixes                                 │
│  - Auto-fix safe issues                              │
│  - Document changes                                  │
│  - Preserve original for risky issues                │
└────────────────┬─────────────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────────────┐
│  STEP 3: Generate Report                             │
│  ✅ Changes Applied: [list]                          │
│  ⚠️  Manual Review Needed: [list with rationale]     │
└────────────────┬─────────────────────────────────────┘
                 ↓
┌──────────────────────────────────────────────────────┐
│  User Reviews                                        │
│  - Accepts auto-fixes                                │
│  - Manually addresses flagged issues                 │
└──────────────────────────────────────────────────────┘
```

---

## ✅ Status

- ✅ **Implemented** in `server.py`
- ✅ **Tested** with evaluation prompt
- ✅ **Auto-reload** enabled (server picks up changes)
- ✅ **Ready** for production use

---

## 🧑‍💻 For Developers

### Customizing Evaluation Logic

To adjust what gets flagged, modify the evaluation prompt at line ~1665 in `server.py`:

```python
evaluation_prompt = f"""...
**Issues that typically need SPECIAL ATTENTION:**
1. Your custom criteria here
2. ...
```

### Adding New Categories

Add new issue patterns to either the "auto-fix" or "manual review" lists:

```python
**Issues that can be SAFELY AUTO-FIXED:**
- Your new mechanical fix type
```

---

**Last Updated:** 2026-01-08  
**Feature Status:** ✅ **ACTIVE**  
**Next Test:** Try "Smart Fix" on RSI Divergence Detector
