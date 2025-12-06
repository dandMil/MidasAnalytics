# Database Tracking for Buy/Sell Transactions

## Database Overview

**Database File:** `portfolio.db` (SQLite database)

The system uses **two main tables** to track all transactions:

---

## Table 1: `portfolio` - Current Positions

Stores your **current holdings** (what you currently own).

### Schema
```sql
CREATE TABLE portfolio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT UNIQUE,          -- Stock symbol (e.g., "AAPL")
    shares INTEGER,               -- Number of shares owned
    price REAL,                   -- Average cost per share (dollar-cost averaged)
    stop_loss REAL,               -- Stop loss price
    take_profit REAL,             -- Take profit price
    type TEXT,                    -- Asset type (usually "stock")
    updated_at TEXT               -- Last update timestamp
)
```

### Purpose
- **Snapshot of current holdings** at any point in time
- **One row per ticker** (UNIQUE constraint)
- When you buy more shares, it updates the existing row
- When you sell all shares, the row is deleted
- Stores average cost basis (dollar-cost averaged if you buy multiple times)

### Example Data
```
| id | ticker | shares | price | stop_loss | take_profit | type  | updated_at          |
|----|--------|--------|-------|-----------|-------------|-------|---------------------|
| 1  | AAPL   | 10     | 150.0 | 145.0     | 160.0       | stock | 2024-10-25T12:00:00|
| 2  | TSLA   | 5      | 200.0 | 190.0     | 220.0       | stock | 2024-10-25T13:00:00|
```

---

## Table 2: `transactions` - Transaction History

Stores **every single transaction** (complete audit trail).

### Schema
```sql
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT,                  -- Stock symbol
    shares INTEGER,               -- Number of shares (positive for buy, negative for sell)
    price REAL,                   -- Price per share at transaction time
    stop_loss REAL,               -- Stop loss set at transaction time
    take_profit REAL,             -- Take profit set at transaction time
    transaction_type TEXT,        -- "BUY" or "SELL"
    created_at TEXT               -- Transaction timestamp
)
```

### Purpose
- **Complete historical record** of all transactions
- **Never deleted** - permanent audit trail
- Every buy and sell is recorded here
- Can reconstruct portfolio history from this table

### Example Data
```
| id | ticker | shares | price | stop_loss | take_profit | transaction_type | created_at          |
|----|--------|--------|-------|-----------|-------------|------------------|---------------------|
| 1  | AAPL   | 10     | 150.0 | 145.0     | 160.0       | BUY              | 2024-10-25T12:00:00|
| 2  | TSLA   | 5      | 200.0 | 190.0     | 220.0       | BUY              | 2024-10-25T13:00:00|
| 3  | AAPL   | 5      | 155.0 | 145.0     | 160.0       | BUY              | 2024-10-25T14:00:00|
| 4  | AAPL   | -3     | 158.0 | 145.0     | 160.0       | SELL             | 2024-10-25T15:00:00|
```

---

## How Transactions Are Recorded

### When You BUY Shares

1. **Update `portfolio` table:**
   - If ticker exists: Update shares and recalculate average price
   - If new ticker: Insert new row
   - Update stop_loss and take_profit

2. **Insert into `transactions` table:**
   - Record with `shares > 0` (positive)
   - `transaction_type = "BUY"`
   - Store price, stop_loss, take_profit, timestamp

### When You SELL Shares

1. **Update `portfolio` table:**
   - Decrease shares count
   - If shares = 0: Delete the row
   - Calculate P&L based on average cost

2. **Insert into `transactions` table:**
   - Record with `shares < 0` (negative)
   - `transaction_type = "SELL"`
   - Store price, P&L calculation, timestamp

---

## Example Transaction Flow

### Scenario: Buying and Selling AAPL

#### Transaction 1: Buy 10 shares @ $150
```sql
-- portfolio table
INSERT INTO portfolio (ticker, shares, price, stop_loss, take_profit, type, updated_at)
VALUES ('AAPL', 10, 150.0, 145.0, 160.0, 'stock', '2024-10-25T12:00:00');

-- transactions table
INSERT INTO transactions (ticker, shares, price, stop_loss, take_profit, transaction_type, created_at)
VALUES ('AAPL', 10, 150.0, 145.0, 160.0, 'BUY', '2024-10-25T12:00:00');
```

#### Transaction 2: Buy 5 more shares @ $155
```sql
-- portfolio table (updates existing row, calculates new average)
UPDATE portfolio 
SET shares = 15, 
    price = 152.0,  -- Dollar-cost averaged: (10*150 + 5*155) / 15
    stop_loss = 145.0, 
    take_profit = 160.0,
    updated_at = '2024-10-25T14:00:00'
WHERE ticker = 'AAPL';

-- transactions table
INSERT INTO transactions (ticker, shares, price, stop_loss, take_profit, transaction_type, created_at)
VALUES ('AAPL', 5, 155.0, 145.0, 160.0, 'BUY', '2024-10-25T14:00:00');
```

#### Transaction 3: Sell 3 shares @ $158
```sql
-- portfolio table (decreases shares, keeps average price)
UPDATE portfolio 
SET shares = 12,  -- 15 - 3
    updated_at = '2024-10-25T15:00:00'
WHERE ticker = 'AAPL';

-- transactions table
INSERT INTO transactions (ticker, shares, price, stop_loss, take_profit, transaction_type, created_at)
VALUES ('AAPL', -3, 158.0, 145.0, 160.0, 'SELL', '2024-10-25T15:00:00');
```

#### Transaction 4: Sell remaining 12 shares @ $160
```sql
-- portfolio table (position closed, row deleted)
DELETE FROM portfolio WHERE ticker = 'AAPL';

-- transactions table
INSERT INTO transactions (ticker, shares, price, stop_loss, take_profit, transaction_type, created_at)
VALUES ('AAPL', -12, 160.0, 145.0, 160.0, 'SELL', '2024-10-25T16:00:00');
```

**Result:** After all transactions, `portfolio` table is empty (position closed), but `transactions` table has complete history of all 4 transactions.

---

## Data Integrity

### Portfolio Table
- ✅ **UNIQUE constraint** on ticker - one row per stock
- ✅ **Average price** calculated for multiple purchases
- ✅ **Automatic cleanup** when position closed

### Transactions Table
- ✅ **Immutable** - never deleted or updated
- ✅ **Complete audit trail** - every transaction recorded
- ✅ **Can reconstruct** portfolio at any point in time

---

## Querying the Database

### Get Current Portfolio
```python
from services.portfolio_service import fetch_portfolio
portfolio = fetch_portfolio()
```

### Query Transactions (would need to add function)
```sql
-- Get all transactions for a ticker
SELECT * FROM transactions WHERE ticker = 'AAPL' ORDER BY created_at;

-- Get all buys
SELECT * FROM transactions WHERE transaction_type = 'BUY';

-- Get transaction history
SELECT * FROM transactions ORDER BY created_at DESC;
```

---

## Database File Location

**File:** `/Users/dandmil/Desktop/Projects/MidasAnalytics/portfolio.db`

- SQLite database (file-based, no server needed)
- Automatically created on first transaction
- Tables created automatically via `initialize_portfolio_db()`
- Schema migration handles adding new columns

---

## Summary

✅ **Yes, there IS a database** (`portfolio.db`)

✅ **Two tables track everything:**
- `portfolio` = Current holdings (what you own now)
- `transactions` = Complete history (every buy/sell ever)

✅ **Every transaction is recorded:**
- Both tables updated on every buy/sell
- Complete audit trail maintained
- Can reconstruct portfolio at any point in time

✅ **Database is persistent:**
- Data survives server restarts
- SQLite file-based database
- Automatic schema management

