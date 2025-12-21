# Historical Calculation Flow - Detailed Explanation

## Overview

The historical calculation ensures **NO LOOK-AHEAD BIAS** by using only data that would have been available at the reference date. This document explains the step-by-step flow.

---

## Function: `get_historical_stock_data(ticker, reference_date, lookback_days=180)`

This is the core function that calculates all metrics using only historical data up to the reference date.

---

## Step-by-Step Flow

### **Step 1: Fetch Historical Price Data**

```python
bars = get_price_history_at_date(ticker, reference_date, days_back=lookback_days)
```

**What happens:**
- Calls `polygon_client.get_price_history_at_date()`
- Calculates date range: `[reference_date - 180 days, reference_date]`
- API call: `GET /v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}`
- **Critical**: End date is the `reference_date` - no future data!

**Example:**
- Reference date: `2024-09-01`
- Start date: `2024-03-05` (180 days earlier)
- End date: `2024-09-01` ✅
- Returns: All daily bars from March 5 to September 1, 2024

**Data Structure:**
```json
[
  {"t": 1709596800000, "o": 100.50, "h": 102.00, "l": 99.75, "c": 101.25, "v": 1000000},
  {"t": 1709683200000, "o": 101.25, "h": 103.00, "l": 100.50, "c": 102.50, "v": 1200000},
  ...
  {"t": 1725148800000, "o": 125.00, "h": 126.50, "l": 124.25, "c": 125.75, "v": 1500000}  // Last bar on 2024-09-01
]
```

---

### **Step 2: Data Validation**

```python
if not bars or len(bars) < 30:
    return None  # Insufficient data
```

**Checks:**
- At least 30 days of data required (needed for indicators)
- If insufficient, returns `None` (ticker skipped)

---

### **Step 3: Convert to DataFrame**

```python
df = pd.DataFrame(bars)
df = df.rename(columns={"o": "Open", "h": "High", "l": "Low", "c": "Close", "v": "Volume"})
df['Date'] = pd.to_datetime(df['t'], unit='ms')
df.set_index('Date', inplace=True)
df.sort_index(inplace=True)
```

**Transformation:**
- Converts list of dicts to pandas DataFrame
- Maps API column names to readable names
- Converts timestamp (milliseconds) to datetime
- Sets Date as index and sorts chronologically

**Result:**
```
Date       | Open   | High   | Low    | Close  | Volume
-----------|--------|--------|--------|--------|--------
2024-03-05 | 100.50 | 102.00 | 99.75  | 101.25 | 1000000
2024-03-06 | 101.25 | 103.00 | 100.50 | 102.50 | 1200000
...
2024-09-01 | 125.00 | 126.50 | 124.25 | 125.75 | 1500000  ← Last row (reference date)
```

---

### **Step 4: Get "Current" Price**

```python
current_price = df['Close'].iloc[-1]
```

**What this means:**
- Gets the **last close price** in the DataFrame
- This is the close price on the `reference_date`
- This is treated as the "current" price for all calculations
- Example: If reference_date is 2024-09-01, `current_price = 125.75`

**Key Point**: This price is NOT today's price - it's the price as of the reference date!

---

### **Step 5: Calculate Performance Percentages**

#### **5.1: 1-Month Performance**

```python
if len(df) >= 30:
    price_1m_ago = df['Close'].iloc[-30]  # Price 30 days before reference_date
    performance_1m = calculate_performance_percentage(current_price, price_1m_ago)
```

**Calculation:**
- Gets close price from 30 days before reference_date
- Formula: `((current_price - price_1m_ago) / price_1m_ago) * 100`

**Example:**
- Reference date: 2024-09-01
- Current price (2024-09-01): $125.75
- Price 30 days ago (2024-08-02): $120.00
- Performance: `((125.75 - 120.00) / 120.00) * 100 = 4.79%`

**Timeline Visualization:**
```
2024-08-02 ($120.00) ──────────────→ 2024-09-01 ($125.75)
    30 days ago                          Reference Date
    ↓                                     ↓
  Start Price                          Current Price
```

#### **5.2: 3-Month Performance**

```python
if len(df) >= 90:
    price_3m_ago = df['Close'].iloc[-90]  # Price 90 days before reference_date
    performance_3m = calculate_performance_percentage(current_price, price_3m_ago)
```

**Same logic, but:**
- Uses price from 90 days before reference_date
- Shows 3-month trend as it existed at reference_date

#### **5.3: 6-Month Performance**

```python
if len(df) >= 180:
    price_6m_ago = df['Close'].iloc[-180]  # Price 180 days before reference_date
    performance_6m = calculate_performance_percentage(current_price, price_6m_ago)
```

**Same logic, but:**
- Uses price from 180 days before reference_date
- Shows 6-month trend as it existed at reference_date

---

### **Step 6: Calculate ADR (Average Daily Range)**

```python
recent_df = df.tail(30)  # Last 30 days up to reference_date
adr_percentages = []
for _, row in recent_df.iterrows():
    adr_pct = calculate_adr_percentage(row['High'], row['Low'], row['Close'])
    adr_percentages.append(adr_pct)

avg_adr_percentage = sum(adr_percentages) / len(adr_percentages)
```

**ADR Calculation (per day):**
```python
def calculate_adr_percentage(high, low, close):
    return ((high - low) / close) * 100
```

**Example for one day:**
- High: $126.50
- Low: $124.25
- Close: $125.75
- ADR%: `((126.50 - 124.25) / 125.75) * 100 = 1.79%`

**Average ADR:**
- Calculates ADR% for each of the last 30 days
- Averages them together
- Shows typical daily volatility as of reference_date

**Key Point**: Uses last 30 days **up to** reference_date, not last 30 days from today!

---

### **Step 7: Calculate RSI (Relative Strength Index)**

```python
rsi = calculate_rsi(df['Close'], window=14)
current_rsi = rsi.iloc[-1]  # RSI value on reference_date
```

**RSI Calculation:**
```python
def calculate_rsi(prices, window=14):
    delta = prices.diff()  # Price changes
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()  # Average gains
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()  # Average losses
    rs = gain / loss  # Relative strength
    rsi = 100 - (100 / (1 + rs))  # RSI formula
    return rsi
```

**What this does:**
- Calculates RSI using 14-day window
- Uses only prices up to reference_date
- Returns RSI series, takes the last value (RSI on reference_date)

**RSI Signal:**
- RSI < 30: OVERSOLD
- RSI > 70: OVERBOUGHT
- 30 <= RSI <= 70: NEUTRAL

---

### **Step 8: Calculate MACD (Moving Average Convergence Divergence)**

```python
macd_line, macd_signal_line = calculate_macd(df['Close'])
current_macd = macd_line.iloc[-1]
current_macd_signal = macd_signal_line.iloc[-1]
```

**MACD Calculation:**
```python
def calculate_macd(prices, fast=12, slow=26, signal=9):
    ema_fast = prices.ewm(span=12).mean()    # 12-day EMA
    ema_slow = prices.ewm(span=26).mean()    # 26-day EMA
    macd_line = ema_fast - ema_slow          # MACD line
    macd_signal = macd_line.ewm(span=9).mean()  # Signal line
    return macd_line, macd_signal
```

**What this shows:**
- MACD line: Difference between 12-day and 26-day EMAs
- Signal line: 9-day EMA of MACD line
- Uses only data up to reference_date
- Values are as they would have appeared on reference_date

---

### **Step 9: Calculate Stochastic Oscillator**

```python
stochastic_osc = calculate_stochastic_oscillator(df)
current_stochastic = stochastic_osc.iloc[-1]
```

**Stochastic Calculation:**
```python
def calculate_stochastic_oscillator(df, window=14):
    low_min = df['Low'].rolling(window=14).min()    # 14-day low
    high_max = df['High'].rolling(window=14).max()  # 14-day high
    so = 100 * ((df['Close'] - low_min) / (high_max - low_min))
    return so
```

**What this shows:**
- Measures where current price is relative to 14-day price range
- Uses only data up to reference_date
- Value 0-100 (0 = at 14-day low, 100 = at 14-day high)

---

### **Step 10: Calculate ATR (Average True Range)**

```python
atr = calculate_atr(df)
current_atr = atr.iloc[-1]
```

**ATR Calculation:**
```python
def calculate_atr(df, window=14):
    high_low = df['High'] - df['Low']
    high_close = abs(df['High'] - df['Close'].shift())
    low_close = abs(df['Low'] - df['Close'].shift())
    
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=14).mean()
    return atr
```

**What this shows:**
- Measures volatility (average true range over 14 days)
- Uses only data up to reference_date
- Higher ATR = more volatility

---

### **Step 11: Calculate Indicator Scores**

```python
indicator_scores = {
    "MACD": 1 if current_macd > current_macd_signal else -1,  # Bullish if MACD > signal
    "RSI": 1 if current_rsi < 30 else -1 if current_rsi > 70 else 0,  # Bullish if oversold
    "SO": 1 if current_stochastic < 20 else -1 if current_stochastic > 80 else 0,  # Bullish if oversold
    "PRC": 1 if performance_1m > 0 else -1  # Bullish if positive 1M performance
}
```

**Scoring System:**
- `+1`: Bullish signal
- `-1`: Bearish signal
- `0`: Neutral

---

### **Step 12: Calculate Overall Signal**

```python
weights = {"MACD": 0.5, "PRC": 0.3, "RSI": 0.2, "SO": 0.4}
overall_score = sum(indicator_scores[k] * weights[k] for k in indicator_scores)

if overall_score > 0:
    overall_signal = "BULLISH"
elif overall_score < 0:
    overall_signal = "BEARISH"
else:
    overall_signal = "NEUTRAL"
```

**Weighted Score:**
- Combines all indicator scores with weights
- Positive score = BULLISH
- Negative score = BEARISH
- Zero = NEUTRAL

---

### **Step 13: Return Calculated Data**

```python
return {
    "ticker": ticker,
    "current_price": round(current_price, 2),  # Price on reference_date
    "performance_1m": round(performance_1m, 2),
    "performance_3m": round(performance_3m, 2),
    "performance_6m": round(performance_6m, 2),
    "adr_percentage": round(avg_adr_percentage, 2),
    "rsi": round(current_rsi, 2),
    "rsi_signal": rsi_signal,
    "macd": round(current_macd, 2),
    "macd_signal": round(current_macd_signal, 2),
    "stochastic_oscillator": round(current_stochastic, 2),
    "atr": round(current_atr, 2),
    "indicator_scores": indicator_scores,
    "overall_signal": overall_signal,
    "overall_score": round(overall_score, 2),
    "volume_avg_30d": int(recent_df['Volume'].mean()),
    "last_updated": reference_date  # ⚠️ CRITICAL: Uses reference_date, not today!
}
```

---

## Critical Points: No Look-Ahead Bias

### ✅ **What We DO:**

1. **Fetch data up to reference_date only**
   - API call: `start_date` to `reference_date`
   - Never fetches data after reference_date

2. **Use "current" price from reference_date**
   - `current_price = df['Close'].iloc[-1]` (last row)
   - This is the price on reference_date, not today

3. **Calculate metrics using only historical data**
   - Performance: Compares reference_date price to prices from 30/90/180 days earlier
   - Indicators: Calculated using data up to reference_date
   - ADR: Uses last 30 days up to reference_date

4. **Set last_updated to reference_date**
   - `"last_updated": reference_date` (not `datetime.now()`)
   - Clearly indicates these are historical calculations

### ❌ **What We DON'T DO:**

1. **Never fetch future data**
   - No API calls with dates after reference_date

2. **Never use today's price**
   - `current_price` is always from reference_date

3. **Never calculate using future data**
   - All calculations use only data up to reference_date

4. **Never use current timestamp**
   - `last_updated` is reference_date, not `datetime.now()`

---

## Example: Complete Calculation

**Input:**
- Ticker: `AAPL`
- Reference Date: `2024-09-01`
- Lookback Days: `180`

**Step-by-Step:**

1. **Fetch Data**: Gets bars from `2024-03-05` to `2024-09-01`
2. **Current Price**: Last close on `2024-09-01` = `$178.50`
3. **1M Performance**: 
   - Price on `2024-08-02` (30 days ago) = `$172.00`
   - Performance: `((178.50 - 172.00) / 172.00) * 100 = 3.78%`
4. **3M Performance**: 
   - Price on `2024-06-03` (90 days ago) = `$165.00`
   - Performance: `((178.50 - 165.00) / 165.00) * 100 = 8.18%`
5. **6M Performance**: 
   - Price on `2024-03-05` (180 days ago) = `$150.00`
   - Performance: `((178.50 - 150.00) / 150.00) * 100 = 19.00%`
6. **ADR**: Average of daily ranges for `2024-08-03` to `2024-09-01` (30 days)
7. **RSI**: Calculated using prices from `2024-03-05` to `2024-09-01`
8. **MACD**: Calculated using prices from `2024-03-05` to `2024-09-01`
9. **Stochastic**: Calculated using prices from `2024-03-05` to `2024-09-01`
10. **ATR**: Calculated using prices from `2024-03-05` to `2024-09-01`

**Result:** All metrics reflect how AAPL would have appeared on `2024-09-01`, using only data available up to that date.

---

## Data Flow Diagram

```
Reference Date: 2024-09-01
    ↓
┌─────────────────────────────────────────┐
│ get_price_history_at_date()            │
│ Start: 2024-03-05                      │
│ End:   2024-09-01 ✅ (NOT future!)    │
└─────────────────────────────────────────┘
    ↓
Returns: [180 days of bars up to 2024-09-01]
    ↓
┌─────────────────────────────────────────┐
│ DataFrame (sorted chronologically)     │
│ 2024-03-05 | ... | 2024-09-01 ← Last  │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Calculate Metrics                      │
│ • current_price = Close[-1]            │
│   (Price on 2024-09-01)                │
│ • performance_1m = vs Close[-30]       │
│   (vs price 30 days before 2024-09-01) │
│ • ADR = avg of last 30 days            │
│   (Days up to 2024-09-01)              │
│ • RSI/MACD/etc = using all data        │
│   (Up to 2024-09-01)                   │
└─────────────────────────────────────────┘
    ↓
Returns: Historical metrics as of 2024-09-01
```

---

## Why This Matters

**Without this approach:**
- If we used today's price with historical reference date → WRONG
- If we calculated indicators using future data → LOOK-AHEAD BIAS
- If we used today's date in last_updated → MISLEADING

**With this approach:**
- All metrics reflect the true state of the stock on the reference date
- No look-ahead bias - we only see what would have been visible then
- Accurate backtesting - we're testing what we would have known, not what we know now

