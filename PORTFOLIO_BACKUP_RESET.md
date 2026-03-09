# Portfolio Backup & Reset Guide

## Overview

The portfolio reset functionality now automatically creates a backup of your portfolio database before resetting, so you can keep all your trading records.

## How It Works

### Automatic Backup on Reset

When you reset the portfolio, the system:
1. **Creates a backup** of `portfolio.db` with a timestamp
2. **Saves it** to `portfolio_backups/portfolio_backup_YYYYMMDD_HHMMSS.db`
3. **Resets** the portfolio (clears positions and transactions)
4. **Resets** the account balance to starting capital

### Backup Location

**Directory:** `portfolio_backups/`  
**Filename Format:** `portfolio_backup_YYYYMMDD_HHMMSS.db`

**Example:**
```
portfolio_backups/
  ├── portfolio_backup_20240225_143022.db
  ├── portfolio_backup_20240226_091545.db
  └── portfolio_backup_20240301_120030.db
```

## API Endpoints

### Reset Portfolio (with Auto-Backup)

**Endpoint:** `POST /midas/paper_trade/reset`

**Request Body:**
```json
{
  "starting_capital": 100000.0,  // Optional, defaults to $100,000
  "create_backup": true          // Optional, defaults to true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Paper trading account reset with $100,000.00 | Backup saved to: portfolio_backups/portfolio_backup_20240225_143022.db",
  "starting_capital": 100000.0,
  "cash_balance": 100000.0,
  "backup_created": true,
  "backup_path": "portfolio_backups/portfolio_backup_20240225_143022.db"
}
```

### List Backups

**Endpoint:** `GET /midas/paper_trade/backups`

**Response:**
```json
{
  "backups": [
    {
      "filename": "portfolio_backup_20240225_143022.db",
      "path": "portfolio_backups/portfolio_backup_20240225_143022.db",
      "size_bytes": 245760,
      "size_mb": 0.23,
      "created_at": "2024-02-25T14:30:22",
      "created_at_readable": "2024-02-25 14:30:22"
    },
    {
      "filename": "portfolio_backup_20240226_091545.db",
      "path": "portfolio_backups/portfolio_backup_20240226_091545.db",
      "size_bytes": 327680,
      "size_mb": 0.31,
      "created_at": "2024-02-26T09:15:45",
      "created_at_readable": "2024-02-26 09:15:45"
    }
  ],
  "count": 2,
  "backup_directory": "portfolio_backups"
}
```

## What Gets Backed Up

The backup includes **all tables** in `portfolio.db`:

### Paper Trading Tables
- `paper_portfolio` - Current paper trading positions
- `paper_transactions` - Paper trading transaction history
- `paper_account` - Paper trading account balance and P&L

### Regular Portfolio Tables (if used)
- `portfolio` - Regular portfolio positions
- `transactions` - Regular transaction history

## What Gets Reset

When you reset:
- ✅ **Cleared:** All positions in `paper_portfolio`
- ✅ **Cleared:** All transactions in `paper_transactions`
- ✅ **Reset:** Account balance to starting capital (default: $100,000)
- ✅ **Preserved:** All data backed up before reset

## Usage Examples

### Reset via API

**cURL:**
```bash
curl -X POST http://localhost:8000/midas/paper_trade/reset \
  -H "Content-Type: application/json" \
  -d '{"starting_capital": 100000.0}'
```

**Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/midas/paper_trade/reset",
    json={"starting_capital": 100000.0}
)
result = response.json()
print(f"Reset successful! Backup: {result['backup_path']}")
```

### List Backups via API

**cURL:**
```bash
curl http://localhost:8000/midas/paper_trade/backups
```

**Python:**
```python
import requests

response = requests.get("http://localhost:8000/midas/paper_trade/backups")
backups = response.json()
print(f"Found {backups['count']} backups")
for backup in backups['backups']:
    print(f"  - {backup['filename']} ({backup['size_mb']} MB) - {backup['created_at_readable']}")
```

## Restoring from Backup

To restore a backup, you can:

1. **Stop the server** (if running)
2. **Copy the backup file** over the current database:
   ```bash
   cp portfolio_backups/portfolio_backup_20240225_143022.db portfolio.db
   ```
3. **Restart the server**

Or use SQLite tools to restore specific tables.

## Notes

- Backups are **automatic** - created every time you reset
- Backups are **timestamped** - easy to identify when they were created
- Backups are **complete** - include all portfolio data
- Backups are **persistent** - stored in `portfolio_backups/` directory
- You can **disable backup** by setting `create_backup: false` in the request (not recommended)

## File Structure

```
MidasAnalytics/
  ├── portfolio.db                    # Current active database
  └── portfolio_backups/              # Backup directory
      ├── portfolio_backup_20240225_143022.db
      ├── portfolio_backup_20240226_091545.db
      └── ...
```

## Safety Features

- ✅ Backup is created **before** any data is deleted
- ✅ If backup fails, reset will still proceed (but you'll be warned)
- ✅ Multiple backups can exist (each reset creates a new one)
- ✅ Backups are never automatically deleted (you manage them manually)
