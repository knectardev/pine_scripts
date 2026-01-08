# Pine Script v5 Coding Standards

## Official TradingView Documentation References

This document consolidates the official TradingView Pine Script v5 coding standards from:
- [Style Guide](https://www.tradingview.com/pine-script-docs/v5/writing/style-guide/)
- [Debugging Guide](https://www.tradingview.com/pine-script-docs/v5/writing/debugging/)
- [Profiling and Optimization](https://www.tradingview.com/pine-script-docs/v5/writing/profiling-and-optimization/)
- [Limitations](https://www.tradingview.com/pine-script-docs/v5/writing/limitations/)

**Last Updated:** January 8, 2026

---

## 1. Naming Conventions

### Variables and Functions
- **Use `camelCase`** for all identifiers:
  - Variables: `ma`, `maFast`, `maLengthInput`, `maColor`
  - Functions: `roundedOHLC()`, `pivotHi()`, `calculateSignal()`

### Constants
- **Use All Caps `SNAKE_CASE`** for constants:
  - `BULL_COLOR`, `BEAR_COLOR`, `MAX_LOOKBACK`
  - `MS_IN_MIN`, `MS_IN_HOUR`, `MS_IN_DAY`

### Qualifying Suffixes
Use suffixes to provide context about variable type or purpose:
- **Input variables**: `maLengthInput`, `bearColorInput`, `showAvgInput`
- **Arrays**: `volumesArray`, `levelsColorArray`
- **Plot IDs**: `maPlotID`
- **Tables**: `resultsTable`
- **Colors**: `bearColor`, `bullColor`

---

## 2. Script Organization

**CRITICAL:** Scripts must follow this exact structure:

```pine
<license>
<version>
<declaration_statement>
<import_statements>
<constant_declarations>
<inputs>
<function_declarations>
<calculations>
<strategy_calls>
<visuals>
<alerts>
```

### 2.1 License (Required for Published Scripts)

```pine
// This source code is subject to the terms of the Mozilla Public License 2.0 at https://mozilla.org/MPL/2.0/
// © username
```

### 2.2 Version Declaration (Required)

```pine
//@version=5
```

### 2.3 Declaration Statement (Required)

Must be one of:
- `indicator()`
- `strategy()`
- `library()`

```pine
indicator("My Indicator", overlay=true)
```

### 2.4 Import Statements (If Using Libraries)

```pine
import username/library_name/1 as lib
```

### 2.5 Constant Declarations

**Rules:**
- Use `const` keyword for compile-time constants
- Use `SNAKE_CASE` naming
- Initialize with literals or built-in constants only
- Group all constants together near the top

```pine
// ————— Constants
int MS_IN_MIN = 60 * 1000
int MS_IN_HOUR = MS_IN_MIN * 60
int MS_IN_DAY = MS_IN_HOUR * 24

color GRAY = #808080ff
color LIME = #00FF00ff
color MAROON = #800000ff

color BG_DIV = color.new(MAROON, 90)
color BG_RESETS = color.new(GRAY, 90)

string RST1 = "No reset; cumulate since the beginning of the chart"
string RST2 = "On a stepped higher timeframe (HTF)"
```

**DON'T:**
- Don't use `var` for constants (minor performance penalty)
- Don't scatter constants throughout the code
- Don't use literals directly when used multiple times

### 2.6 Inputs

**Rules:**
- Group ALL inputs together
- Place near the beginning of script
- Use `Input` suffix for input variable names
- Use descriptive tooltips for complex inputs

```pine
// ————— Inputs
int maLengthInput = input.int(14, "MA Length", minval=1, maxval=200)
color bullColorInput = input.color(color.green, "Bull Color")
bool showSignalsInput = input.bool(true, "Show Signals")
string resetInput = input.string(RST1, "Reset Mode", options=[RST1, RST2])
```

### 2.7 Function Declarations

**Rules:**
- Define all functions in global scope (no nested functions)
- Minimize use of global variables within functions
- Document with standard comment format
- Place functions before calculations section

```pine
// @function Calculates moving average with custom smoothing
// @param source (series float) The data source to smooth
// @param length (simple int) The averaging period
// @returns (series float) The smoothed value
// Dependencies: None
customMA(series float source, simple int length) =>
    sum = 0.0
    for i = 0 to length - 1
        sum := sum + source[i]
    sum / length
```

### 2.8 Calculations

Place core script logic and calculations here.

```pine
// ————— Calculations
maValue = ta.sma(close, maLengthInput)
signal = close > maValue ? 1 : -1
```

### 2.9 Strategy Calls (For Strategies Only)

Group all strategy entry/exit calls together:

```pine
// ————— Strategy Calls
if signal == 1
    strategy.entry("Long", strategy.long)
else if signal == -1
    strategy.close("Long")
```

### 2.10 Visuals

**All visual output should be grouped together:**
- `plot()` calls
- `plotshape()` calls
- `bgcolor()` calls
- `plotcandle()` calls
- Drawing objects (lines, boxes, labels, tables)

```pine
// ————— Visuals
plot(maValue, "MA", color=color.blue, linewidth=2)
plotshape(signal == 1, style=shape.triangleup, location=location.belowbar, 
     color=color.green, size=size.small)
bgcolor(signal == 1 ? color.new(color.green, 90) : na)
```

### 2.11 Alerts (At End)

Alert code should be at the end since it requires calculations to complete:

```pine
// ————— Alerts
alertcondition(signal == 1, "Buy Signal", "Long entry signal detected")
```

---

## 3. Spacing and Formatting

### 3.1 Operator Spacing

**Use spaces around all binary operators:**

```pine
// ✅ GOOD
int a = close > open ? 1 : -1
float result = (high + low) / 2
bool condition = close > ma and volume > avgVolume

// ❌ BAD
int a=close>open?1:-1
float result=(high+low)/2
```

**Exception:** No space for unary operators:

```pine
// ✅ GOOD
float a = -b
int negative = -1

// ❌ BAD
float a = - b
```

### 3.2 Comma and Argument Spacing

```pine
// ✅ GOOD - Space after comma
plot(close, title="Close", color=color.red, linewidth=2)

// ✅ GOOD - Space around named arguments
strategy.entry(id="Long", direction=strategy.long, qty=10)

// ❌ BAD - No spaces
plot(close,title="Close",color=color.red)
```

### 3.3 Line Wrapping

**Use indentation that is NOT a multiple of 4 spaces (typically 2 spaces):**

```pine
// ✅ GOOD - 2-space indent for continuation
longLabel = label.new(
  x=bar_index,
  y=high,
  text="Buy Signal",
  style=label.style_label_up,
  color=color.green
)

plot(
  series=close,
  title="Close Price",
  color=color.blue,
  linewidth=2,
  show_last=10
)

// ❌ BAD - 4-space indent looks like local block
plot(
    series=close,
    title="Close"
)
```

### 3.4 Vertical Alignment

Use alignment for similar declarations to improve readability:

```pine
// ✅ GOOD - Aligned declarations
color COLOR_AQUA    = #0080FFff
color COLOR_BLACK   = #000000ff
color COLOR_BLUE    = #013BCAff
color COLOR_CORAL   = #FF8080ff
color COLOR_GOLD    = #CCCC00ff

int   PERIOD_FAST   = 12
int   PERIOD_SLOW   = 26
int   PERIOD_SIGNAL = 9
```

---

## 4. Type Declarations

### 4.1 Explicit Typing (Recommended)

**Always declare variable types explicitly** for better readability:

```pine
// ✅ GOOD - Explicit types
float ema12 = ta.ema(close, 12)
int barCount = bar_index
bool isUptrend = close > open
string message = "Signal detected"

// ❌ ACCEPTABLE but less clear
ema12 = ta.ema(close, 12)
barCount = bar_index
```

**Benefits:**
- Easier to read and understand
- Helps distinguish declaration (=) from reassignment (:=)
- Makes scripts easier to debug
- Clarifies expected types at each step

---

## 5. Performance Optimization

### 5.1 Avoid Expensive Operations in Loops

```pine
// ❌ BAD - Recalculating inside loop
for i = 0 to 100
    value = ta.sma(close, 50)  // Calculated 101 times!
    array.push(myArray, value)

// ✅ GOOD - Calculate once before loop
smaValue = ta.sma(close, 50)
for i = 0 to 100
    array.push(myArray, smaValue)
```

### 5.2 Use Built-in Functions

```pine
// ❌ BAD - Manual calculation
sum = 0.0
for i = 0 to length - 1
    sum := sum + close[i]
average = sum / length

// ✅ GOOD - Built-in function (much faster)
average = ta.sma(close, length)
```

### 5.3 Minimize History Operator [] Usage

```pine
// ❌ BAD - Multiple lookbacks
if close[1] > close[2] and close[2] > close[3]
    // ...

// ✅ GOOD - Store in variables
prev1 = close[1]
prev2 = close[2]
prev3 = close[3]
if prev1 > prev2 and prev2 > prev3
    // ...
```

### 5.4 Limit Plot Counts

```pine
// Use conditional plots to stay within limits
if showSignalsInput
    plot(signal, "Signal")
```

---

## 6. Pine Script Limitations

### 6.1 Plot Limits

**Maximum 64 plot counts per script**

Plot count includes:
- `plot()` calls
- `plotshape()`, `plotchar()`, `plotarrow()`
- `plotcandle()`, `plotbar()`
- `hline()`
- `fill()` between plots
- `alertcondition()`

**Strategies count toward 64 plot limit:**
- Equity curve
- Each series plotted
- Each plotshape/plotchar

**Workarounds:**
- Use conditional plotting with `if` statements
- Combine multiple series into one plot with color changes
- Use drawing objects (labels, lines, boxes) instead of plots
- Split functionality into multiple indicators

```pine
// ❌ BAD - Will hit limit quickly
plot(ma5)
plot(ma10)
plot(ma20)
plot(ma50)
plot(ma100)
plot(ma200)
// ... 58 more plots

// ✅ GOOD - Conditional plotting
showMA5  = input.bool(true, "Show MA5")
showMA10 = input.bool(true, "Show MA10")
plot(showMA5  ? ta.sma(close, 5)  : na, "MA5",  color.red)
plot(showMA10 ? ta.sma(close, 10) : na, "MA10", color.blue)
```

### 6.2 Script Size Limits

- **Maximum compile time:** 40 seconds
- **Maximum execution time per bar:** Limited (varies by plan)
- **Maximum local scopes:** 500
- **Maximum variables per scope:** 1000

**Best Practices:**
- Keep scripts under 10,000 lines
- Avoid deeply nested structures
- Use libraries for shared code
- Optimize loops and calculations

### 6.3 Historical Data Limits

- **Default history:** ~5000 bars
- **Maximum `max_bars_back`:** 5000 bars
- **`var` variables:** Persist across all bars
- **History references `[]`:** Limited by available data

```pine
// ✅ GOOD - Declare expected history
indicator("My Indicator", max_bars_back=500)

// ✅ GOOD - Check for sufficient data
if bar_index >= 50
    value = ta.sma(close, 50)
    plot(value)
```

### 6.4 Loop Limits

- **Maximum iterations:** 500,000 per script execution
- Applies to: `for`, `while` loops

```pine
// ❌ BAD - Could exceed limit
for i = 0 to bar_index  // On bar 10000, this runs 10,000 times
    // ...

// ✅ GOOD - Bounded loop
maxIterations = math.min(bar_index, 500)
for i = 0 to maxIterations
    // ...
```

### 6.5 Drawing Objects Limits

| Object Type | Maximum Per Script |
|------------|-------------------|
| Lines | ~500-550 visible |
| Boxes | ~500-550 visible |
| Labels | ~500-550 visible |
| Tables | 1 per script |
| Polylines | ~100 visible |

**Best Practices:**
- Delete old drawings when creating new ones
- Use `line.delete()`, `label.delete()`, etc.
- Keep track of drawing arrays and manage lifecycle

```pine
// ✅ GOOD - Manage drawing lifecycle
var line[] lines = array.new_line()
if array.size(lines) > 50
    line.delete(array.shift(lines))

newLine = line.new(bar_index, high, bar_index+10, low)
array.push(lines, newLine)
```

---

## 7. Debugging Best Practices

### 7.1 Use Pine Logs (Preferred Method)

```pine
// ✅ GOOD - Pine Logs for debugging
log.info("Entry condition met: price={0}, signal={1}", close, signal)
log.warning("Unusual volume: {0}", volume)
log.error("Invalid parameter: length must be > 0")
```

**Benefits:**
- Doesn't affect chart visuals
- Can be filtered and searched
- Supports string formatting
- Better for complex debugging

### 7.2 Using Labels for Values

```pine
// ✅ GOOD - Display values on chart
if barstate.islast
    label.new(bar_index, high, 
      text="MA: " + str.tostring(maValue) + "\nSignal: " + str.tostring(signal),
      style=label.style_label_down)
```

### 7.3 Using Tables for Multiple Values

```pine
// ✅ GOOD - Table for multiple debug values
var table debugTable = table.new(position.top_right, 2, 5)
if barstate.islast
    table.cell(debugTable, 0, 0, "Indicator", bgcolor=color.gray)
    table.cell(debugTable, 1, 0, "Value", bgcolor=color.gray)
    table.cell(debugTable, 0, 1, "RSI")
    table.cell(debugTable, 1, 1, str.tostring(rsiValue, "#.##"))
    table.cell(debugTable, 0, 2, "MACD")
    table.cell(debugTable, 1, 2, str.tostring(macdValue, "#.##"))
```

### 7.4 Conditional Debugging

```pine
// Use input to enable/disable debug output
debugMode = input.bool(false, "Debug Mode")

if debugMode and signal != signal[1]
    log.info("Signal changed: {0} -> {1}", signal[1], signal)
```

---

## 8. Common Mistakes to Avoid

### 8.1 Using var for Constants

```pine
// ❌ BAD - Unnecessary var
var int THRESHOLD = 100  

// ✅ GOOD - Use const or simple declaration
const int THRESHOLD = 100
```

### 8.2 Recalculating Same Values

```pine
// ❌ BAD
if ta.rsi(close, 14) > 70
    alert("Overbought")
if ta.rsi(close, 14) < 30
    alert("Oversold")

// ✅ GOOD
rsi = ta.rsi(close, 14)
if rsi > 70
    alert("Overbought")
if rsi < 30
    alert("Oversold")
```

### 8.3 Not Checking for Sufficient Data

```pine
// ❌ BAD - May reference invalid data
sma200 = ta.sma(close, 200)
plot(sma200)

// ✅ GOOD - Check bar index
plot(bar_index >= 200 ? ta.sma(close, 200) : na, "SMA 200")
```

### 8.4 Modifying Arrays/Objects Without var

```pine
// ❌ BAD - Array recreated each bar
myArray = array.new_float()

// ✅ GOOD - Array persists across bars
var myArray = array.new_float()
```

---

## 9. Code Review Checklist

Before committing any Pine Script, verify:

- [ ] Uses `//@version=5`
- [ ] Follows script organization structure (license → version → declaration → imports → constants → inputs → functions → calculations → strategy calls → visuals → alerts)
- [ ] Constants use `SNAKE_CASE` and are declared at top
- [ ] Variables use `camelCase`
- [ ] Input variables have `Input` suffix
- [ ] All inputs are grouped together
- [ ] Functions are documented with `@function`, `@param`, `@returns`
- [ ] Explicit type declarations used
- [ ] Spaces around all operators
- [ ] Line wrapping uses 2-space indentation
- [ ] No unnecessary recalculations
- [ ] Stays within 64 plot limit
- [ ] Manages drawing object lifecycle
- [ ] Checks for sufficient historical data before calculations
- [ ] Uses Pine Logs for debugging (remove or disable before publishing)
- [ ] Header comment includes description, author, version, parameters, usage

---

## 10. Quick Reference

### Variable Naming Quick Guide

| Type | Convention | Example |
|------|-----------|---------|
| Regular variable | `camelCase` | `maValue`, `signalStrength` |
| Constant | `SNAKE_CASE` | `MAX_BARS`, `DEFAULT_COLOR` |
| Input variable | `camelCase` + `Input` | `lengthInput`, `colorInput` |
| Function | `camelCase` + `()` | `calculateSignal()`, `drawLabel()` |
| Array | `camelCase` + `Array` | `pricesArray`, `signalsArray` |
| Table | `camelCase` + `Table` | `resultsTable`, `debugTable` |

### Organization Quick Template

```pine
// © username
//@version=5
indicator("My Indicator", overlay=true)

// ————— Constants
const int DEFAULT_LENGTH = 14
const color BULL_COLOR = #26A69A
const color BEAR_COLOR = #EF5350

// ————— Inputs
int lengthInput = input.int(DEFAULT_LENGTH, "Length", minval=1)
color bullColorInput = input.color(BULL_COLOR, "Bull Color")

// ————— Function Declarations
// @function Description
// @param param1 Description
// @returns Description
myFunction(float param1) =>
    param1 * 2

// ————— Calculations
value = myFunction(close)
signal = value > 0

// ————— Visuals
plot(value, "Value", color=signal ? bullColorInput : color.red)
bgcolor(signal ? color.new(bullColorInput, 90) : na)
```

---

## Additional Resources

- **Official Pine Script v5 Documentation:** https://www.tradingview.com/pine-script-docs/v5/
- **Pine Script Reference Manual:** https://www.tradingview.com/pine-script-reference/v5/
- **TradingView Community:** https://www.tradingview.com/scripts/
- **Pine Script Style Guide:** https://www.tradingview.com/pine-script-docs/v5/writing/style-guide/

---

**Document Version:** 1.0.0  
**Pine Script Version:** 5  
**Last Reviewed:** January 8, 2026
