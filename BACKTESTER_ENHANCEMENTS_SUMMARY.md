# Backtester Enhancements Summary

## Overview

The backtester has been enhanced with two major features:
1. **SIC-Based Sector Support** - Backtester now supports SIC-based sectors (like the screener)
2. **Time Range Backtesting** - New endpoint for running backtests across multiple dates

## Workflow

The backtester follows a clear two-step workflow:

**Step 1: Select Sector** → **Step 2: Select Time Range**

1. **First**, choose which sector to analyze (required)
2. **Then**, choose the time range for analysis (required)
3. Optionally configure filters and optimization parameters

This workflow ensures you know what you're analyzing before deciding when to analyze it.

---

## 1. SIC-Based Sector Support

### What Changed

The backtester now supports the same sector options as the screener:
- **Universe**: Full ticker universe (~11,802 stocks)
- **All**: All predefined sectors combined
- **Predefined Sectors**: `tech`, `energy`, `bio`, `finance` - These now automatically use SIC-based data when available
- **SIC-Based Sectors**: `tech_sic`, `energy_sic`, `healthcare_sic` - Direct access to SIC-based sectors

### How It Works

When you select a predefined sector (e.g., `sector="tech"`):
1. The system checks if a SIC-based CSV exists for that sector
2. If found, it loads all tickers from the SIC CSV (e.g., 563 tech tickers from `tech_tickers_by_sic.csv`)
3. If not found, it falls back to the predefined sector list (e.g., 30 tech stocks)

### Example Usage

**Single Date Backtest with Tech Sector:**
```bash
GET /midas/backtest/historical_rankings?reference_date=2024-01-15&sector=tech&top_n=50
```

This will:
- Use SIC-based tech sector (563 stocks) if CSV exists
- Fall back to predefined tech (30 stocks) if CSV doesn't exist
- Return top 50 ranked stocks as of 2024-01-15

**Direct SIC Sector Access:**
```bash
GET /midas/backtest/historical_rankings?reference_date=2024-01-15&sector=tech_sic&top_n=50
```

**Universe:**
```bash
GET /midas/backtest/historical_rankings?reference_date=2024-01-15&sector=universe&top_n=50
```

---

## 2. Time Range Backtesting

### New Endpoint: `/midas/backtest/historical_rankings_range`

This endpoint allows you to run backtests for multiple dates within a specified range.

### Workflow

**Step 1: Select Sector** (Required)
- Choose which sector to analyze: `universe`, `all`, predefined sectors, or SIC-based sectors

**Step 2: Select Time Range** (Required)
- Choose `start_date` and `end_date` for the analysis period
- Choose `date_interval`: `daily`, `weekly`, or `monthly`

**Step 3: Configure Options** (Optional)
- Set filters, optimization parameters, etc.

### Parameters

**Required:**
- `sector`: Sector to analyze (must be selected first)
- `start_date`: Start date in YYYY-MM-DD format
- `end_date`: End date in YYYY-MM-DD format

**Optional:**
- `date_interval`: Interval between dates - `"daily"`, `"weekly"`, or `"monthly"` (default: `"weekly"`)
- `top_n`: Number of top stocks per date (default: 50)
- All standard filters: `min_price`, `max_price`, `min_adr`, `max_adr`, performance filters, etc.
- Optimization parameters: `use_sample`, `sample_size`, `max_workers`, etc.

### Example Usage

**Step 1: Select Tech Sector, Step 2: Weekly Backtest for 3 Months:**
```bash
GET /midas/backtest/historical_rankings_range?sector=tech&start_date=2024-01-01&end_date=2024-03-31&date_interval=weekly&top_n=50
```

This will:
1. Use tech sector (SIC-based if available, 563 stocks)
2. Generate dates: 2024-01-01, 2024-01-08, 2024-01-15, ... 2024-03-31
3. Run backtest for each date
4. Return rankings for each date

**Step 1: Select Tech SIC Sector, Step 2: Daily Backtest for 1 Week:**
```bash
GET /midas/backtest/historical_rankings_range?sector=tech_sic&start_date=2024-01-01&end_date=2024-01-07&date_interval=daily&top_n=20
```

**Step 1: Select Universe, Step 2: Monthly Backtest for 1 Year:**
```bash
GET /midas/backtest/historical_rankings_range?sector=universe&start_date=2023-01-01&end_date=2023-12-31&date_interval=monthly&top_n=100
```

### Response Format

```json
{
  "start_date": "2024-01-01",
  "end_date": "2024-03-31",
  "date_interval": "weekly",
  "total_dates": 13,
  "successful_dates": 13,
  "failed_dates": 0,
  "results": [
    {
      "reference_date": "2024-01-01",
      "rankings": [...],
      "session_id": "session_123",
      "count": 50
    },
    {
      "reference_date": "2024-01-08",
      "rankings": [...],
      "session_id": "session_124",
      "count": 50
    },
    ...
  ]
}
```

### Features

1. **Caching**: Uses existing session cache - if a date was already processed, it returns cached results
2. **Error Handling**: If one date fails, others continue processing
3. **Progress Logging**: Logs progress for each date being processed
4. **Flexible Intervals**: Daily, weekly, or monthly intervals

---

## Updated Endpoints

### 1. `/midas/backtest/historical_rankings` (Updated)

**Changes:**
- Updated `sector` parameter description to include SIC-based sectors
- Now supports all sector types: `universe`, `all`, predefined sectors, SIC-based sectors

**Sector Parameter:**
```
sector: Optional sector filter. Supports: 'universe', 'all', predefined sectors ('tech', 'energy', 'bio', 'finance'), or SIC-based sectors ('tech_sic', 'energy_sic', 'healthcare_sic'). Predefined sectors automatically use SIC-based data when available.
```

### 2. `/midas/backtest/historical_rankings_range` (New)

**Purpose:** Run backtests for multiple dates in a range

**Key Features:**
- Date range validation
- Flexible date intervals (daily, weekly, monthly)
- Reuses existing caching mechanism
- Error handling per date
- Returns aggregated results

---

## Implementation Details

### Files Modified

1. **`services/historical_screener_service.py`**
   - Added imports: `SIC_SECTOR_MAPPING`, `PREDEFINED_TO_SIC_MAPPING`, `load_tickers_from_sic_csv`
   - Updated sector filtering logic to support SIC-based sectors
   - Predefined sectors (`tech`, `energy`, `bio`) now automatically use SIC-based data when available

2. **`app.py`**
   - Updated `/midas/backtest/historical_rankings` endpoint description
   - Added new `/midas/backtest/historical_rankings_range` endpoint
   - Added `timedelta` import

### Sector Resolution Logic

```
sector = "tech"
  ↓
Check PREDEFINED_TO_SIC_MAPPING
  ↓
Found: "tech" → "tech_sic"
  ↓
Load from tech_tickers_by_sic.csv
  ↓
If CSV exists: Use 563 tech tickers
If CSV missing: Fall back to predefined 30 tech tickers
```

---

## Usage Examples

### Example 1: Single Date with Tech Sector

```bash
curl "http://localhost:8000/midas/backtest/historical_rankings?reference_date=2024-01-15&sector=tech&top_n=50"
```

**Result:** Top 50 tech stocks (from SIC-based tech sector) as of 2024-01-15

### Example 2: Weekly Backtest for Tech Sector

```bash
curl "http://localhost:8000/midas/backtest/historical_rankings_range?sector=tech&start_date=2024-01-01&end_date=2024-01-31&date_interval=weekly&top_n=50"
```

**Result:** Rankings for 5 dates (weekly intervals) in January 2024

### Example 3: Monthly Backtest for Universe

```bash
curl "http://localhost:8000/midas/backtest/historical_rankings_range?sector=universe&start_date=2023-01-01&end_date=2023-12-31&date_interval=monthly&top_n=100&use_sample=true&sample_size=3000"
```

**Result:** Monthly rankings for entire 2023, using sampled universe (3000 stocks per date)

---

## Benefits

1. **Comprehensive Sector Coverage**: SIC-based sectors include all companies in that sector, not just a predefined list
2. **Time Series Analysis**: Time range backtesting enables analysis of strategy performance over time
3. **Efficient Caching**: Reuses existing session cache for faster subsequent runs
4. **Consistent API**: Same sector options as screener for consistency
5. **Flexible Analysis**: Daily, weekly, or monthly intervals for different analysis needs

---

## Notes

- **Performance**: Time range backtesting can take significant time for large date ranges. Use `use_sample=true` for faster results during development.
- **Caching**: Results are cached per date, so subsequent runs are much faster.
- **Error Handling**: If one date fails, others continue processing. Check `failed_dates` in response.
- **Date Validation**: Dates cannot be in the future. `start_date` must be ≤ `end_date`.

---

## Next Steps

1. Test with various sectors and date ranges
2. Integrate with frontend for time range selection UI
3. Add visualization for time series backtest results
4. Consider adding batch trade simulation for time range results
