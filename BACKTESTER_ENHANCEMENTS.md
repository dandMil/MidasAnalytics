# Backtester Enhancements

## Summary

Enhanced the backtester with strategy management and batch simulation capabilities.

---

## 1. Strategy System Architecture

### Strategy Types

The system now supports two types of strategies:

#### **Screening Strategies** (How to find stocks)
- **Purpose**: Define how to filter and rank stocks from the universe
- **Example**: ADR Stack Rank
- **Components**:
  - Filters (price, ADR, performance thresholds)
  - Sort criteria (field and order)
  - Sector selection

#### **Selling Strategies** (How to exit trades) - *Future Implementation*
- **Purpose**: Define exit rules for trades
- **Components**:
  - Stop loss method (percentage, ATR-based, fixed)
  - Take profit method
  - Max hold days

### Current Strategy: ADR Stack Rank

**Type**: Screening Strategy  
**ID**: `adr_stack_rank`  
**Description**: Ranks stocks by ADR with performance filters (1M, 3M, 6M)

**Configuration**:
```typescript
{
  id: 'adr_stack_rank',
  name: 'ADR Stack Rank',
  type: 'screening',
  description: 'Ranks stocks by ADR with performance filters (1M, 3M, 6M)',
  filters: {
    sort_by: 'adr',
    sort_order: 'desc',
    // Plus all the performance filters (1M, 3M, 6M, ADR, price, etc.)
  }
}
```

---

## 2. Strategy Persistence

### Backend Changes

**Session Cache** (`services/backtest_session_cache.py`):
- Added `screening_strategy` and `selling_strategy` fields to session data
- `update_session()` now accepts strategy parameters
- Strategies are saved with sessions and persist across sessions

**Session Structure**:
```python
{
  "session_id": "...",
  "reference_date": "2024-09-01",
  "filters": {...},
  "historical_rankings": [...],
  "screening_strategy": {
    "id": "adr_stack_rank",
    "name": "ADR Stack Rank",
    "type": "screening",
    "description": "...",
    "filters": {...}
  },
  "selling_strategy": null,  # For future use
  "trade_results": {...},
  ...
}
```

### Frontend Changes

**Strategy State**:
- `currentScreeningStrategy` state stores the active screening strategy
- Default: ADR Stack Rank strategy
- Strategy is displayed in the UI panel above rankings

**Strategy Display**:
- Shows current strategy name and description
- Displays strategy type (screening/selling)
- Shows sort criteria (field and order)

---

## 3. Batch Simulation

### Features

**Simulate All Stocks**:
- "Simulate All" button simulates trades for all stocks in the historical rankings
- Uses the same trade configuration (quantity, stop loss, take profit, max hold days) for all trades
- Processes stocks sequentially with progress tracking

**Batch Results Display**:
- Summary statistics:
  - Total winners
  - Total losers
  - Total P/L (dollars)
  - Average P/L percentage
- Detailed results table showing:
  - Ticker
  - Entry/Exit prices
  - Profit/Loss ($ and %)
  - Hold days
  - Exit reason

### Implementation

**Frontend** (`BacktestingView.tsx`):
```typescript
const handleBatchSimulate = async () => {
  // Validates inputs
  // Confirms with user
  // Loops through all historicalRankings
  // Simulates each trade
  // Updates batchResults as it progresses
  // Displays summary and detailed results
}
```

**UI Elements**:
- "Simulate All (N)" button in strategy info panel
- Progress indicator during simulation
- Batch results panel with summary stats and table
- Color-coded P/L (green for positive, red for negative)

---

## 4. UI Enhancements

### Strategy Info Panel

Added above the historical rankings table:
- Shows current strategy name and description
- Displays strategy type and sort criteria
- Contains "Simulate All" button for batch simulation

### Batch Results Panel

Appears below trade simulation panel when batch simulation completes:
- Summary cards with key statistics
- Scrollable table with all trade results
- Color-coded profit/loss indicators

### Individual vs Batch Simulation

**Individual Simulation** (existing):
- Select a stock from rankings
- Configure trade parameters
- Run single trade simulation
- View detailed results for one trade

**Batch Simulation** (new):
- Use same trade configuration
- Simulate all stocks in rankings
- View aggregated results and statistics
- Compare performance across all trades

---

## 5. Data Flow

### Strategy Saving

1. **On Historical Rankings Fetch**:
   - Strategy is automatically associated with the session
   - Strategy info is stored in session cache
   - Strategy can be restored when loading session

2. **On Session Load**:
   - Strategy is restored from session data
   - UI updates to show the strategy that was used

### Batch Simulation Flow

```
User clicks "Simulate All"
    ↓
Validates trade config (quantity, stop loss, take profit, max hold days)
    ↓
Confirms with user (shows number of stocks to simulate)
    ↓
For each stock in historicalRankings:
    ├─→ Fetch forward price history
    ├─→ Simulate trade day-by-day
    ├─→ Check stop loss, take profit, max hold days
    ├─→ Calculate P/L
    └─→ Add result to batchResults
    ↓
Update UI with results (as they complete)
    ↓
Display summary statistics and detailed table
```

---

## 6. Future Enhancements (Planned)

### 1. Additional Strategies

**Screening Strategies**:
- Momentum-based ranking
- RSI-based ranking
- Multi-factor scoring
- Custom filter combinations

**Selling Strategies**:
- Trailing stop loss
- ATR-based stops
- Time-based exits
- Profit target scaling

### 2. Strategy Builder UI

- Visual strategy configuration interface
- Save/load custom strategies
- Strategy testing and comparison
- Strategy library/collection

### 3. Enhanced Batch Analysis

- Portfolio-level statistics
- Risk metrics (Sharpe ratio, max drawdown)
- Win rate analysis
- Performance by sector/market cap
- Comparison across different strategies

---

## 7. Usage Examples

### Example 1: Single Stock Simulation

1. Select reference date (e.g., 2024-09-01)
2. Fetch historical rankings
3. Click on a stock row to select it
4. Configure trade: quantity, stop loss, take profit, max hold days
5. Click "Run Trade Simulation"
6. View individual trade results

### Example 2: Batch Simulation

1. Select reference date (e.g., 2024-09-01)
2. Fetch historical rankings (e.g., top 50 stocks)
3. Configure trade parameters (applies to all)
4. Click "Simulate All (50)" button
5. Wait for all simulations to complete
6. Review summary statistics and detailed results table

### Example 3: Strategy Comparison

1. Run batch simulation with ADR Stack Rank strategy
2. Note the results (win rate, total P/L, etc.)
3. *Future*: Switch to a different strategy
4. Run batch simulation again
5. Compare results between strategies

---

## 8. Technical Details

### State Management

**New State Variables**:
- `batchResults`: Array of trade simulation results
- `batchSimulating`: Boolean flag for batch simulation in progress
- `currentScreeningStrategy`: Current screening strategy configuration

**Updated State**:
- `tradeConfig`: Now includes `maxHoldDays`

### API Integration

**Existing APIs Used**:
- `getHistoricalRankings()`: Fetches historical rankings
- `simulateTrade()`: Simulates individual trades (called multiple times for batch)

**No New Backend APIs Required**:
- Batch simulation is handled client-side by calling `simulateTrade()` in a loop
- Strategies are stored in session cache alongside other session data

### Performance Considerations

**Batch Simulation**:
- Sequential processing (one trade at a time)
- Progress updates after each trade completes
- Can be interrupted (results are shown as they complete)
- For large batches (50+ stocks), may take several minutes

**Optimization Opportunities** (Future):
- Parallel trade simulation (multiple trades simultaneously)
- Progress bar with percentage complete
- Cancel/stop batch simulation button
- Resume interrupted batch simulations

---

## 9. Files Modified

### Frontend
- `midas-dashboard/src/components/BacktestingView.tsx`
  - Added strategy interfaces and state
  - Added batch simulation function
  - Added strategy info panel UI
  - Added batch results display UI

### Backend
- `MidasAnalytics/services/backtest_session_cache.py`
  - Added `screening_strategy` and `selling_strategy` fields to session data
  - Updated `update_session()` to accept strategy parameters
  - Added backward compatibility for existing sessions

---

## 10. Testing Checklist

- [x] Single stock simulation still works
- [x] Batch simulation processes all stocks
- [x] Batch results display correctly
- [x] Strategy info is displayed
- [x] Session loading restores strategy
- [x] Max hold days is configurable
- [x] Error handling for failed simulations
- [x] Progress tracking during batch simulation

---

## Summary

The backtester now supports:
1. ✅ **Strategy System**: Framework for screening and selling strategies (ADR Stack Rank implemented)
2. ✅ **Strategy Persistence**: Strategies saved with sessions
3. ✅ **Batch Simulation**: Simulate trades for all stocks in rankings
4. ✅ **Enhanced UI**: Strategy display and batch results panel
5. ✅ **Configurable Max Hold Days**: Dynamic setting from UI

The system is ready for future strategy implementations while maintaining full backward compatibility with existing sessions.

