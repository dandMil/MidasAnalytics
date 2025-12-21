# Backtesting System Proposal: ADR Performance Rank Strategy

## Current Strategy Overview

**Strategy:** ADR Performance Rank
- Pull stock universe (or check cache)
- Calculate ADR (Average Daily Range) and performance metrics over several months
- Order stocks by ADR performance rank
- Arbitrarily pick a few stocks from the top selection
- Attempt to swing trade them

## Backtesting Requirements

1. **Point-in-Time Universe**: See stocks as they existed at a historical date
2. **Historical Rankings**: Calculate ADR rankings using only data available up to that date
3. **Forward Performance**: See how selected stocks performed after entry
4. **Trade Simulation**: Simulate buying/selling with stop loss/take profit rules

---

## Proposed Architecture

### Phase 1: Historical Data Access Layer

**New Function: `get_price_history_at_date()`**
```python
def get_price_history_at_date(
    ticker: str, 
    end_date: str,  # YYYY-MM-DD format
    days_back: int = 180
) -> list[dict]:
    """
    Get historical price data up to a specific end date.
    This allows us to see the data as it existed at that point in time.
    """
```

**New Function: `get_forward_price_history()`**
```python
def get_forward_price_history(
    ticker: str,
    start_date: str,  # YYYY-MM-DD format
    end_date: str = None,  # Defaults to today
) -> list[dict]:
    """
    Get price data from a start date forward.
    Used to track performance after entry.
    """
```

### Phase 2: Historical Screener

**New Service: `historical_screener_service.py`**
```python
def get_historical_universe_rankings(
    reference_date: str,  # YYYY-MM-DD - the "point in time"
    filters: Dict,  # Same filters as current screener
    lookback_days: int = 180  # How much historical data to use for calculations
) -> List[Dict]:
    """
    Recreate the stock universe rankings as they would have appeared
    at the reference_date.
    
    Steps:
    1. Get ticker universe (use current universe as approximation, or fetch historical)
    2. For each ticker, get price history UP TO reference_date
    3. Calculate ADR and performance metrics using only that data
    4. Rank by ADR as they would have been ranked at that time
    5. Return top N results
    """
```

### Phase 3: Trade Simulation

**New Service: `backtest_trade_simulator.py`**
```python
def simulate_trade(
    ticker: str,
    entry_date: str,  # YYYY-MM-DD
    entry_price: float,
    quantity: int,
    stop_loss: float = None,
    take_profit: float = None,
    exit_date: str = None,  # Optional: force exit by date
    max_hold_days: int = None  # Optional: max holding period
) -> Dict:
    """
    Simulate a trade and track performance.
    
    Returns:
    {
        "entry_date": "2024-01-15",
        "entry_price": 50.00,
        "exit_date": "2024-02-20",
        "exit_price": 55.00,
        "exit_reason": "take_profit",  # or "stop_loss", "max_hold", "manual"
        "quantity": 100,
        "total_cost": 5000.00,
        "total_proceeds": 5500.00,
        "profit_loss": 500.00,
        "profit_loss_pct": 10.0,
        "hold_days": 36,
        "price_history": [...],
        "events": [
            {"date": "2024-01-20", "event": "stop_loss_hit", "price": 47.50},
            ...
        ]
    }
    """
```

### Phase 4: Strategy Backtesting Engine

**New Service: `adr_strategy_backtester.py`**
```python
class ADRStrategyBacktester:
    """
    Backtests the ADR Performance Rank strategy.
    """
    
    def run_single_backtest(
        self,
        reference_date: str,  # When to "look back" from
        top_n: int = 10,  # How many stocks to select from top rankings
        filters: Dict = None,
        capital_per_trade: float = 10000,  # Capital allocated per stock
        stop_loss_pct: float = 0.05,  # 5% stop loss
        take_profit_pct: float = 0.10,  # 10% take profit
        max_hold_days: int = 60,  # Max swing trade holding period
        exit_date: str = None  # When to close all positions
    ) -> Dict:
        """
        Run a complete backtest:
        
        1. Get historical rankings at reference_date
        2. Select top N stocks
        3. Simulate buying each at entry_price on reference_date
        4. Track each trade until exit (stop loss, take profit, or max hold)
        5. Calculate portfolio performance
        """
        
    def run_walk_forward_backtest(
        self,
        start_date: str,
        end_date: str,
        period_days: int = 30,  # Rebalance every 30 days
        **kwargs
    ) -> Dict:
        """
        Walk-forward analysis:
        - Start from start_date
        - Every period_days, re-run rankings and rebalance
        - Track cumulative performance
        """
```

---

## Implementation Approach

### Option A: Interactive Time-Travel Backtesting (Recommended First)

**User Experience:**
1. User selects a historical date (e.g., "2024-01-15")
2. System shows:
   - Top 50 stocks ranked by ADR as of that date
   - ADR values, performance metrics, signals (all calculated using data up to that date)
3. User selects one or more stocks from the list
4. System shows:
   - Forward performance chart from entry date to today (or selected exit date)
   - What the outcome would have been with various stop loss/take profit rules
   - Trade simulation results

**Benefits:**
- Intuitive and educational
- Helps users understand how their strategy would have worked
- Interactive exploration

### Option B: Automated Strategy Backtesting

**User Experience:**
1. User configures backtest parameters:
   - Start date / End date
   - Top N stocks to select
   - Position sizing rules
   - Stop loss / Take profit rules
   - Rebalancing frequency
2. System runs automated backtest:
   - For each period (weekly/monthly):
     - Calculate rankings at that point in time
     - Select top N stocks
     - Simulate trades
     - Track performance
3. System returns comprehensive results:
   - Total return
   - Win rate
   - Average hold time
   - Best/worst trades
   - Drawdown analysis
   - Comparison vs. benchmark (SPY)

**Benefits:**
- Statistical rigor
- Performance metrics
- Strategy optimization

---

## Technical Implementation Details

### 1. Historical Data Challenges

**Challenge:** Getting accurate historical universe
- **Solution 1:** Use current universe as approximation (stocks that exist now)
  - Pro: Simple, fast
  - Con: May include stocks that didn't exist historically
- **Solution 2:** Use Polygon's tickers endpoint with historical dates
  - Pro: More accurate
  - Con: May require premium API access, slower

**Recommendation:** Start with Solution 1, upgrade to Solution 2 if needed.

### 2. Point-in-Time Calculations

All calculations must use only data available up to the reference date:
- ADR: Calculate using last 30 days of data UP TO reference_date
- Performance 1M/3M/6M: Calculate using data UP TO reference_date
- RSI, MACD, etc.: Calculate using data UP TO reference_date

### 3. Trade Execution Rules

Simulate realistic trading:
- Entry: Next available price after reference_date (avoid look-ahead bias)
- Stop Loss: Monitor daily prices, exit if stop loss is hit
- Take Profit: Monitor daily prices, exit if take profit is hit
- Slippage: Optional - add small slippage to simulate real trading
- Commissions: Optional - subtract commission fees

### 4. Performance Metrics

Track:
- Total return (%)
- Number of trades
- Win rate (%)
- Average win / Average loss
- Profit factor (total wins / total losses)
- Maximum drawdown
- Sharpe ratio
- Average hold time
- Best trade / Worst trade

---

## API Endpoints

### Backend Endpoints

```
GET /midas/backtest/historical_rankings
  Query params:
    - reference_date: "2024-01-15" (required)
    - top_n: 50 (default)
    - filters: JSON string (same as screener filters)
  
  Returns: List of stocks ranked by ADR as of reference_date

GET /midas/backtest/simulate_trade
  Body:
    {
      "ticker": "AAPL",
      "entry_date": "2024-01-15",
      "entry_price": 185.00,
      "quantity": 100,
      "stop_loss": 175.75,
      "take_profit": 203.50,
      "exit_date": null,  # or "2024-03-15"
      "max_hold_days": 60
    }
  
  Returns: Trade simulation results with performance

POST /midas/backtest/run_strategy
  Body:
    {
      "reference_date": "2024-01-15",
      "top_n": 10,
      "capital_per_trade": 10000,
      "stop_loss_pct": 0.05,
      "take_profit_pct": 0.10,
      "max_hold_days": 60,
      "exit_date": "2024-06-15",
      "filters": {...}
    }
  
  Returns: Complete backtest results

POST /midas/backtest/walk_forward
  Body:
    {
      "start_date": "2023-01-01",
      "end_date": "2024-12-31",
      "period_days": 30,
      ... (same params as run_strategy)
    }
  
  Returns: Walk-forward backtest results
```

---

## Frontend Components

### New Component: `BacktestingView.tsx`

**Features:**
1. **Date Picker**: Select historical reference date
2. **Historical Rankings Table**: 
   - Shows top stocks ranked by ADR at that date
   - All metrics calculated as of that date
   - Visual indication that it's "historical view"
3. **Stock Selection**: 
   - Select one or more stocks from historical rankings
   - Configure trade parameters (quantity, stop loss, take profit)
4. **Forward Performance Chart**: 
   - Chart showing price action from entry date forward
   - Markers for stop loss / take profit levels
   - Highlight exit point and reason
5. **Results Panel**: 
   - Trade outcome (profit/loss)
   - Hold duration
   - Exit reason
   - Comparison to multiple strategies

### UI Flow:
```
[Date Picker] → [View Historical Rankings] → [Select Stock(s)] → 
[Configure Trade] → [Run Simulation] → [View Results]
```

---

## Development Phases

### Phase 1: Core Infrastructure (Week 1)
- ✅ Add `get_price_history_at_date()` to polygon_client
- ✅ Add `get_forward_price_history()` to polygon_client
- ✅ Create `historical_screener_service.py`
- ✅ Test historical rankings accuracy

### Phase 2: Trade Simulation (Week 1-2)
- ✅ Create `backtest_trade_simulator.py`
- ✅ Implement stop loss / take profit logic
- ✅ Track trade events and performance
- ✅ Test with sample trades

### Phase 3: Strategy Backtester (Week 2)
- ✅ Create `adr_strategy_backtester.py`
- ✅ Implement single backtest
- ✅ Implement walk-forward backtest
- ✅ Calculate performance metrics

### Phase 4: API & Frontend (Week 2-3)
- ✅ Create backend endpoints
- ✅ Create `BacktestingView.tsx` component
- ✅ Integrate with existing UI
- ✅ Add charts and visualizations

### Phase 5: Testing & Optimization (Week 3)
- ✅ Test with various date ranges
- ✅ Validate results accuracy
- ✅ Performance optimization
- ✅ Documentation

---

## Questions for Discussion

1. **Historical Universe Accuracy**: 
   - Do we need exact historical universe, or is current universe acceptable?
   - Should we filter out stocks that IPO'd after reference_date?

2. **Entry Price**: 
   - Should we use the close price on reference_date, or next open?
   - This affects realism (avoid look-ahead bias)

3. **Position Sizing**: 
   - Fixed capital per trade (e.g., $10,000 per stock)?
   - Percentage of portfolio?
   - Equal weight vs. ADR-weighted?

4. **Rebalancing**: 
   - How often should we rebalance?
   - Weekly? Monthly? When a position exits?

5. **Multiple Trades**: 
   - Can we hold multiple positions simultaneously?
   - Maximum number of concurrent positions?

6. **Data Storage**: 
   - Should we cache historical rankings?
   - Store backtest results in database?

---

## Recommended Next Steps

1. **Start with Option A (Interactive)**: Build the time-travel view first
   - More intuitive
   - Easier to validate
   - Educational for users

2. **Iterate to Option B**: Add automated backtesting once interactive version works
   - Users can see individual trades working
   - Then run full strategy backtests

3. **Focus on Accuracy**: Ensure no look-ahead bias
   - All calculations use only data up to reference_date
   - Entry prices use next available price after decision date

4. **Performance Optimization**: 
   - Cache historical price data
   - Batch API calls where possible
   - Consider local data storage for frequently used ranges

---

## Example Use Case

**User wants to test strategy on Jan 15, 2024:**

1. User selects date: `2024-01-15`
2. System calculates ADR rankings using data up to Jan 15:
   - Gets price history for each ticker ending on Jan 15
   - Calculates ADR, performance metrics
   - Ranks by ADR
   - Returns: Top 50 stocks as they would have appeared

3. User sees historical rankings:
   ```
   Rank | Ticker | ADR% | 1M% | 3M% | 6M% | Price (Jan 15)
   1    | TSLA   | 4.5  | 15  | 25  | 30  | $248.50
   2    | NVDA   | 4.2  | 20  | 40  | 60  | $546.20
   ...
   ```

4. User selects TSLA, configures:
   - Quantity: 100 shares
   - Stop Loss: $236.08 (5% below entry)
   - Take Profit: $273.35 (10% above entry)

5. System simulates trade:
   - Entry: Jan 16, 2024 @ $248.50 (next day open)
   - Monitors daily prices forward
   - Finds: Take profit hit on Jan 28 @ $273.35
   - Results: +10% profit, 12 day hold, $2,485 profit

6. User can then test multiple stocks or run full strategy backtest

---

This approach gives you a comprehensive backtesting system that accurately simulates your ADR-based strategy!
