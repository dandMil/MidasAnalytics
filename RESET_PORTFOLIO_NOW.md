# Reset Portfolio - Quick Guide

## Option 1: Via API (Recommended)

If your server is running, use the API endpoint:

```bash
curl -X POST http://localhost:8000/midas/paper_trade/reset \
  -H "Content-Type: application/json" \
  -d '{"starting_capital": 100000.0}'
```

Or use Python:
```python
import requests
response = requests.post(
    "http://localhost:8000/midas/paper_trade/reset",
    json={"starting_capital": 100000.0}
)
print(response.json())
```

## Option 2: Run Script Directly

```bash
cd /Users/dandmil/Desktop/Projects/MidasAnalytics
python3 reset_portfolio_now.py
```

## Option 3: Python Interactive

```python
from services.paper_trading_service import reset_paper_account

result = reset_paper_account(starting_capital=100000.0, create_backup=True)
print(result)
```

## What Happens

1. ✅ **Backup Created**: `portfolio_backups/portfolio_backup_YYYYMMDD_HHMMSS.db`
2. ✅ **Positions Cleared**: All positions removed from `paper_portfolio`
3. ✅ **Transactions Cleared**: All transactions removed from `paper_transactions`
4. ✅ **Account Reset**: Cash balance reset to $100,000

## Verify Reset

Check your portfolio:
```bash
curl http://localhost:8000/midas/paper_trade/portfolio
```

Check backups:
```bash
curl http://localhost:8000/midas/paper_trade/backups
```
