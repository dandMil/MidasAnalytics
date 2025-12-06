# ADR and RSI: Purpose in Stock Screening

## Overview

Ranking stocks by **ADR (Average Daily Range)** and **RSI (Relative Strength Index)** is a common strategy used by traders to identify **high-opportunity stocks** that are in **favorable entry zones**.

## What is ADR? (Average Daily Range)

### Definition
ADR measures the **average percentage range** a stock moves from high to low in a day, calculated over the last 30 days.

**Formula:**
```
ADR% = Average((High - Low) / Close) × 100
```

### Purpose: **Find Volatile Stocks**

**High ADR stocks (3-10%+):**
- ✅ Move significantly each day
- ✅ Provide multiple trading opportunities
- ✅ Better for **day trading** and **swing trading**
- ✅ Higher profit potential (but also higher risk)

**Low ADR stocks (<1%):**
- ❌ Move very little daily
- ❌ Fewer trading opportunities
- ❌ Better for **long-term investing** (not active trading)
- ⚠️ May not move enough to justify transaction costs

### Why Rank by ADR?
Traders want stocks that **move enough** to:
1. **Capture meaningful profits** in short timeframes
2. **Provide entry/exit opportunities** throughout the day
3. **Justify trading costs** (commissions, slippage)
4. **Meet profit targets** quickly

---

## What is RSI? (Relative Strength Index)

### Definition
RSI is a **momentum oscillator** that measures the speed and magnitude of price changes over the last 14 days.

**Range:** 0-100

### Purpose: **Identify Entry Zones**

**RSI < 30 (Oversold):**
- ✅ Stock may be undervalued
- ✅ **Potential buying opportunity**
- ✅ Price may bounce back up
- ✅ Good entry point for mean reversion

**RSI > 70 (Overbought):**
- ⚠️ Stock may be overvalued
- ⚠️ **Potential selling opportunity**
- ⚠️ Price may pull back
- ⚠️ Good exit point or short opportunity

**RSI 30-70 (Neutral):**
- Normal trading range
- No extreme conditions
- Less clear signal

### Why Rank by RSI?
Traders want to find stocks:
1. **Near entry zones** (oversold for buying, overbought for selling)
2. **With momentum potential** (trending up/down)
3. **That haven't exhausted their move** yet

---

## Why Rank by ADR + RSI Together?

### The Strategy

**Find stocks that are:**
1. **Volatile enough to trade** (High ADR) ✅
2. **In favorable entry zones** (RSI signals) ✅

### Common Use Cases

#### 1. **Day Trading Opportunities**
```
High ADR (5%+) + Oversold RSI (<30) = Potential bounce play
High ADR (5%+) + Overbought RSI (>70) = Potential pullback play
```
**Goal:** Capture intraday moves in volatile stocks

#### 2. **Swing Trading Setups**
```
Moderate ADR (2-5%) + Oversold RSI (<30) = Swing long opportunity
Moderate ADR (2-5%) + Overbought RSI (>70) = Swing short opportunity
```
**Goal:** Hold for 2-5 days to capture larger moves

#### 3. **Momentum Plays**
```
High ADR + Rising RSI (30→70) = Strong uptrend, ride the momentum
High ADR + Falling RSI (70→30) = Strong downtrend, short opportunity
```
**Goal:** Follow the trend in volatile stocks

#### 4. **Mean Reversion Trading**
```
High ADR + Extreme RSI (<20 or >80) = Mean reversion opportunity
```
**Goal:** Profit from price returning to average

---

## Your Current Screener Implementation

### Default Sorting: ADR (Descending)

**Why ADR first?**
```python
sort_by = filters.get("sort_by", "adr")  # Default: sort by ADR
```

1. **Prioritize volatility** - Find stocks that move enough to trade
2. **Identify trading candidates** - High ADR = more opportunities
3. **Filter out low-movers** - Stocks that don't move much aren't worth screening

### RSI as Secondary Filter

**Why RSI filtering?**
```python
min_rsi = filters.get("min_rsi", 0.0)
max_rsi = filters.get("max_rsi", 100.0)
rsi_signal = filters.get("rsi_signal", "all")  # "oversold", "overbought", "neutral"
```

1. **Find entry zones** - Filter for oversold/overbought conditions
2. **Timing entry/exit** - Use RSI to determine when to trade
3. **Risk management** - Avoid extreme conditions if desired

---

## Example Scenarios

### Scenario 1: Find Volatile Oversold Stocks
```
Filters:
- min_adr: 3% (find volatile stocks)
- max_adr: 10% (not too volatile)
- min_rsi: 0
- max_rsi: 30 (oversold only)
- Sort by: ADR (desc)

Result: Volatile stocks that are oversold = potential bounce plays
```

### Scenario 2: Find High-Momentum Movers
```
Filters:
- min_adr: 5% (very volatile)
- max_adr: 15%
- min_rsi: 50 (rising momentum)
- max_rsi: 100
- Sort by: ADR (desc)

Result: Very volatile stocks with positive momentum = trend following
```

### Scenario 3: Conservative Swing Trading
```
Filters:
- min_adr: 2% (moderate volatility)
- max_adr: 5%
- min_rsi: 30
- max_rsi: 40 (slightly oversold)
- Sort by: RSI (asc)

Result: Moderately volatile stocks near entry zones = safer swings
```

---

## Real-World Trading Purposes

### Day Traders
- **Use ADR** to find stocks that move 3-5%+ daily
- **Use RSI** to time entries (buy oversold, sell overbought)
- **Goal:** Multiple profitable trades per day

### Swing Traders
- **Use ADR** to find stocks with 2-5% daily ranges
- **Use RSI** to identify swing entry/exit points
- **Goal:** Hold 2-7 days for larger moves

### Position Traders
- **Use ADR** less (focus on longer trends)
- **Use RSI** to identify major reversal points
- **Goal:** Hold weeks/months, use RSI for timing major entries

### Scalpers
- **Use ADR** to find stocks with consistent intraday ranges
- **Use RSI** less (focus on price action)
- **Goal:** Many small profits per day

---

## How Your Screener Uses This

### Current Implementation

1. **Calculates ADR%** for last 30 days
   ```python
   avg_adr_percentage = sum(adr_percentages) / len(adr_percentages)
   ```

2. **Calculates RSI** (14-day)
   ```python
   rsi = calculate_rsi(df['Close'], window=14)
   current_rsi = rsi.iloc[-1]
   ```

3. **Filters by both**:
   ```python
   if (adr >= min_adr and adr <= max_adr and
       rsi >= min_rsi and rsi <= max_rsi):
   ```

4. **Sorts by ADR by default** (configurable)
   ```python
   screened_stocks.sort(key=lambda x: x.get(sort_key, 0), reverse=True)
   ```

### Why This Works

✅ **ADR first** - Prioritizes stocks worth trading (high volatility)
✅ **RSI filtering** - Finds stocks in good entry zones
✅ **Together** - High-opportunity stocks that are ready to trade

---

## Summary

**ADR (Average Daily Range):**
- **Purpose:** Find volatile stocks that move enough to trade
- **Why rank by it:** Prioritize stocks with trading opportunities
- **Use case:** Day trading, swing trading, active trading

**RSI (Relative Strength Index):**
- **Purpose:** Identify entry/exit zones (oversold/overbought)
- **Why filter by it:** Time your entries and exits better
- **Use case:** Entry timing, momentum identification, risk management

**Together:**
- **Purpose:** Find **volatile stocks in favorable entry zones**
- **Why combine:** High opportunity + Good timing = Better trades
- **Result:** Stocks worth trading at the right time

---

## Bottom Line

Your screener ranks by **ADR** to find stocks that **move enough to be worth trading**, and filters by **RSI** to find stocks that are in **favorable entry/exit zones**. This combination helps traders identify **high-opportunity setups** with **good timing** - the holy grail of active trading! 🎯

