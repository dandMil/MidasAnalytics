# Portfolio Reset Instructions

If you're still seeing the old portfolio after resetting, follow these steps:

## Step 1: Run the Direct Reset Script

```bash
cd /Users/dandmil/Desktop/Projects/MidasAnalytics
python3 direct_reset.py
```

This will:
- Show you what's currently in the database
- Create a backup
- Clear all portfolio tables
- Reset account to $100,000

## Step 2: Restart Your Backend Server

If your FastAPI server is running, restart it to ensure it picks up the database changes:

```bash
# Stop the server (Ctrl+C), then restart:
cd /Users/dandmil/Desktop/Projects/MidasAnalytics
python3 -m uvicorn app:app --reload
```

## Step 3: Clear Frontend Cache

The frontend may be caching the portfolio data. Do a hard refresh:

- **Mac**: `Cmd + Shift + R`
- **Windows/Linux**: `Ctrl + Shift + R`

Or clear your browser cache completely.

## Step 4: Verify the Reset

Check the API endpoint directly:

```bash
curl http://localhost:8000/midas/paper_trade/portfolio
```

This should return an empty array `[]` if the reset worked.

## Step 5: If Still Not Working

If you still see positions, check:

1. **Multiple database files?**
   ```bash
   find . -name "*.db" -type f
   ```

2. **Database location?**
   The database should be at: `/Users/dandmil/Desktop/Projects/MidasAnalytics/portfolio.db`

3. **Check what the API returns:**
   ```bash
   curl http://localhost:8000/midas/paper_trade/portfolio | python3 -m json.tool
   ```

4. **Check database directly:**
   ```bash
   sqlite3 portfolio.db "SELECT COUNT(*) FROM paper_portfolio;"
   ```

## Alternative: Use the API Endpoint

You can also reset via the API (if server is running):

```bash
curl -X POST http://localhost:8000/midas/paper_trade/reset \
  -H "Content-Type: application/json" \
  -d '{"starting_capital": 100000.0}'
```

Then refresh your browser!
