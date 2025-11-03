# Stock Screener Usage Guide

## 🎯 Overview
With your **Polygon Stocks Starter plan** ($29/month), you have **unlimited API calls** to screen stocks across the entire US market.

## 📊 Screening Modes

### 1. **Quick Sample Scan** (Default - Recommended)
- Screens **3,000 stocks** (stratified A-Z sample)
- **Time:** ~5-10 minutes (first run), ~1-2 seconds (cached)
- **Coverage:** Full A-Z alphabet, all exchanges
- **Use for:** Quick screening, development, testing

```bash
# Quick scan with 3,000 stocks
curl "http://localhost:8000/midas/asset/stock_screener?sector=all&limit=10"

# Custom sample size (e.g., 5,000 stocks)
curl "http://localhost:8000/midas/asset/stock_screener?sector=all&sample_size=5000&limit=10"
```

### 2. **Full Universe Scan**
- Screens **ALL 11,802 stocks**
- **Time:** ~30-60 minutes (first run), ~1-2 seconds (cached)
- **Coverage:** Complete US stock market
- **Use for:** Comprehensive analysis, finding hidden gems

```bash
# Full scan of all 11,802 stocks
curl "http://localhost:8000/midas/asset/stock_screener?sector=all&use_full_universe=true&limit=10"
```

### 3. **Sector-Specific Scan**
- Screens **20-30 predefined stocks** per sector
- **Time:** ~30-60 seconds
- **Sectors:** tech, bio, finance, energy
- **Use for:** Focused sector analysis

```bash
# Tech sector only
curl "http://localhost:8000/midas/asset/stock_screener?sector=tech&limit=10"
```

## 🔍 Filter Parameters

### Performance Filters
- `min_1m_performance` - Minimum 1-month performance (%)
- `min_3m_performance` - Minimum 3-month performance (%)
- `min_6m_performance` - Minimum 6-month performance (%)

### Price Filters
- `min_price` - Minimum stock price ($)
- `max_price` - Maximum stock price ($)

### RSI Filters
- `min_rsi` - Minimum RSI value (0-100)
- `max_rsi` - Maximum RSI value (0-100)
- `rsi_signal` - Filter by signal: "all", "oversold", "overbought", "neutral"

### Universe Options
- `use_full_universe` - Scan all 11,802 stocks (true/false)
- `sample_size` - Number of stocks to sample (default: 3000)
- `limit` - Max results to return (default: 50)

## 📝 Example API Calls

### Find High-Growth Stocks
```bash
curl "http://localhost:8000/midas/asset/stock_screener?\
sector=all&\
min_1m_performance=10&\
min_3m_performance=20&\
min_6m_performance=30&\
min_price=1&\
max_price=50&\
sample_size=5000&\
limit=20"
```

### Find Oversold Bargains
```bash
curl "http://localhost:8000/midas/asset/stock_screener?\
sector=all&\
rsi_signal=oversold&\
min_price=5&\
max_price=100&\
sample_size=3000&\
limit=20"
```

### Full Universe Tech Scan
```bash
curl "http://localhost:8000/midas/asset/stock_screener?\
sector=tech&\
use_full_universe=true&\
min_1m_performance=5&\
limit=50"
```

## 💾 Caching System

### How It Works
- **First scan:** Fetches data from Polygon API, saves to cache
- **Subsequent scans:** Loads from cache (instant)
- **Cache duration:** 1 hour (configurable)
- **Storage:** `cache/stock_screener_cache.json`

### Cache Benefits
- ⚡ **Fast:** Cached results return in 1-2 seconds
- 💰 **Efficient:** Reduces API calls even with unlimited plan
- 🔄 **Smart:** Only fetches missing/expired data

### Cache Management
The cache automatically:
- Expires after 1 hour
- Merges new data with existing cache
- Handles partial updates (only fetches missing stocks)

## 📊 Response Format

Each stock in the results includes:
```json
{
  "ticker": "AAPL",
  "current_price": 150.25,
  "performance_1m": 5.2,
  "performance_3m": 12.8,
  "performance_6m": 25.4,
  "adr_percentage": 2.1,
  "rsi": 65.4,
  "rsi_signal": "NEUTRAL",
  "macd": 1.2,
  "macd_signal": 0.8,
  "stochastic_oscillator": 72.3,
  "atr": 3.2,
  "indicator_scores": {
    "MACD": 1,
    "RSI": 0,
    "SO": -1,
    "PRC": 1
  },
  "overall_signal": "BULLISH",
  "overall_score": 0.6,
  "volume_avg_30d": 50234567,
  "last_updated": "2025-10-02T20:15:30.123456"
}
```

## 🚀 Recommendations

### For Development
- Use **sample scan** (3,000-5,000 stocks)
- Fast iteration and testing
- Good A-Z coverage

### For Production
- Use **full universe scan** overnight
- Cache results for the day
- Refresh cache daily or on-demand

### For Quick Checks
- Use **sector-specific** scans
- Fastest results
- Focused analysis

## ⚡ Performance Tips

1. **First run:** Let it complete to build the cache
2. **Subsequent runs:** Almost instant from cache
3. **Full scans:** Run during off-hours or overnight
4. **Sample size:** Adjust based on your needs (1000-5000 optimal)

## 🔗 Related Endpoints

- `/midas/asset/universe_stats` - Get universe statistics
- `/midas/asset/screener_info` - Get screener capabilities
- `/midas/asset/available_sectors` - List available sectors
- `/midas/asset/sector_summary/{sector}` - Get sector summary

## 💡 Pro Tips

1. **Start with samples** to test filters, then run full scan
2. **Use caching** - first run is slow, subsequent runs are fast
3. **Adjust sample_size** based on your time constraints
4. **Full scans** are great for overnight batch jobs
5. **Monitor progress** in the backend logs

