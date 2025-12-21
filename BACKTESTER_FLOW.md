# Backtester Flow Explanation

## Overview

The backtester implements an "interactive time-travel" approach where you can:
1. See how stocks were ranked at a historical date (using only data available up to that date)
2. Select stocks from those rankings
3. Simulate trades forward from that historical date
4. See what the profit/loss would have been

This avoids **look-ahead bias** by ensuring all calculations use only data that would have been available at the reference date.

---

## Complete Flow

### Phase 1: Fetch Historical Rankings

#### 1.1 Frontend Initiation (`BacktestingView.tsx`)
- User selects a **reference date** (e.g., 90 days ago)
- User clicks "Fetch Historical Rankings"
- Frontend calls `getHistoricalRankings()` API function

#### 1.2 API Request (`api.tsx` → `app.py`)
- **Endpoint**: `GET /midas/backtest/historical_rankings`
- **Parameters**:
  - `reference_date`: Historical date (YYYY-MM-DD)
  - `top_n`: Number of top stocks to return (default: 50)
  - Filters: `sector`, `min_price`, `max_price`, `min_adr`, `max_adr`
  - Performance filters: `min_1m_performance`, `min_3m_performance`, `min_6m_performance`
  - Sorting: `sort_by` (default: 'adr'), `sort_order` (default: 'desc')
  - Optimization: `use_sample`, `max_workers`, `rate_limit_per_minute`

#### 1.3 Backend: Session Check (`app.py`)
- Checks if a session already exists for this `reference_date` + `filters`
- If found: Returns cached rankings immediately ✅
- If not found: Proceeds to generate new rankings

#### 1.4 Historical Rankings Generation (`historical_screener_service.py`)

**Step 1: Early Session Creation**
- Creates a session **immediately** (before processing starts)
- Session has empty rankings initially
- This ensures session exists even if request times out
- Session saved to: `cache/backtest_sessions/{session_id}.json`

**Step 2: Get Ticker Universe**
- Loads ticker list from `data/us_stock_universe.csv`
- Applies sector filter if specified
- Optionally samples if `use_sample=True`

**Step 3: Parallel Processing (Multi-Worker)**
- Uses `ThreadPoolExecutor` with configurable workers (default: 5)
- Each worker processes tickers concurrently
- Rate limiting respects API limits (default: 200 calls/min for Pro tier)

**Step 4: For Each Ticker (per worker)**
- Calls `get_historical_stock_data(ticker, reference_date, lookback_days=180)`
- **Critical**: Uses `get_price_history_at_date()` which:
  - Fetches price data ONLY up to `reference_date`
  - Calculates performance metrics using this limited dataset
  - Ensures NO look-ahead bias

**Step 5: Calculate Historical Metrics**
For each ticker, calculates:
- **Performance**: 1M%, 3M%, 6M% (based on prices relative to reference_date)
- **ADR%**: Average Daily Range percentage
- **RSI**: Relative Strength Index (14-day)
- **MACD**: Moving Average Convergence Divergence
- **Stochastic Oscillator**
- **ATR**: Average True Range
- **Overall Signal**: Bullish/Bearish/Neutral

**Step 6: Apply Filters**
- Filters by price range, ADR, performance thresholds
- Only stocks matching ALL filters are kept

**Step 7: Sort & Rank**
- Sorts filtered stocks by specified field (default: ADR)
- Takes top N results
- Updates session with final rankings

**Step 8: Return Results**
- Returns `{rankings: [...], session_id: '...'}`
- Rankings include all calculated metrics

#### 1.5 Frontend Display
- Displays historical rankings in a table
- Shows: Ticker, Price, ADR%, 1M%, 3M%, 6M%, RSI, Signal, Score
- User can click a row to select a stock for trade simulation

---

### Phase 2: Trade Simulation

#### 2.1 User Selection (`BacktestingView.tsx`)
- User clicks on a stock row
- Stock details auto-populate trade form:
  - Entry price (from historical ranking)
  - Suggested stop loss (calculated from ADR)
  - Suggested take profit (calculated from ADR)
- User enters quantity (default: 100 shares)

#### 2.2 Trade Simulation Request
- Frontend calls `simulateTrade()` API function
- **Endpoint**: `POST /midas/backtest/simulate_trade`

#### 2.3 Trade Simulation (`backtest_trade_simulator.py`)

**Step 1: Entry Date Calculation**
- Uses day AFTER reference_date as entry (more realistic)
- Example: If reference_date = 2024-09-01, entry_date = 2024-09-02

**Step 2: Fetch Forward Price History**
- Calls `get_forward_price_history(ticker, entry_date, end_date)`
- **Critical**: Fetches price data FROM entry_date FORWARD
- End date determined by:
  - `max_hold_days` (default: 60 days)
  - Or `exit_date` if specified
  - Or default 90 days

**Step 3: Day-by-Day Simulation**
- Iterates through each trading day forward from entry
- For each day:
  - Checks if stop loss hit (if price <= stop_loss): EXIT
  - Checks if take profit hit (if price >= take_profit): EXIT
  - Checks if max hold days reached: EXIT
  - Otherwise: HOLD and continue

**Step 4: Calculate Results**
When exit occurs:
- Exit price: Price at which trade exited
- Exit reason: "stop_loss", "take_profit", "max_hold_days", or "no_exit"
- Hold days: Number of days held
- Total cost: entry_price × quantity
- Total proceeds: exit_price × quantity
- Profit/Loss: proceeds - cost
- Profit/Loss %: (proceeds - cost) / cost × 100

**Step 5: Save to Session**
- If `session_id` provided, saves trade simulation to session
- Can retrieve all trades for a session later

**Step 6: Return Results**
- Returns trade simulation results
- Includes price history and events (stop loss/take profit hits)

#### 2.4 Frontend Display
- Displays trade results:
  - Entry/Exit dates and prices
  - Profit/Loss ($ and %)
  - Hold days
  - Exit reason
  - Price history chart (optional)

---

### Phase 3: Session Management

#### 3.1 Session Creation
- Sessions created early (before processing starts)
- Session ID generated from: `reference_date + filters`
- Stored in: `cache/backtest_sessions/{session_id}.json`
- Session includes:
  - `reference_date`: Historical date
  - `filters`: Applied filters
  - `historical_rankings`: Calculated rankings
  - `trade_results`: Simulated trades
  - `created_at` / `updated_at`: Timestamps

#### 3.2 Session Retrieval
- Can find session by:
  - Session ID directly
  - Reference date + filters
  - List all sessions

#### 3.3 Session Persistence
- Sessions persist even if:
  - Frontend request times out
  - Browser closes
  - Server restarts (as long as cache directory exists)
- Sessions expire after 30 days (configurable)

---

## Key Design Principles

### 1. No Look-Ahead Bias ✅
- **Historical Rankings**: Only use data up to `reference_date`
- **Trade Simulation**: Only use data forward from `entry_date`
- Never mix future data with past calculations

### 2. Parallel Processing ⚡
- Multi-threaded worker pool
- Configurable worker count (default: 5)
- Thread-safe rate limiting
- Progress tracking per worker

### 3. Session Persistence 💾
- Sessions saved to disk early
- Survives request timeouts
- Can resume work later
- Supports multiple concurrent sessions

### 4. Matching Scanner Criteria 🎯
- Uses same filters as regular scanner
- Same performance calculations (1M, 3M, 6M)
- Same technical indicators (RSI, MACD, etc.)
- Ensures backtest reflects real-world strategy

---

## Data Flow Diagram

```
Frontend (BacktestingView)
    ↓
API Request: GET /midas/backtest/historical_rankings
    ↓
Backend (app.py)
    ├─→ Check Session Cache
    │   ├─→ Found? Return cached rankings ✅
    │   └─→ Not found? Continue...
    ↓
Historical Screener Service
    ├─→ Create Session (early) 💾
    ├─→ Get Ticker Universe
    ├─→ Parallel Processing (Workers)
    │   ├─→ Worker 1: Process ticker A, B, C...
    │   ├─→ Worker 2: Process ticker D, E, F...
    │   └─→ Worker N: Process ticker X, Y, Z...
    │       ├─→ get_price_history_at_date() [NO LOOK-AHEAD]
    │       ├─→ Calculate Metrics (1M%, 3M%, ADR, RSI...)
    │       └─→ Apply Filters
    ├─→ Sort & Rank Results
    └─→ Update Session with Rankings
    ↓
Return Rankings to Frontend
    ↓
User Selects Stock
    ↓
API Request: POST /midas/backtest/simulate_trade
    ↓
Trade Simulator Service
    ├─→ get_forward_price_history() [FORWARD ONLY]
    ├─→ Day-by-Day Simulation
    │   ├─→ Check Stop Loss
    │   ├─→ Check Take Profit
    │   └─→ Check Max Hold Days
    ├─→ Calculate P/L
    └─→ Save to Session
    ↓
Return Trade Results to Frontend
    ↓
Display Results
```

---

## Example Timeline

**Reference Date**: 2024-09-01

1. **Historical Rankings** (as of 2024-09-01):
   - Uses price data up to 2024-09-01
   - Calculates 1M% performance (2024-08-01 to 2024-09-01)
   - Calculates 3M% performance (2024-06-01 to 2024-09-01)
   - Calculates 6M% performance (2024-03-01 to 2024-09-01)
   - Ranks stocks by ADR (using last 30 days before 2024-09-01)

2. **Trade Entry**: 2024-09-02 (next trading day)
   - Entry price: $50.00 (from historical ranking)
   - Stop loss: $47.50
   - Take profit: $55.00

3. **Trade Simulation** (forward from 2024-09-02):
   - Day 1 (2024-09-02): Price $50.20 → HOLD
   - Day 2 (2024-09-03): Price $49.80 → HOLD
   - Day 3 (2024-09-04): Price $47.40 → STOP LOSS HIT → EXIT
   - Exit price: $47.40
   - Hold days: 3
   - P/L: -$260 (-5.2%)

---

## Performance Characteristics

- **Processing Speed**: 
  - ~200 tickers/minute with 5 workers (Pro tier)
  - ~11,802 tickers ≈ ~59 minutes
  - Scales with worker count and rate limit

- **Accuracy**:
  - Processes entire universe by default (no sampling)
  - Accurate rankings (not from sample)
  - Full historical calculations

- **Session Storage**:
  - JSON files in `cache/backtest_sessions/`
  - Index file for fast lookups
  - Automatic expiration (30 days)

---

## Error Handling

- **Timeout Protection**: Session created early, survives timeouts
- **Rate Limiting**: Thread-safe rate limiter prevents API violations
- **Worker Errors**: Individual ticker failures don't stop entire process
- **Data Validation**: Validates dates, filters, ensures no future data

