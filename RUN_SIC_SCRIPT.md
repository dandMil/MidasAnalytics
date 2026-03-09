# How to Run SIC Ticker Scripts

## Quick Start

### Option 1: Simple Script (Recommended - Uses Existing Ticker Universe)

```bash
# 1. Navigate to project directory
cd /Users/dandmil/Desktop/Projects/MidasAnalytics

# 2. Activate virtual environment (if you have one)
source .venv/bin/activate

# 3. Set Polygon API key (add to .env file or export)
# Option A: Add to .env file (recommended)
# echo "POLYGON_API_KEY=your_key_here" >> .env
# Option B: Export for this session
# export POLYGON_API_KEY="your_polygon_api_key_here"

# 4. Run the script
python3 scripts/get_tickers_by_sic_simple.py
```

### Option 2: Full Script (Fetches All Tickers from Polygon)

```bash
# 1. Navigate to project directory
cd /Users/dandmil/Desktop/Projects/MidasAnalytics

# 2. Activate virtual environment
source .venv/bin/activate

# 3. Set Polygon API key (add to .env file or export)
# Option A: Add to .env file (recommended)
# echo "POLYGON_API_KEY=your_key_here" >> .env
# Option B: Export for this session
# export POLYGON_API_KEY="your_polygon_api_key_here"

# 4. Run the full script
python3 scripts/fetch_tickers_by_sic.py
```

---

## Detailed Instructions

### Prerequisites

1. **Python 3.7+** installed
2. **Virtual environment** (optional but recommended)
3. **Dependencies installed**:
   ```bash
   pip install -r requirements.txt
   ```
   Or install just what's needed:
   ```bash
   pip install requests tqdm
   ```

4. **Polygon API Key** (optional but recommended for better results)
   - Get one at: https://polygon.io/
   - Free tier: 5 calls/minute
   - Pro tier: 200 calls/minute (recommended)

5. **Ticker Universe File** (for simple script)
   - Should exist at: `data/us_stock_universe.csv`
   - If missing, run: `python3 scripts/fetch_ticker_universe.py` first

### Step-by-Step

#### 1. Open Terminal

Open your terminal application (Terminal.app on Mac, or your preferred terminal).

#### 2. Navigate to Project Directory

```bash
cd /Users/dandmil/Desktop/Projects/MidasAnalytics
```

#### 3. Activate Virtual Environment (if you have one)

```bash
# Check if .venv exists
ls -la .venv

# If it exists, activate it
source .venv/bin/activate

# You should see (.venv) in your prompt
```

#### 4. Install Dependencies (if not already installed)

```bash
pip install requests tqdm
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

#### 5. Set API Key (Choose One Method)

**Option A: Use .env file (Recommended)**
```bash
# Create or edit .env file in project root
echo "POLYGON_API_KEY=your_api_key_here" >> .env

# Or edit .env file manually:
# POLYGON_API_KEY=your_api_key_here
```

The script automatically loads from `.env` file if `python-dotenv` is installed (it's in requirements.txt).

**Option B: Set for current session**
```bash
export POLYGON_API_KEY="your_api_key_here"
```

**Option C: Inline (one-time use)**
```bash
POLYGON_API_KEY="your_api_key_here" python3 scripts/get_tickers_by_sic_simple.py
```

#### 6. Run the Script

**Simple Script (Recommended):**
```bash
python3 scripts/get_tickers_by_sic_simple.py
```

**Full Script:**
```bash
python3 scripts/fetch_tickers_by_sic.py
```

---

## Script Options

### Simple Script Options

Edit the script to change options:

```python
# In scripts/get_tickers_by_sic_simple.py, line ~251:

# For testing (first 100 tickers only)
classified = get_tickers_by_sic(use_polygon=True, limit=100)

# For full run (all tickers)
classified = get_tickers_by_sic(use_polygon=True, limit=None)
```

### Full Script Options

The full script automatically processes all tickers. No options needed.

---

## Expected Output

### Progress Bar Display

You'll see progress bars like:

```
🚀 Starting SIC code classification...

============================================================
📊 GETTING TICKERS BY SIC CODES
============================================================
📂 Loading ticker universe...
✅ Loaded 11802 tickers

🔍 Classifying tickers by SIC code...
   Using Polygon API: Yes
------------------------------------------------------------
Processing tickers: 45%|████████████          | 5310/11802 [12:34<15:23, 7.1ticker/s] | SIC: 1234 | Tech:456 Energy:234 Health:123
```

### Final Output

```
------------------------------------------------------------
✅ Complete!
📊 Processed: 11802 tickers
📊 Found SIC codes: 8500
📊 Tech: 2345 tickers
📊 Energy: 567 tickers
📊 Healthcare: 1234 tickers

💾 Saving results...
✅ Saved 2345 tech tickers to data/sic_tickers/tech_tickers_by_sic.csv
✅ Saved 567 energy tickers to data/sic_tickers/energy_tickers_by_sic.csv
✅ Saved 1234 healthcare tickers to data/sic_tickers/healthcare_tickers_by_sic.csv

✅ DONE!
📊 Total tickers classified: 4146
```

---

## Output Files

The scripts create CSV files in `data/sic_tickers/`:

- `tech_tickers_by_sic.csv` - Technology/AI tickers
- `energy_tickers_by_sic.csv` - Energy sector tickers
- `healthcare_tickers_by_sic.csv` - Healthcare/Biotech tickers

Each CSV contains:
- `ticker` - Stock symbol
- `name` - Company name
- `sic_code` - SIC code
- `primary_exchange` - Exchange (XNAS, XNYS, etc.)
- `type` - Security type
- `cik` - SEC CIK number

---

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'requests'"

**Solution:**
```bash
pip install requests tqdm
```

### Error: "POLYGON_API_KEY not found!"

**Solution:**
```bash
# Option 1: Add to .env file (recommended)
echo "POLYGON_API_KEY=your_api_key_here" >> .env

# Option 2: Export for current session
export POLYGON_API_KEY="your_api_key_here"

# Option 3: Install python-dotenv if not installed
pip install python-dotenv
```

Or the script will use SEC EDGAR API (slower but free) if no Polygon key is found.

### Error: "Ticker universe file not found"

**Solution:**
```bash
# First, fetch the ticker universe
python3 scripts/fetch_ticker_universe.py
```

### Error: "Rate limit hit"

**Solution:**
- The script automatically waits and retries
- For faster processing, upgrade to Polygon Pro tier (200 calls/min)
- Or use the simple script which is more efficient

### Progress Bar Not Showing

**Solution:**
```bash
pip install tqdm
```

The script will fall back to simple progress updates if tqdm isn't available.

### Script Running Very Slowly

**Reasons:**
- Processing 11,000+ tickers takes time
- API rate limits (5-200 calls/minute depending on tier)
- Each ticker requires an API call

**Solutions:**
- Use `limit=100` for testing
- Upgrade Polygon API tier
- Run during off-peak hours
- The script shows estimated time remaining

---

## Performance Estimates

### Simple Script (with existing ticker universe)

- **With Polygon API**: ~2-4 hours (Pro tier) or ~8-12 hours (Free tier)
- **With SEC EDGAR only**: ~3-5 hours (10 req/sec limit)
- **Progress**: Real-time progress bar

### Full Script (fetches all tickers first)

- **Fetching tickers**: ~5-10 minutes
- **Classifying**: ~2-4 hours (Pro tier) or ~8-12 hours (Free tier)
- **Total**: ~2.5-4.5 hours (Pro tier)

---

## Tips

1. **Test First**: Use `limit=100` to test the script before full run
2. **Run Overnight**: For full runs, consider running overnight
3. **Check Progress**: The progress bar shows estimated time remaining
4. **Monitor API Usage**: Check your Polygon dashboard for API usage
5. **Save Results**: Results are automatically saved to CSV files

---

## Example Full Command

```bash
# Complete example (API key loaded from .env file automatically)
cd /Users/dandmil/Desktop/Projects/MidasAnalytics && \
source .venv/bin/activate && \
python3 scripts/get_tickers_by_sic_simple.py
```

**Note:** Make sure your `.env` file contains:
```
POLYGON_API_KEY=your_api_key_here
```

Or use inline:
```bash
cd /Users/dandmil/Desktop/Projects/MidasAnalytics && \
source .venv/bin/activate && \
export POLYGON_API_KEY="your_api_key_here" && \
python3 scripts/get_tickers_by_sic_simple.py
```

---

## Next Steps

After running the script:

1. **Check Results**: 
   ```bash
   ls -lh data/sic_tickers/
   ```

2. **View Sample Results**:
   ```bash
   head -20 data/sic_tickers/tech_tickers_by_sic.csv
   ```

3. **Use in Screener**: The CSV files can be used to filter your screener by SIC codes

4. **Update Sector Lists**: Use these tickers to update `SECTOR_TICKERS` in `stock_screener_service.py`
