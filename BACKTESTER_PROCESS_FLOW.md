# Backtester Process Flow - Simplified View

## Your Understanding is Correct! ✅

Yes, here's exactly what happens:

---

## Step 1: Pull the Universe

```python
all_tickers = ticker_universe.get_ticker_symbols()
```

**What this does:**
- Loads list of all tickers from `data/us_stock_universe.csv`
- Typically ~11,802 tickers
- Optional: Filters by sector if specified (e.g., "tech", "finance")

**Result:** List of ticker symbols to process
- Example: `['AAPL', 'MSFT', 'GOOGL', 'AMZN', ...]`

---

## Step 2: Check Prices for Reference Date

For **each ticker** in the universe:

```python
stock_data = get_historical_stock_data(ticker, reference_date, lookback_days=180)
```

**What this does:**
- Fetches price data **up to** the reference_date (no future data!)
- Calculates all metrics using that historical data:
  - Current price (price on reference_date)
  - 1M/3M/6M performance (using prices relative to reference_date)
  - ADR% (last 30 days up to reference_date)
  - RSI, MACD, Stochastic, ATR (calculated using data up to reference_date)

**Result:** Dictionary with all calculated metrics for that ticker as they would have appeared on the reference_date

---

## Step 3: Apply Strategy Filter Logic

After getting the stock data, filters are applied:

```python
# Price filters
if min_price and stock_data['current_price'] < min_price:
    return None  # Filtered out
    
if max_price and stock_data['current_price'] > max_price:
    return None  # Filtered out

# ADR filters
if min_adr and stock_data['adr_percentage'] < min_adr:
    return None  # Filtered out
    
if max_adr and stock_data['adr_percentage'] > max_adr:
    return None  # Filtered out

# Performance filters (matching regular scanner)
if min_1m_performance and stock_data['performance_1m'] < min_1m_performance:
    return None  # Filtered out
    
if min_3m_performance and stock_data['performance_3m'] < min_3m_performance:
    return None  # Filtered out
    
if min_6m_performance and stock_data['performance_6m'] < min_6m_performance:
    return None  # Filtered out
    
# ... and max filters too
```

**Result:** Only stocks that pass ALL filters are kept

---

## Step 4: Sort & Rank

After filtering, stocks are sorted by the specified criteria (default: ADR descending):

```python
results.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)
final_results = results[:top_n]  # Take top N
```

**Result:** Top N stocks ranked by the strategy criteria

---

## Complete Flow Diagram

```
┌─────────────────────────────────────┐
│ 1. Pull Universe                    │
│    all_tickers = [...11,802...]    │
│    (Optional: Filter by sector)     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 2. For Each Ticker in Universe      │
│                                     │
│    a) Fetch prices up to            │
│       reference_date                │
│                                     │
│    b) Calculate metrics:            │
│       • Price on reference_date     │
│       • 1M/3M/6M performance        │
│       • ADR%, RSI, MACD, etc.       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 3. Apply Strategy Filters           │
│                                     │
│    Check:                           │
│    ✓ Price range                   │
│    ✓ ADR range                     │
│    ✓ 1M performance                │
│    ✓ 3M performance                │
│    ✓ 6M performance                │
│                                     │
│    If ALL pass → Keep              │
│    If ANY fail → Filter out        │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 4. Sort & Rank                      │
│                                     │
│    Sort by ADR (or other field)    │
│    Take top N results               │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ Result: Top N Stocks                │
│ Ranked by Strategy Criteria         │
└─────────────────────────────────────┘
```

---

## Example Walkthrough

**Input:**
- Universe: 11,802 tickers
- Reference Date: 2024-09-01
- Filters: 
  - min_1m_performance: 10%
  - min_3m_performance: 20%
  - min_6m_performance: 30%
  - min_adr: 2%
- Sort: ADR descending
- Top N: 50

**Process:**

1. **Pull Universe:** Get 11,802 tickers

2. **Check Prices for 2024-09-01:**
   - For `AAPL`: Fetch prices up to 2024-09-01, calculate metrics
   - For `MSFT`: Fetch prices up to 2024-09-01, calculate metrics
   - For `GOOGL`: Fetch prices up to 2024-09-01, calculate metrics
   - ... (repeat for all 11,802 tickers)

3. **Apply Filters:**
   - `AAPL`: 
     - Price on 2024-09-01: $178.50
     - 1M%: 3.78% ❌ (fails min_1m_performance: 10%)
     - **Result:** Filtered out
   
   - `MSFT`:
     - Price on 2024-09-01: $450.00
     - 1M%: 12.5% ✓
     - 3M%: 25.0% ✓
     - 6M%: 35.0% ✓
     - ADR: 2.5% ✓
     - **Result:** Kept
   
   - ... (check all 11,802 tickers)

4. **Sort & Rank:**
   - Take all stocks that passed filters
   - Sort by ADR descending
   - Take top 50

**Final Result:** 50 stocks ranked by ADR, all meeting your strategy criteria, as they would have appeared on 2024-09-01

---

## Key Points

✅ **Universe First**: Start with full ticker list  
✅ **Check Prices**: Get historical prices/metrics for reference_date  
✅ **Apply Filters**: Use your strategy criteria to filter  
✅ **Rank Results**: Sort by your ranking criteria (ADR, etc.)  

This matches exactly how your regular scanner works, but using historical data instead of current data!

