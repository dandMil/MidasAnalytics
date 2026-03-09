# Quick Portfolio Reset Guide

If the portfolio is still showing positions, try these steps in order:

## Method 1: Use the API Endpoint (if server is running)

```bash
curl -X POST http://localhost:8000/midas/paper_trade/reset \
  -H "Content-Type: application/json" \
  -d '{"starting_capital": 100000.0}'
```

## Method 2: Run Python Reset Script

```bash
cd /Users/dandmil/Desktop/Projects/MidasAnalytics
python3 force_clear_portfolio.py
```

## Method 3: Direct Python Call

```bash
cd /Users/dandmil/Desktop/Projects/MidasAnalytics
python3 -c "
from services.paper_trading_service import reset_paper_account
result = reset_paper_account(starting_capital=100000.0, create_backup=True)
print(result)
"
```

## Method 4: Manual SQL Reset (if all else fails)

```bash
sqlite3 portfolio.db << EOF
DELETE FROM paper_portfolio;
DELETE FROM paper_transactions;
DELETE FROM portfolio;
DELETE FROM transactions;
INSERT OR REPLACE INTO paper_account 
(starting_capital, cash_balance, portfolio_value, unrealized_pnl, realized_pnl, total_pnl, last_updated, trading_date)
VALUES (100000.0, 100000.0, 100000.0, 0.0, 0.0, 0.0, datetime('now'), date('now'));
EOF
```

## After Reset:

1. **Restart your backend server** (if running)
   ```bash
   # Stop server (Ctrl+C), then:
   python3 -m uvicorn app:app --reload
   ```

2. **Hard refresh your browser**
   - Mac: `Cmd + Shift + R`
   - Windows: `Ctrl + Shift + R`

3. **Verify the reset worked:**
   ```bash
   python3 verify_reset.py
   ```

4. **Check API endpoint:**
   ```bash
   curl http://localhost:8000/midas/paper_trade/portfolio
   ```
   Should return: `[]`
