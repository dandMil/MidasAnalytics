# Transaction API Implementation

## New Endpoint: `/midas/do_transaction`

### Overview
Implements a unified transaction endpoint that handles both buy and sell operations with stop loss and take profit levels.

### Endpoint Details

**URL:** `POST /midas/do_transaction`

**Request Body:**
```json
{
  "ticker": "AAPL",
  "shares": 10,           // Positive for buy, negative for sell
  "current_price": 150.00,
  "stop_loss": 145.00,
  "take_profit": 160.00
}
```

**Response (Buy):**
```json
{
  "success": true,
  "message": "Purchased 10 shares of AAPL at $150.00",
  "ticker": "AAPL",
  "shares": 10,
  "price": 150.00,
  "stop_loss": 145.00,
  "take_profit": 160.00,
  "transaction_type": "BUY",
  "recommendation": {
    // Trade recommendation object
  }
}
```

**Response (Sell):**
```json
{
  "success": true,
  "message": "Sold 10 shares of AAPL at $150.00 | P&L: $50.00 (+3.33%)",
  "ticker": "AAPL",
  "shares": 10,
  "price": 150.00,
  "stop_loss": 145.00,
  "take_profit": 160.00,
  "transaction_type": "SELL"
}
```

**Error Response (Insufficient Shares):**
```json
{
  "success": false,
  "message": "Cannot sell 10 shares - only 5 shares available",
  "error": "INSUFFICIENT_SHARES",
  "available_shares": 5
}
```

## Implementation Details

### Database Schema

#### Updated Portfolio Table
```sql
CREATE TABLE portfolio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT UNIQUE,
    shares INTEGER,
    price REAL,
    stop_loss REAL,          -- NEW
    take_profit REAL,        -- NEW
    type TEXT,
    updated_at TEXT
)
```

#### New Transactions Table
```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT,
    shares INTEGER,
    price REAL,
    stop_loss REAL,
    take_profit REAL,
    transaction_type TEXT,   -- "BUY" or "SELL"
    created_at TEXT
)
```

### Features

#### Buy Transactions
- ✅ Creates new position or adds to existing
- ✅ Calculates dollar-cost average for existing positions
- ✅ Stores stop_loss and take_profit
- ✅ Generates trade recommendation
- ✅ Records transaction history

#### Sell Transactions
- ✅ Validates sufficient shares
- ✅ Calculates P&L (profit/loss)
- ✅ Supports partial or full position closure
- ✅ Removes position when fully sold
- ✅ Records transaction history

#### Error Handling
- ✅ Validates required fields
- ✅ Checks for sufficient shares before selling
- ✅ Handles missing positions
- ✅ Returns descriptive error messages

### Code Structure

#### Files Modified
1. **`services/portfolio_service.py`**
   - Added `do_transaction()` function
   - Updated database schema
   - Added migration logic for backward compatibility

2. **`app.py`**
   - Added `/midas/do_transaction` endpoint
   - Imported `do_transaction` function
   - Added request validation

### Usage Examples

#### Buy Shares
```javascript
const response = await fetch("/midas/do_transaction", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    ticker: "AAPL",
    shares: 10,              // Positive = buy
    current_price: 150.00,
    stop_loss: 145.00,
    take_profit: 160.00
  })
});
```

#### Sell Shares
```javascript
const response = await fetch("/midas/do_transaction", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    ticker: "AAPL",
    shares: -5,              // Negative = sell
    current_price: 155.00,
    stop_loss: 145.00,
    take_profit: 160.00
  })
});
```

### Business Logic

#### Buy Logic
1. Check if position exists
2. If exists: Calculate new average price (dollar-cost average)
3. If new: Create new position at current_price
4. Update stop_loss and take_profit
5. Record transaction

#### Sell Logic
1. Validate position exists
2. Validate sufficient shares
3. Calculate P&L based on average cost basis
4. Update or remove position
5. Record transaction with P&L

#### Dollar-Cost Averaging
When buying additional shares of an existing position:
```
New Average Price = (Old Price × Old Shares + New Price × New Shares) / Total Shares
```

### Migration Notes

- ✅ Backward compatible with existing database
- ✅ Automatically adds `stop_loss` and `take_profit` columns if missing
- ✅ Creates `transactions` table for history tracking
- ✅ Existing portfolio data remains intact

### Testing

#### Test Cases
1. ✅ Buy new position
2. ✅ Buy additional shares (dollar-cost averaging)
3. ✅ Sell partial position
4. ✅ Sell full position (removes from portfolio)
5. ✅ Sell with insufficient shares (error)
6. ✅ Sell non-existent position (error)
7. ✅ Validate required fields

### Future Enhancements

Potential improvements:
- [ ] Transaction history endpoint
- [ ] Position P&L tracking
- [ ] Stop loss/take profit monitoring
- [ ] Batch transactions
- [ ] Transaction validation rules
- [ ] Audit trail logging

