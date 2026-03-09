# Backtest Mode: Data Flow and Logic

## Overview

The backtest mode implements a two-phase system that simulates historical trading:
1. **Screener Phase**: Generates historical stock rankings as they would have appeared at a reference date
2. **Strategy Phase**: Simulates trades forward from the reference date using the ranked stocks

This design ensures **no look-ahead bias** by strictly separating historical data (for screening) from forward data (for trade simulation).

---

## Phase 1: Screener - Historical Rankings Generation

### Data Flow

```
User Request (Frontend)
    ↓
GET /midas/backtest/historical_rankings
    ↓
Session Cache Check (app.py)
    ├─→ Found? Return cached rankings ✅
    └─→ Not found? Continue...
    ↓
Historical Screener Service (historical_screener_service.py)
    ├─→ Create Session (early) 💾
    ├─→ Load Ticker Universe (data/us_stock_universe.csv)
    ├─→ Apply Sector Filter (if specified)
    ├─→ Apply Sampling (if use_sample=True)
    ├─→ Parallel Processing (ThreadPoolExecutor)
    │   ├─→ Worker 1: Process tickers A, B, C...
    │   ├─→ Worker 2: Process tickers D, E, F...
    │   └─→ Worker N: Process tickers X, Y, Z...
    │       ├─→ Rate Limiting (respects API limits)
    │       ├─→ get_price_history_at_date() [NO LOOK-AHEAD]
    │       ├─→ Calculate Metrics (using only data up to reference_date)
    │       └─→ Apply Filters
    ├─→ Sort & Rank Results
    ├─→ Update Session with Rankings
    └─→ Return Top N Results
    ↓
Frontend Display
```

### Key Logic: Historical Data Fetching

**Function**: `get_historical_stock_data(ticker, reference_date, lookback_days=180)`

**Critical Constraint**: Uses `get_price_history_at_date()` which:
- Fetches price data **ONLY up to and including** the reference_date
- Calculates all metrics using this limited dataset
- Ensures **NO future data** is used in calculations

**Metrics Calculated** (as of reference_date):
1. **Current Price**: Most recent close price up to reference_date
2. **Performance Metrics**:
   - `performance_1m`: Price change over last 30 days (relative to reference_date)
   - `performance_3m`: Price change over last 90 days
   - `performance_6m`: Price change over last 180 days
3. **ADR%**: Average Daily Range percentage (last 30 days up to reference_date)
4. **Technical Indicators**:
   - RSI (14-day)
   - MACD (Moving Average Convergence Divergence)
   - Stochastic Oscillator
   - ATR (Average True Range)
5. **Overall Signal**: Bullish/Bearish/Neutral (weighted combination of indicators)

### Filtering Logic

**Function**: `get_historical_rankings()`

**Filter Application** (in order):
1. **Sector Filter**: Pre-filters ticker universe by sector (if specified)
2. **Universe Size Limit**: Limits total tickers if `max_universe_size` specified
3. **Sampling**: Optional stratified sampling if `use_sample=True`
4. **Per-Ticker Filters** (applied during parallel processing):
   - Price range: `min_price` ≤ current_price ≤ `max_price`
   - ADR range: `min_adr` ≤ adr_percentage ≤ `max_adr`
   - Performance filters:
     - `min_1m_performance` ≤ performance_1m ≤ `max_1m_performance`
     - `min_3m_performance` ≤ performance_3m ≤ `max_3m_performance`
     - `min_6m_performance` ≤ performance_6m ≤ `max_6m_performance`
5. **Sorting**: Sorts by `sort_by` field (default: 'adr') in `sort_order` (default: 'desc')
6. **Top N Selection**: Returns top N stocks after sorting

### Parallel Processing

**Implementation**: Uses `ThreadPoolExecutor` with configurable workers

**Features**:
- **Rate Limiting**: Thread-safe rate limiter respects API limits (default: 200 calls/min for Pro tier)
- **Progress Tracking**: Logs progress every 10 seconds and worker status every 15 seconds
- **Checkpointing**: Session created early (before processing) and updated incrementally
- **Error Handling**: Individual ticker failures don't stop the entire process

**Worker Flow** (per ticker):
```python
def process_ticker(ticker):
    1. Rate limiter.wait_if_needed()  # Respect API limits
    2. stock_data = get_historical_stock_data(ticker, reference_date)
    3. if not stock_data: return None  # Insufficient data
    4. Apply all filters sequentially
    5. if passes all filters: return stock_data
    6. else: return None  # Filtered out
```

### Session Management

**Session Structure**:
```json
{
  "session_id": "abc123...",
  "reference_date": "2024-09-01",
  "filters": {
    "sector": "tech",
    "min_price": 10.0,
    "min_adr": 3.0,
    ...
  },
  "historical_rankings": [
    {
      "ticker": "AAPL",
      "current_price": 150.00,
      "adr_percentage": 2.5,
      "performance_1m": 5.2,
      ...
    },
    ...
  ],
  "screening_strategy": {...},
  "selling_strategy": null,
  "trade_results": {...}
}
```

**Session Lifecycle**:
1. **Early Creation**: Session created immediately (before processing starts)
   - Ensures session exists even if request times out
   - Initially has empty rankings
2. **Incremental Updates**: Rankings updated as processing completes
3. **Cache Location**: `cache/backtest_sessions/{session_id}.json`

---

## Phase 2: Strategy - Trade Simulation

### Data Flow

```
User Selection (Frontend)
    ↓
POST /midas/backtest/simulate_trade
    ↓
Trade Simulator Service (backtest_trade_simulator.py)
    ├─→ get_forward_price_history() [FORWARD ONLY]
    ├─→ Day-by-Day Simulation
    │   ├─→ Check Stop Loss (if low ≤ stop_loss)
    │   ├─→ Check Take Profit (if high ≥ take_profit)
    │   ├─→ Check Max Hold Days
    │   └─→ Check Forced Exit Date
    ├─→ Calculate P/L
    ├─→ Save to Session
    └─→ Return Trade Results
    ↓
Frontend Display
```

### Key Logic: Forward Data Fetching

**Function**: `simulate_trade(ticker, entry_date, entry_price, quantity, stop_loss, take_profit, max_hold_days)`

**Critical Constraint**: Uses `get_forward_price_history()` which:
- Fetches price data **ONLY from entry_date forward**
- Never uses data before entry_date
- Ensures trade simulation uses realistic forward-looking data

**Data Range Calculation**:
- If `exit_date` specified: Fetch from entry_date to exit_date
- If `max_hold_days` specified: Fetch from entry_date to entry_date + max_hold_days
- Default: Fetch 90 days forward from entry_date

### Trade Simulation Logic

**Day-by-Day Processing**:
```python
for each day in forward_price_history:
    1. Check Stop Loss: if low ≤ stop_loss:
       → Exit immediately at stop_loss price
       → exit_reason = "stop_loss"
       → break
    
    2. Check Take Profit: if high ≥ take_profit:
       → Exit immediately at take_profit price
       → exit_reason = "take_profit"
       → break
    
    3. Check Max Hold Days: if days_held ≥ max_hold_days:
       → Exit at closing price
       → exit_reason = "max_hold_days"
       → break
    
    4. Check Forced Exit Date: if date ≥ exit_date:
       → Exit at closing price
       → exit_reason = "forced_exit"
       → break

# If no exit condition met:
→ Exit at final available price
→ exit_reason = "no_exit_triggered"
```

**Exit Priority** (first condition met wins):
1. Stop Loss (highest priority - risk management)
2. Take Profit
3. Max Hold Days
4. Forced Exit Date
5. No Exit Triggered (uses final price)

### Performance Calculation

**Metrics Calculated**:
```python
total_cost = entry_price * quantity
total_proceeds = exit_price * quantity
profit_loss = total_proceeds - total_cost
profit_loss_pct = (profit_loss / total_cost) * 100
hold_days = (exit_date - entry_date).days
```

**Return Structure**:
```json
{
  "entry_date": "2024-09-02",
  "entry_price": 50.00,
  "exit_date": "2024-09-05",
  "exit_price": 47.40,
  "exit_reason": "stop_loss",
  "quantity": 100,
  "total_cost": 5000.00,
  "total_proceeds": 4740.00,
  "profit_loss": -260.00,
  "profit_loss_pct": -5.20,
  "hold_days": 3,
  "price_history": [...],
  "events": [
    {
      "date": "2024-09-05",
      "event": "stop_loss_hit",
      "price": 47.50,
      "low": 47.40,
      "high": 48.20
    }
  ]
}
```

---

## Alternative: Strategy-Based Backtesting (BacktestEngine)

### Overview

The `BacktestEngine` class provides an alternative approach that uses strategy objects with `apply()` methods to generate buy/sell signals dynamically.

### Data Flow

```
Strategy Object (e.g., VolatilityStrategy)
    ↓
BacktestEngine.run(strategy, data, ticker)
    ├─→ Convert data to DataFrame
    ├─→ Initialize portfolio (cash=10000, position=0)
    ├─→ Day-by-Day Loop (starting at index 20)
    │   ├─→ Get sub_df (data up to current index)
    │   ├─→ strategy.apply(sub_df, ticker)
    │   │   └─→ Returns: {signal, price, stop_loss, take_profit, ...}
    │   ├─→ Execute Trade Logic:
    │   │   ├─→ If signal='buy' and position=0:
    │   │   │   → Buy at current price
    │   │   │   → position = cash / price
    │   │   │   → cash = 0
    │   │   └─→ If signal='sell' and position>0:
    │   │       → Sell at current price
    │   │       → cash = position * price
    │   │       → position = 0
    │   └─→ Track portfolio value
    └─→ Calculate total return
    ↓
Return Results
```

### Strategy Interface

**Strategy Requirements**:
- Must implement `apply(df: pd.DataFrame, ticker: str) -> dict`
- Returns dictionary with:
  - `signal`: 'buy', 'sell', or 'hold'
  - `price`: Current price
  - `stop_loss`: Stop loss price (optional)
  - `take_profit`: Take profit price (optional)
  - `expected_profit`: Expected profit amount (optional)
  - `expected_loss`: Expected loss amount (optional)

**Example Strategy**: `VolatilityStrategy`
```python
class VolatilityStrategy:
    def apply(self, df: pd.DataFrame, ticker: str):
        # Calculate ATR
        df['atr'] = df['high'].sub(df['low']).rolling(window=14).mean()
        price = df['c'].iloc[-1]
        atr = df['atr'].iloc[-1]
        
        # Calculate stop loss and take profit based on ATR
        stop_loss = price - (2.0 * atr)
        take_profit = price + (3.0 * atr)
        
        # Generate signal (example logic)
        signal = "buy" if len(df) % 2 == 0 else "hold"
        
        return {
            "signal": signal,
            "price": price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            ...
        }
```

### Key Differences from Trade Simulator

| Feature | Trade Simulator | BacktestEngine |
|---------|----------------|----------------|
| **Input** | Manual entry/exit prices | Strategy-generated signals |
| **Entry** | Fixed entry price | Dynamic based on strategy |
| **Exit** | Fixed stop/take profit | Dynamic based on strategy signals |
| **Use Case** | Testing specific trade setups | Testing strategy algorithms |
| **Flexibility** | Limited to predefined rules | Fully customizable via strategies |

---

## Complete End-to-End Flow

### Example Timeline

**Reference Date**: 2024-09-01

#### Phase 1: Historical Rankings (as of 2024-09-01)
1. Load ticker universe (~11,802 tickers)
2. For each ticker:
   - Fetch price data up to 2024-09-01 (no future data)
   - Calculate metrics:
     - 1M% performance: 2024-08-01 to 2024-09-01
     - 3M% performance: 2024-06-01 to 2024-09-01
     - 6M% performance: 2024-03-01 to 2024-09-01
     - ADR%: Last 30 days before 2024-09-01
     - RSI, MACD, etc.: Using data up to 2024-09-01
3. Apply filters (price, ADR, performance thresholds)
4. Sort by ADR (descending)
5. Return top 50 stocks

#### Phase 2: Trade Simulation (forward from 2024-09-02)
1. User selects stock from rankings (e.g., AAPL at $150.00)
2. Configure trade:
   - Entry date: 2024-09-02 (next trading day)
   - Entry price: $150.00
   - Quantity: 100 shares
   - Stop loss: $142.50 (5% below entry)
   - Take profit: $165.00 (10% above entry)
   - Max hold days: 60
3. Fetch forward price data from 2024-09-02
4. Day-by-day simulation:
   - Day 1 (2024-09-02): Price $150.20 → HOLD
   - Day 2 (2024-09-03): Price $149.80 → HOLD
   - Day 3 (2024-09-04): Price $142.40 → STOP LOSS HIT → EXIT
5. Calculate results:
   - Exit price: $142.50 (stop loss)
   - Hold days: 3
   - P/L: -$750 (-5.0%)

---

## Key Design Principles

### 1. No Look-Ahead Bias
- **Screener**: Uses only data up to reference_date
- **Trade Simulator**: Uses only data from entry_date forward
- **Separation**: Historical screening and forward simulation are completely separate

### 2. Realistic Simulation
- **Entry**: Uses next available price after reference_date
- **Exit**: Checks daily high/low for stop/take profit triggers
- **Slippage**: Currently not implemented (uses exact prices)

### 3. Performance Optimization
- **Parallel Processing**: Multi-threaded ticker processing
- **Rate Limiting**: Respects API limits
- **Caching**: Session-based caching for rankings
- **Sampling**: Optional sampling for faster results

### 4. Error Handling
- **Individual Failures**: Ticker processing failures don't stop entire scan
- **Data Validation**: Checks for sufficient data (minimum 30 bars)
- **Graceful Degradation**: Returns partial results if processing interrupted

---

## Current Limitations

1. **No Slippage**: Uses exact prices (no bid/ask spread simulation)
2. **No Commissions**: Doesn't subtract trading fees
3. **No Partial Fills**: Assumes full order execution
4. **Fixed Universe**: Uses current ticker universe (may include stocks that didn't exist historically)
5. **Strategy Backtesting**: `BacktestEngine` exists but full integration with screener not yet implemented

---

## Future Enhancements

1. **Full Strategy Integration**: Connect `BacktestEngine` with historical screener
2. **Walk-Forward Analysis**: Test strategy across multiple time periods
3. **Portfolio Simulation**: Test multiple stocks simultaneously
4. **Advanced Metrics**: Sharpe ratio, maximum drawdown, win rate
5. **Benchmark Comparison**: Compare against SPY or other benchmarks
