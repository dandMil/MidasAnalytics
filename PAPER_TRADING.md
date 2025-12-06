# Paper Trading System

## Overview

Paper trading allows you to practice trading with virtual money without risking real capital. Track your trades, monitor P&L, and test strategies in a risk-free environment.

## Features

✅ **Cash Balance Tracking** - Track available cash and spending  
✅ **Portfolio Management** - Buy/sell stocks with automatic position tracking  
✅ **P&L Calculation** - Real-time unrealized and realized profit/loss  
✅ **Transaction History** - Complete audit trail of all trades  
✅ **Daily Account Updates** - Track account value and returns over time  
✅ **Available from Screener** - Execute trades directly from stock screener view  
✅ **Available from other views** - Trade from any view that shows stocks

---

## Database Structure

### `paper_portfolio` Table
Current positions in paper trading account:
- `ticker` - Stock symbol
- `shares` - Number of shares owned
- `entry_price` - Average cost per share (dollar-cost averaged)
- `stop_loss` - Stop loss price
- `take_profit` - Take profit price
- `updated_at` - Last update timestamp

### `paper_transactions` Table
Complete transaction history:
- `ticker` - Stock symbol
- `shares` - Number of shares (positive for buy, negative for sell)
- `price` - Transaction price
- `transaction_type` - "BUY" or "SELL"
- `realized_pnl` - Realized profit/loss (for sells)
- `realized_pnl_percent` - Realized P&L percentage
- `created_at` - Transaction timestamp

### `paper_account` Table
Account balance and performance:
- `starting_capital` - Initial capital (default: $100,000)
- `cash_balance` - Available cash
- `portfolio_value` - Total portfolio value (cash + positions)
- `unrealized_pnl` - Unrealized profit/loss from open positions
- `realized_pnl` - Total realized profit/loss from closed positions
- `total_pnl` - Total P&L (unrealized + realized)
- `trading_date` - Date of this account snapshot

---

## API Endpoints

### 1. Execute Paper Trade
**POST** `/midas/paper_trade/do_transaction`

Execute a buy or sell transaction.

**Request:**
```json
{
  "ticker": "AAPL",
  "shares": 10,  // Positive for buy, negative for sell
  "current_price": 150.00,
  "stop_loss": 145.00,  // Optional
  "take_profit": 160.00  // Optional
}
```

**Response:**
```json
{
  "success": true,
  "message": "Purchased 10 shares of AAPL at $150.00 for $1500.00",
  "ticker": "AAPL",
  "shares": 10,
  "price": 150.00,
  "cash_balance": 98500.00,
  "portfolio_value": 100000.00,
  "unrealized_pnl": 0.00,
  "total_pnl": 0.00,
  "recommendation": {...}
}
```

**Error Cases:**
- `INSUFFICIENT_CASH` - Not enough cash to buy
- `NO_POSITION` - No position to sell
- `INSUFFICIENT_SHARES` - Not enough shares to sell

---

### 2. Get Account Status
**GET** `/midas/paper_trade/account`

Get current account balance, P&L, and portfolio value.

**Response:**
```json
{
  "starting_capital": 100000.00,
  "cash_balance": 98500.00,
  "portfolio_value": 101500.00,
  "total_portfolio_value": 100000.00,
  "unrealized_pnl": 1500.00,
  "realized_pnl": 0.00,
  "total_pnl": 1500.00,
  "total_return_percent": 1.50,
  "last_updated": "2024-12-02T21:30:00",
  "trading_date": "2024-12-02"
}
```

---

### 3. Get Portfolio
**GET** `/midas/paper_trade/portfolio`

Get all open positions with current values and P&L.

**Response:**
```json
[
  {
    "ticker": "AAPL",
    "shares": 10,
    "entry_price": 150.00,
    "current_price": 151.50,
    "position_value": 1515.00,
    "cost_basis": 1500.00,
    "unrealized_pnl": 15.00,
    "unrealized_pnl_percent": 1.00,
    "stop_loss": 145.00,
    "take_profit": 160.00,
    "updated_at": "2024-12-02T21:00:00"
  }
]
```

---

### 4. Get Transaction History
**GET** `/midas/paper_trade/transactions?limit=50`

Get transaction history.

**Response:**
```json
[
  {
    "ticker": "AAPL",
    "shares": 10,
    "price": 150.00,
    "transaction_type": "BUY",
    "realized_pnl": null,
    "realized_pnl_percent": null,
    "created_at": "2024-12-02T21:00:00"
  },
  {
    "ticker": "TSLA",
    "shares": 5,
    "price": 200.00,
    "transaction_type": "SELL",
    "realized_pnl": 25.00,
    "realized_pnl_percent": 2.50,
    "created_at": "2024-12-02T20:00:00"
  }
]
```

---

### 5. Reset Account
**POST** `/midas/paper_trade/reset`

Reset paper trading account (clear all positions and reset cash).

**Request:**
```json
{
  "starting_capital": 100000.00  // Optional, defaults to 100000
}
```

**Response:**
```json
{
  "success": true,
  "message": "Paper trading account reset with $100,000.00",
  "starting_capital": 100000.00,
  "cash_balance": 100000.00
}
```

---

## Frontend API Functions

### TypeScript/React Functions

Located in `src/services/api.tsx`:

```typescript
// Execute paper trade
doPaperTransaction({
  ticker: "AAPL",
  transactionType: "buy",  // or "sell"
  shares: 10,
  current_price: 150.00,
  stop_loss: 145.00,  // Optional
  take_profit: 160.00  // Optional
})

// Get account status
getPaperAccount()

// Get portfolio positions
getPaperPortfolio()

// Get transaction history
getPaperTransactions(50)  // limit

// Reset account
resetPaperAccount(100000)  // starting capital
```

---

## How It Works

### Buying Stocks

1. **Check Cash Balance** - Validates sufficient cash for purchase
2. **Calculate Cost** - `shares × current_price`
3. **Update Position** - Adds to existing position or creates new one
4. **Dollar-Cost Averaging** - If buying more shares, calculates new average entry price
5. **Deduct Cash** - Removes cost from cash balance
6. **Record Transaction** - Saves transaction to history
7. **Update Account** - Recalculates portfolio value and P&L

### Selling Stocks

1. **Check Position** - Validates position exists with sufficient shares
2. **Calculate P&L** - `(current_price - entry_price) × shares`
3. **Update Position** - Reduces shares or removes position if fully sold
4. **Add Cash** - Adds sale proceeds to cash balance
5. **Record Transaction** - Saves transaction with realized P&L
6. **Update Account** - Recalculates portfolio value and P&L

### P&L Calculation

**Unrealized P&L:**
- Calculated from open positions
- `(current_price - entry_price) × shares` for each position
- Updated in real-time based on current market prices

**Realized P&L:**
- Calculated when selling
- Summed from all completed sell transactions
- Permanent (doesn't change after transaction)

**Total P&L:**
- `unrealized_pnl + realized_pnl`
- Total profit/loss since account creation

---

## Usage Examples

### From Screener View

1. Screen stocks using filters
2. Click on a stock to view details
3. Use transaction form to:
   - Select "Buy" or "Sell"
   - Enter number of shares
   - Set stop loss and take profit (optional)
   - Execute trade
4. View updated cash balance and portfolio

### From Portfolio View

1. View current positions
2. See unrealized P&L for each position
3. Sell positions directly
4. Add to positions (buy more shares)

### Daily Tracking

1. Check account status to see:
   - Total portfolio value
   - Daily P&L
   - Total return percentage
2. Review transaction history
3. Analyze performance over time

---

## Default Settings

- **Starting Capital:** $100,000.00
- **Database:** `portfolio.db` (same database, separate tables)
- **Price Updates:** Real-time from Polygon.io API

---

## Integration Points

### Screener View
- Buy/sell directly from screener results
- View cash balance before executing trades
- See transaction success/failure messages

### Portfolio View (Future)
- View all paper trading positions
- Monitor P&L for each position
- Execute trades from portfolio view

### Stock Detail Views (Future)
- Trade from any stock detail page
- View paper trading history for specific ticker

---

## Error Handling

The system handles common errors gracefully:

- **Insufficient Cash** - Prevents buying more than cash allows
- **No Position** - Prevents selling stocks you don't own
- **Insufficient Shares** - Prevents selling more shares than owned
- **Price Fetch Errors** - Falls back gracefully if current price unavailable

---

## Best Practices

1. **Start with Reset** - Reset account to $100k when starting new strategy
2. **Track Daily P&L** - Check account status daily to monitor performance
3. **Use Stop Loss/Take Profit** - Set limits when entering positions
4. **Review Transactions** - Regularly review transaction history
5. **Paper Trade First** - Test strategies in paper trading before real money

---

## Future Enhancements

- [ ] Daily P&L charts and graphs
- [ ] Performance analytics (win rate, avg P&L per trade)
- [ ] Multiple paper trading accounts (for different strategies)
- [ ] Portfolio allocation tracking
- [ ] Comparison with market benchmarks
- [ ] Export transaction history to CSV

---

## Summary

Paper trading provides a complete virtual trading environment where you can:
- ✅ Practice trading without risk
- ✅ Track performance with real-time P&L
- ✅ Test strategies and learn from mistakes
- ✅ Execute trades from the screener and other views
- ✅ Monitor cash balance and portfolio value

All without risking real money! 🎯

