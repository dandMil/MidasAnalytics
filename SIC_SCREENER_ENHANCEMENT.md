# SIC-Based Screener Enhancement

## Overview

Enhanced the stock screener to support SIC (Standard Industrial Classification) code-based sector filtering. When a SIC sector is selected, the screener loads tickers from the appropriate CSV file and processes them using the same history checking logic as the universal pull.

## Changes Made

### 1. Backend Enhancements (`services/stock_screener_service.py`)

#### Added SIC Sector Mapping
```python
SIC_SECTOR_MAPPING = {
    "tech_sic": {
        "csv_file": "data/sic_tickers/tech_tickers_by_sic.csv",
        "display_name": "Technology/AI",
        "fallback": "tech"
    },
    "energy_sic": {
        "csv_file": "data/sic_tickers/energy_tickers_by_sic.csv",
        "display_name": "Energy",
        "fallback": "energy"
    },
    "healthcare_sic": {
        "csv_file": "data/sic_tickers/healthcare_tickers_by_sic.csv",
        "display_name": "Healthcare/Biotech",
        "fallback": "bio"
    }
}
```

#### New Function: `load_tickers_from_sic_csv()`
- Loads ticker symbols from SIC-based CSV files
- Returns list of ticker symbols
- Handles missing files gracefully
- Logs warnings if CSV not found

#### Updated Sector Handling Logic
- **SIC Sectors**: When `tech_sic`, `energy_sic`, or `healthcare_sic` is selected:
  1. Loads tickers from the corresponding CSV file
  2. Falls back to predefined sector if CSV not available
  3. Uses same history checking logic as universal pull
  
- **Existing Sectors**: Continue to work as before
- **All Sectors**: Still uses full universe

#### Updated `get_available_sectors()`
- Now includes SIC-based sectors
- Returns human-readable names for frontend
- Shows ticker counts from CSV files
- Indicates if SIC CSV is available

### 2. API Endpoint Updates (`app.py`)

#### Updated `/midas/asset/stock_screener`
- Now accepts SIC-based sector values:
  - `tech_sic` - Technology/AI (SIC-based)
  - `energy_sic` - Energy (SIC-based)
  - `healthcare_sic` - Healthcare/Biotech (SIC-based)
- Maintains backward compatibility with existing sectors

#### Updated `/midas/asset/available_sectors`
- Returns both predefined and SIC-based sectors
- Includes human-readable names
- Shows availability status for SIC sectors

#### Updated `/midas/asset/screener_info`
- Uses `get_available_sectors()` to include SIC sectors

## How It Works

### Data Flow

```
Frontend Request
    ↓
sector="tech_sic" (or "energy_sic", "healthcare_sic")
    ↓
Backend: screen_stocks()
    ├─→ Check if sector in SIC_SECTOR_MAPPING
    ├─→ Load tickers from CSV: data/sic_tickers/{sector}_tickers_by_sic.csv
    ├─→ If CSV not found: Fallback to predefined sector
    └─→ Process tickers (same as universal pull)
        ├─→ Check cache for each ticker
        ├─→ Fetch history if not cached
        ├─→ Calculate metrics (ADR, RSI, performance, etc.)
        ├─→ Apply filters
        └─→ Sort and return results
    ↓
Return Results (with human-readable sector name)
```

### History Checking

**Same Logic for All Sectors:**
1. Check cache first (48-hour cache duration)
2. If cached and valid: Use cached data
3. If not cached or expired: Fetch from Polygon API
4. Calculate all metrics (1M/3M/6M performance, ADR, RSI, etc.)
5. Apply filters
6. Return results

**No Changes to History Logic:**
- SIC-based tickers use the exact same history checking as universal pull
- Same cache mechanism
- Same API calls
- Same metric calculations

## Frontend Integration

### Sector Selection

The frontend should display human-readable names:

| Backend Value | Frontend Display |
|--------------|------------------|
| `tech_sic` | "Technology/AI" |
| `energy_sic` | "Energy" |
| `healthcare_sic` | "Healthcare/Biotech" |
| `tech` | "Tech" (predefined) |
| `energy` | "Energy" (predefined) |
| `bio` | "Bio" (predefined) |

### API Response

The `/midas/asset/available_sectors` endpoint now returns:

```json
{
  "tech_sic": {
    "name": "Technology/AI",
    "ticker_count": 2345,
    "tickers": ["AAPL", "MSFT", "NVDA", ...],
    "type": "sic_based",
    "available": true,
    "csv_file": "data/sic_tickers/tech_tickers_by_sic.csv"
  },
  "energy_sic": {
    "name": "Energy",
    "ticker_count": 567,
    "tickers": ["XOM", "CVX", "SLB", ...],
    "type": "sic_based",
    "available": true,
    "csv_file": "data/sic_tickers/energy_tickers_by_sic.csv"
  },
  "healthcare_sic": {
    "name": "Healthcare/Biotech",
    "ticker_count": 1234,
    "tickers": ["PFE", "JNJ", "ISRG", ...],
    "type": "sic_based",
    "available": true,
    "csv_file": "data/sic_tickers/healthcare_tickers_by_sic.csv"
  },
  "tech": {
    "name": "Tech",
    "ticker_count": 30,
    "tickers": ["AAPL", "MSFT", ...],
    "type": "predefined"
  },
  ...
}
```

### Frontend Implementation

1. **Fetch Available Sectors:**
   ```typescript
   const sectors = await fetch('/midas/asset/available_sectors');
   ```

2. **Display Human-Readable Names:**
   ```typescript
   sectors.forEach(sector => {
     displayName = sector.name;  // "Technology/AI" instead of "tech_sic"
   });
   ```

3. **Send Backend Value:**
   ```typescript
   // When user selects "Technology/AI", send "tech_sic" to backend
   fetch(`/midas/asset/stock_screener?sector=tech_sic&...`);
   ```

## Usage Examples

### API Calls

**SIC-Based Technology Sector:**
```bash
GET /midas/asset/stock_screener?sector=tech_sic&limit=50&min_adr=3
```

**SIC-Based Energy Sector:**
```bash
GET /midas/asset/stock_screener?sector=energy_sic&limit=50&min_adr=3
```

**SIC-Based Healthcare Sector:**
```bash
GET /midas/asset/stock_screener?sector=healthcare_sic&limit=50&min_adr=3
```

### Expected Behavior

1. **If SIC CSV exists:**
   - Loads tickers from CSV file
   - Processes using same history checking as universal pull
   - Returns results filtered by SIC codes

2. **If SIC CSV missing:**
   - Falls back to predefined sector
   - Logs warning message
   - Still processes normally

3. **History Checking:**
   - Uses same cache mechanism
   - Same API calls to Polygon
   - Same metric calculations
   - No difference from universal pull

## Benefits

1. **More Accurate Sector Filtering**: Uses actual SIC codes instead of predefined lists
2. **Comprehensive Coverage**: Includes all stocks matching SIC codes, not just major ones
3. **Same Performance**: Uses same caching and history checking as existing screener
4. **Backward Compatible**: Existing sectors still work
5. **Human-Readable**: Frontend shows friendly names

## File Structure

```
data/
  └── sic_tickers/
      ├── tech_tickers_by_sic.csv
      ├── energy_tickers_by_sic.csv
      └── healthcare_tickers_by_sic.csv
```

Each CSV contains:
- `ticker` - Stock symbol
- `name` - Company name
- `sic_code` - SIC code
- `primary_exchange` - Exchange
- `type` - Security type
- `cik` - SEC CIK number

## Next Steps

1. **Run SIC Ticker Script**: Generate CSV files first
   ```bash
   python3 scripts/get_tickers_by_sic_simple.py
   ```

2. **Update Frontend**: 
   - Fetch available sectors
   - Display human-readable names
   - Send correct backend values

3. **Test**: 
   - Verify SIC sectors load correctly
   - Confirm history checking works
   - Test fallback behavior

## Notes

- SIC CSV files are generated by running the SIC ticker scripts
- If CSV files don't exist, screener falls back to predefined sectors
- History checking logic is unchanged - works identically for all sectors
- Cache mechanism works the same for SIC-based tickers
