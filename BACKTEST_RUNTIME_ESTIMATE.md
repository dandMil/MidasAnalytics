# Backtest Runtime Estimate: 5 Stocks, 3 Months Back

## Scenario
- **5 stocks** to simulate trades on
- **3 months** lookback period for historical rankings

## Runtime Breakdown

### Step 1: Historical Rankings (Initial Step)
**This is the bottleneck**

**What happens:**
- Processes **entire ticker universe** (typically 3,000-10,000+ stocks)
- Makes 1 API call per ticker to Polygon.io to get 90 days of historical data
- Calculates ADR, RSI, performance metrics for each
- Ranks and returns top N results

**Time estimate:**
- **API Rate Limits:** Polygon.io free tier: ~5 calls/minute
- **Universe Size:** Assume ~5,000 stocks (typical US stock universe)
- **API Calls Needed:** 5,000 calls
- **Time per Call:** ~0.5 seconds (network + processing)
- **Rate Limiting:** 5 calls/minute = 12 seconds per 5 stocks

**Worst Case (Full Universe, No Caching):**
- 5,000 stocks ÷ 5 calls/minute = **1,000 minutes = ~16.7 hours** ⚠️

**Realistic Case (Free Tier Rate Limit):**
- **Estimated: 2-3 hours** for full universe processing
- Polygon may allow bursts, so could be faster: **30-60 minutes** with good network

**Best Case (Cached or Premium API):**
- If data is cached or you have premium API (higher rate limits): **5-15 minutes**

### Step 2: Trade Simulation (5 Stocks)
**Much faster - this is what you're asking about**

**What happens:**
- Takes 5 selected stocks from historical rankings
- Makes 1 API call per stock to get forward price data (from entry date forward)
- Simulates each trade day-by-day checking stop loss/take profit

**Time estimate:**
- **API Calls:** 5 calls (one per stock)
- **Data Range:** ~90 days forward (default max hold)
- **Time per Call:** ~0.5 seconds
- **No Rate Limiting Issues:** Only 5 calls

**Total Time:**
- **~3-5 seconds** for all 5 trade simulations ⚡

## Total Runtime Breakdown

### First Run (No Cache):
```
Historical Rankings:  30-60 minutes (realistic)
                      2-3 hours (worst case)
Trade Simulation:     3-5 seconds
────────────────────────────────────────
TOTAL:                ~30-60 minutes to ~3 hours
```

### Subsequent Runs (Same Date):
```
Historical Rankings:  30-60 minutes (still needs to process)
                      (Note: Historical rankings can't be cached the same way 
                       because each date requires fresh calculations)
Trade Simulation:     3-5 seconds
────────────────────────────────────────
TOTAL:                ~30-60 minutes
```

## Optimization Opportunities

### 1. **Reduce Universe Size** (Biggest Impact)
- Filter by sector, exchange, or market cap before processing
- Example: Only process tech stocks (~500-1000 stocks)
- **Impact:** Reduces time from 60 min → **6-12 minutes**

### 2. **Use Sampling** (Quick Results)
- Process every 10th stock (10% sample)
- **Impact:** Reduces time from 60 min → **6 minutes**
- Trade-off: May miss some top performers

### 3. **Parallel Processing** (Implementation Required)
- Process multiple tickers in parallel (respecting rate limits)
- **Impact:** Could reduce time by 2-3x

### 4. **Premium Polygon API**
- Higher rate limits (up to 200 calls/minute)
- **Impact:** Reduces time from 60 min → **2-5 minutes**

## Recommended Approach for 5 Stocks

### Option A: Quick Test (Recommended for Development)
1. **Limit Universe:** Filter to specific sector (e.g., tech only)
2. **Result:** ~500-1000 stocks to process
3. **Time:** **6-12 minutes** for rankings + **3-5 seconds** for simulations
4. **Total:** **~10-15 minutes**

### Option B: Full Analysis
1. **Full Universe:** Process all stocks
2. **Time:** **30-60 minutes** for rankings + **3-5 seconds** for simulations  
3. **Total:** **~30-60 minutes**
4. **Best for:** Production runs when you need accurate rankings

### Option C: Optimized (Best Performance)
1. **Use existing screener cache** (if available)
2. **Sample top performers** from cache
3. **Time:** **1-2 minutes** (if cache exists)
4. **Total:** **~2 minutes**

## Answer to Your Question

**For simulating 5 trades with 3 months lookback:**

- **Historical Rankings Step:** 30-60 minutes (if full universe)
- **5 Trade Simulations:** ~3-5 seconds

**Total: ~30-60 minutes** for the complete backtest

**If you already have historical rankings:**
- **Just the 5 simulations:** ~3-5 seconds ⚡

## Recommendations

1. **For Quick Testing:** Use sector filtering or sampling
2. **For Production:** Allow time for full universe processing
3. **For Repeated Testing:** Consider caching mechanisms or reducing universe size
4. **Best Practice:** Process rankings once per date, then simulate multiple trades on those rankings

