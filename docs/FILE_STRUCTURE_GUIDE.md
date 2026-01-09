# Pine Script File Structure Guide

## Overview
This document defines the standard file organization for all Pine Script projects in this repository. Following this structure ensures consistency, maintainability, and easy version tracking.

---

## The Recommended Structure

### Basic Layout
```
scripts/
└── [type]/
    └── [project-name]/
        ├── [project-name].pine           <-- LIVE file (always current version)
        ├── [project-name].md             <-- Documentation
        └── archive/                      <-- Version history
            ├── [project-name]_v1.0.0.pine
            ├── [project-name]_v1.1.0.pine
            └── [project-name]_v1.2.0_feature.pine
```

### Types
- **strategies/** - Trading strategies with entry/exit logic
- **indicators/** - Technical indicators (RSI, MACD, custom indicators)
- **studies/** - Other analysis tools and research scripts

---

## Key Principles

### 1. Live File at Project Root
The main Pine Script file at the project root is **ALWAYS** the current working version.

✅ **Correct:**
```
scripts/strategies/range-scalper/range-scalper.pine
```

❌ **Incorrect:**
```
scripts/strategies/range-scalper/v1.0.3/range-scalper.pine
```

**Why?** You always know where to find the latest code without navigating through nested folders.

---

### 2. Flat Archive Structure
Historical versions live in a flat `archive/` folder with version-tagged filenames.

✅ **Correct:**
```
archive/
├── range-scalper_v1.0.0.pine
├── range-scalper_v1.0.1.pine
├── range-scalper_v1.0.2.pine
└── range-scalper_v1.0.3.pine
```

❌ **Incorrect:**
```
v1.0.0/
└── v1.0.1/
    └── v1.0.2/
        └── v1.0.3/
            └── range-scalper.pine
```

**Why?** Flat structure prevents confusion and makes all versions visible at a glance.

---

### 3. Naming Convention Rules

#### File Names
- **Prefix**: Always use the project name first
- **Version Tag**: Use `vX.X.X` format
- **Optional Descriptor**: Add keyword for major changes (e.g., `_atr-patch`)
- **Case**: Lowercase with hyphens (not underscores or mixed case)
- **Extension**: `.pine`

**Format:**
```
[project-name]_v[X.X.X]_[optional-descriptor].pine
```

**Examples:**
```
✅ range-scalper_v1.0.2.pine
✅ range-scalper_v1.0.3_atr-patch.pine
✅ es-professional-fade-strategy_v2.5.4_exec-gap.pine

❌ RangeScalper_1.0.2.pine           (wrong case)
❌ v1.0.2_range_scalper.pine         (version first)
❌ range-scalper-v1.0.2.pine         (hyphen before version)
```

#### Project Folder Names
- Lowercase with hyphens
- Descriptive and concise
- Match the script name

**Examples:**
```
✅ range-scalper/
✅ es-professional-fade-strategy/
✅ macd-histogram-divergence/

❌ RangeScalper/
❌ ES_Professional_Fade_Strategy/
❌ MACD-Histogram-Divergence/
```

---

## File Structure Examples

### Example 1: Indicator
```
scripts/
└── indicators/
    └── range-scalper/
        ├── range-scalper.pine               <-- Current version (v1.0.3)
        ├── range-scalper.md                 <-- Documentation
        └── archive/
            ├── range-scalper_v1.0.0.pine
            ├── range-scalper_v1.0.1.pine
            ├── range-scalper_v1.0.2_dynamic-thresh.pine
            └── range-scalper_v1.0.3.pine
```

### Example 2: Strategy
```
scripts/
└── strategies/
    └── es-professional-fade-strategy/
        ├── es-professional-fade-strategy.pine    <-- Current version (v2.5.4)
        ├── es-professional-fade-strategy.md      <-- Documentation
        └── archive/
            ├── es-professional-fade-strategy_v2.5.0.pine
            ├── es-professional-fade-strategy_v2.5.1.pine
            ├── es-professional-fade-strategy_v2.5.2.pine
            ├── es-professional-fade-strategy_v2.5.3.pine
            └── es-professional-fade-strategy_v2.5.4_exec-gap.pine
```

---

## Version File Headers

Every archived version should include a standardized header with change log:

```pine
//@version=5
// =============================================================================
// [TYPE]: [Script Name]
// FILENAME: [exact-filename.pine]
// VERSION:  v[X.X.X]
// AUTHOR:   [Your Name/Team]
// DATE:     YYYY-MM-DD
// =============================================================================
/* CHANGE LOG:
   v[X.X.X] - [Major change description]
            - [Additional change]
            - [Additional change]
            
   STRENGTHS: [What this version does well]
   WEAKNESSES: [Known issues or limitations]
   ============================================================================= */
```

**Example:**
```pine
//@version=5
// =============================================================================
// STRATEGY: ES Professional Fade
// FILENAME: es-professional-fade-strategy_v2.5.4_exec-gap.pine
// VERSION:  v2.5.4
// AUTHOR:   Trading Team
// DATE:     2026-01-08
// =============================================================================
/* CHANGE LOG:
   v2.5.4 - Implemented 'Execution Penalty' logic (Slippage simulation).
          - Added time-decaying friction model (penalty expires after X mins).
          - Migrated to STOP orders for more realistic fill simulation.
          
   STRENGTHS: High-volatility open regimes, realistic execution modeling.
   WEAKNESSES: Sustained Trend Days (addressed via $TICK veto).
   ============================================================================= */
```

---

## Documentation (.md) Files

Each project should include a `.md` documentation file at the project root. Use the template at:
```
docs/SCRIPT_DOCUMENTATION_TEMPLATE.md
```

Minimum required sections:
- **Overview**: What the script does
- **Current Version**: Version number
- **Features**: Key capabilities
- **Parameters**: All configurable inputs
- **Usage**: How to apply the script
- **Last Updated**: Date

---

## Why This Structure?

### Problems with Nested Folders
❌ **The Old Way:**
```
scripts/strategies/range-scalper/v1.0.0/v1.0.1/v1.0.2/v1.0.3.pine
```

**Issues:**
1. **Confusing**: Folder name (v1.0.2) doesn't match file version (v1.0.3)
2. **Inefficient**: Must click through 4+ folders to find the latest version
3. **Error-Prone**: Easy to use the wrong version
4. **Poor Git Diffs**: Hard to compare versions in nested structures

### Benefits of Flat Structure
✅ **The New Way:**
```
scripts/strategies/range-scalper/
├── range-scalper.pine
├── range-scalper.md
└── archive/
    ├── range-scalper_v1.0.0.pine
    ├── range-scalper_v1.0.1.pine
    ├── range-scalper_v1.0.2.pine
    └── range-scalper_v1.0.3.pine
```

**Benefits:**
1. **Clear**: Live file is always at project root
2. **Fast**: All versions visible at a glance
3. **Reliable**: No confusion about which version is current
4. **Git-Friendly**: Easy to track changes and compare versions

---

## Workflow

### Creating a New Project
1. Create project folder: `scripts/[type]/[project-name]/`
2. Create live file: `[project-name].pine`
3. Create documentation: `[project-name].md` (use template)
4. Create archive folder: `archive/`
5. Add initial version: `archive/[project-name]_v1.0.0.pine`

### Updating an Existing Project
1. Copy current live file to archive with version tag:
   ```
   cp [project-name].pine archive/[project-name]_v[X.X.X].pine
   ```
2. Add change log header to archived version
3. Make changes to live file
4. Update version number in live file
5. Update documentation `.md` file
6. Commit changes to Git

### Version Numbering
Follow semantic versioning:
- **Major** (v2.0.0): Breaking changes, complete rewrites
- **Minor** (v1.1.0): New features, significant improvements
- **Patch** (v1.0.1): Bug fixes, small tweaks

Add descriptive tags for major changes:
- `_exec-gap` - Execution modeling added
- `_atr-patch` - ATR filter improvements
- `_volume-filter` - Volume confirmation added

---

## Quick Reference

### Do's ✅
- Keep live file at project root
- Use flat archive structure
- Version tag all archived files
- Include change log headers
- Use lowercase-with-hyphens naming
- Document each project

### Don'ts ❌
- Don't nest version folders
- Don't put version number in folder name
- Don't use mixed case or underscores
- Don't skip documentation
- Don't leave orphaned test files
- Don't forget to archive old versions

---

## Questions?

If you're unsure about structure, refer to these example projects:
- `scripts/strategies/es-professional-fade-strategy/`
- `scripts/strategies/momentum-breakout-strategy/`
- `scripts/indicators/range-scalper/`
- `scripts/indicators/macd-histogram-divergence/`

For template files, see:
- `docs/SCRIPT_DOCUMENTATION_TEMPLATE.md`
- `docs/FILE_STRUCTURE_GUIDE.md` (this file)

---

**Last Updated:** 2026-01-08
