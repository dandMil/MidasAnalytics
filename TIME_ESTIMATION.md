# Time Estimation for Full Universe ADR Ranking

## Overview
This document estimates the time required to process the entire US stock universe (11,802 tickers) to rank all stocks by Average Daily Range (ADR) percentage.

## Key Metrics

- **Total Tickers**: 11,802 stocks
- **API Endpoint**: `GET /v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}`
- **Data Required**: 180 days of historical price data per ticker
- **Current Cache Duration**: 8 hours
- **Current Rate Limiting**: 0.1s pause every 50 requests

## Time Estimation

### Base Scenario (Average API Response Time: 0.3s)

| Component | Time |
|-----------|------|
| API Calls (11,802 × 0.3s) | 59.0 minutes |
| Rate Limit Pauses (236 pauses × 0.1s) | 23.6 seconds |
| **Total Time** | **~60 minutes (~1 hour)** |

### Scenario Variations

| Scenario | API Response Time | Total Time |
|----------|-------------------|------------|
| **Optimistic** | 0.2s per call | ~40 minutes (0.66 hours) |
| **Average** | 0.3s per call | ~60 minutes (0.99 hours) |
| **Pessimistic** | 0.5s per call | ~99 minutes (1.65 hours) |

### Without Rate Limiting

If rate limiting is removed:
- **Time**: ~59 minutes (0.98 hours)
- **Trade-off**: May hit API rate limits or get throttled

## Processing Breakdown

### Per Ticker Processing:
1. **API Call**: Fetch 180 days of price history (~0.3s)
2. **Data Processing**:
   - Convert to DataFrame
   - Calculate ADR% (Average Daily Range %)
   - Calculate performance metrics (1M, 3M, 6M)
   - Calculate technical indicators (RSI, MACD, Stochastic, ATR)
3. **Storage**: Save to cache (~instant)

### Total Processing Steps:
- 11,802 API calls
- 11,802 data processing operations
- 236 rate limit pauses

## Cache Impact

### First Run (Cold Cache)
- **Time**: Full ~60 minutes
- **Cache Hits**: 0%
- **API Calls**: 11,802

### Subsequent Runs (Warm Cache)
- **Time**: ~0-5 seconds (just sorting cached data)
- **Cache Hits**: 100% (if within 8-hour window)
- **API Calls**: 0

### Progressive Cache Building
- **First 1,000 tickers**: ~5 minutes
- **First 5,000 tickers**: ~25 minutes
- **Full universe**: ~60 minutes
- After completion, all future requests are instant (within cache window)

## Recommendations

### Option 1: Full Universe Scan (Recommended)
```python
# In your API call or script
filters = {
    "use_full_universe": True,
    "sector": "all",
    # No filters - process everything
    "limit": 11802  # or don't set limit
}
```

**Time**: ~60 minutes (first run only)
**Benefits**: 
- Complete market coverage
- Instant subsequent runs (cached)
- Can filter/sort by ADR after processing

### Option 2: Batch Processing
Process universe in batches over time:
- **Batch 1**: 3,000 tickers (~15 min)
- **Batch 2**: 3,000 tickers (~15 min)
- **Batch 3**: 3,000 tickers (~15 min)
- **Batch 4**: 2,802 tickers (~14 min)

**Time**: Same total, but spread out
**Benefits**: Lower impact during development/testing

### Option 3: Use Market Snapshot API
Instead of individual API calls, use the new market snapshot endpoint:
- **Single API call** for all tickers
- **Time**: ~1-2 seconds
- **Limitation**: Only provides current day data, no historical ADR calculation

**Note**: This won't give you ADR ranking (needs historical data), but could be used for other metrics.

## Current Implementation

The current screener service:
1. ✅ Supports full universe scanning (`use_full_universe=True`)
2. ✅ Has 8-hour cache (recently updated from 1 hour)
3. ✅ Calculates ADR% for all processed tickers
4. ✅ Sorts by ADR% (highest first)
5. ✅ Includes rate limiting protection

## API Usage

### API Calls Required:
- **Per Full Scan**: 11,802 calls
- **Daily** (with 8-hour cache): ~3 scans max = 35,406 calls/day
- **Monthly** (typical usage): ~90 scans = 1,062,180 calls/month

### Polygon.io Rate Limits:
- **Free Tier**: 5 calls/minute
- **Starter Tier**: 5 calls/minute  
- **Developer Tier**: 15 calls/minute
- **Advanced Tier**: 200 calls/minute
- **Professional Tier**: Unlimited

**Note**: At 0.3s per call (~200 calls/minute), you need at least Advanced tier for efficient processing.

## Optimization Opportunities

1. **Parallel Processing**: Use async/concurrent requests
   - Could reduce time to ~10-20 minutes
   - Requires rate limit awareness

2. **Batch API Calls**: If Polygon supports batch endpoints
   - Could reduce to single or few API calls
   - Check Polygon API documentation

3. **Incremental Updates**: Only fetch updates for changed tickers
   - Daily updates: Only new/changed tickers
   - Much faster after initial load

4. **Database Storage**: Store results in database instead of JSON
   - Faster queries and sorting
   - Better for large datasets

## Conclusion

**Estimated Time**: **~60 minutes** (1 hour) to process the entire universe for ADR ranking.

**Key Points**:
- ✅ One-time cost (cached for 8 hours)
- ✅ Subsequent requests are instant
- ✅ Can run overnight or during off-peak hours
- ✅ Results can be sorted/filtered after processing

**Recommended Approach**:
1. Run full universe scan once (or schedule overnight)
2. Use cached results for all subsequent requests
3. Re-scan every 8 hours (or as needed)

