# Midas Dashboard - Implementation Plan

## Overview
Complete Stock & Crypto Analytics Dashboard with multiple views and backtesting capabilities.

---

## Current Status

### ✅ Already Implemented
1. **Top Movers** - Basic backend and frontend exist
2. **Portfolio** - Basic view exists (needs paper trading integration)
3. **Screener** - Fully functional with filters, ADR/RSI ranking
4. **Research** - Basic search and technical indicators
5. **Shorts** - Reddit scraper and basic view exist
6. **Backtesting Engine** - Core engine exists (`services/backtesting/backtest_engine.py`)

### 🔧 Needs Enhancement

#### 1. Top Movers View
**Current:** Shows basic gainers/losers
**Needs:**
- ✅ Add technical indicators (RSI, MACD, Stochastic, etc.)
- ✅ Add bullish/bearish signals
- ✅ Show ADR, volume metrics
- ✅ Link to paper trading

**Backend:** Enhance `fetch_top_movers()` to include technical indicators
**Frontend:** Enhance `TopMoverFetcher.tsx` to display indicators and signals

---

#### 2. Portfolio View
**Current:** Shows recommendations, basic portfolio
**Needs:**
- ✅ Integrate paper trading (`getPaperPortfolio()`, `getPaperAccount()`)
- ✅ Show paper trading positions with P&L
- ✅ Display stop loss, take profit
- ✅ Show cash balance and total portfolio value
- ✅ Add buy/sell buttons for paper trading

**Frontend:** Enhance `Portfolio.tsx` to show paper trading data

---

#### 3. Research View
**Current:** Basic ticker search with indicators
**Needs:**
- ✅ Add news integration (Polygon news API or alternative)
- ✅ Show company/industry information
- ✅ Add crypto support (already partially there)
- ✅ Enhanced technical analysis display

**Backend:** Add news endpoint, company info endpoint
**Frontend:** Enhance `ResearchView.tsx` with news section

---

#### 4. Shorts View
**Current:** Reddit scraper exists, basic view
**Needs:**
- ✅ Add technical indicators for each ticker (like other views)
- ✅ Show bullish/bearish signals
- ✅ Display volume, price change
- ✅ Better formatting and organization

**Backend:** Enhance `/fetch_shorts` to include technical indicators
**Frontend:** Enhance `ShortsSqueezeView.tsx` to match other views

---

#### 5. Backtesting View (NEW)
**Current:** Backend engine exists
**Needs:**
- ✅ Frontend UI to:
  - Select multiple strategies
  - Choose time range (date picker)
  - Select tickers or use screener results
  - Display backtest results
  - Compare strategy performance
- ✅ Backend endpoints for running backtests
- ✅ Results visualization (charts, metrics)

**New Files Needed:**
- `src/components/BacktestingView.tsx`
- Backend endpoint: `/midas/backtest/run`
- Backend endpoint: `/midas/backtest/strategies`

---

## Implementation Priority

### Phase 1: Core Enhancements (High Priority)
1. **Top Movers** - Add indicators & signals ✅
2. **Portfolio** - Paper trading integration ✅
3. **Shorts** - Add indicators & signals ✅

### Phase 2: Research & News (Medium Priority)
4. **Research** - News integration
5. **Research** - Company/industry info

### Phase 3: Backtesting (High Priority - New Feature)
6. **Backtesting View** - Complete implementation

---

## Technical Details

### Backend Endpoints Needed

#### Top Movers Enhancement
```
GET /midas/asset/top_movers?mover=gainers&include_indicators=true
```
Returns: Top movers with technical indicators and signals

#### Research Enhancement
```
GET /midas/asset/news/{ticker}
GET /midas/asset/company_info/{ticker}
```

#### Shorts Enhancement
```
GET /midas/shorts/enriched?lookback=7
```
Returns: Reddit shorts with technical indicators

#### Backtesting (New)
```
GET /midas/backtest/strategies
POST /midas/backtest/run
  {
    "strategies": ["momentum", "mean_reversion"],
    "tickers": ["AAPL", "TSLA"],
    "start_date": "2024-01-01",
    "end_date": "2024-12-01",
    "initial_capital": 100000
  }
GET /midas/backtest/results/{backtest_id}
```

---

### Frontend Components Needed

#### New Components
- `BacktestingView.tsx` - Main backtesting interface
- `BacktestResults.tsx` - Display backtest results
- `NewsSection.tsx` - News display component
- `CompanyInfo.tsx` - Company/industry info display

#### Enhanced Components
- `TopMoverFetcher.tsx` - Add indicators display
- `Portfolio.tsx` - Add paper trading UI
- `ShortsSqueezeView.tsx` - Add indicators display
- `ResearchView.tsx` - Add news and company info

---

## Data Flow

### Top Movers Enhanced Flow
```
User → Top Movers View
  ↓
Frontend: Fetch top movers
  ↓
Backend: GET /midas/asset/top_movers
  ↓
Backend: For each ticker, fetch technical indicators
  ↓
Backend: Calculate bullish/bearish signals
  ↓
Frontend: Display with indicators and signals
  ↓
User: Can click to trade (paper trading)
```

### Portfolio Paper Trading Flow
```
User → Portfolio View
  ↓
Frontend: Fetch paper portfolio + account
  ↓
Backend: GET /midas/paper_trade/portfolio
Backend: GET /midas/paper_trade/account
  ↓
Frontend: Display positions, P&L, cash balance
  ↓
User: Can buy/sell (paper trading)
```

### Backtesting Flow
```
User → Backtesting View
  ↓
User: Select strategies, tickers, date range
  ↓
Frontend: POST /midas/backtest/run
  ↓
Backend: Run backtest engine for each strategy
  ↓
Backend: Return results (metrics, trades, performance)
  ↓
Frontend: Display results in charts and tables
  ↓
User: Compare strategies, analyze performance
```

---

## File Structure

### Backend (MidasAnalytics)
```
services/
  ├── top_mover_service.py (enhance)
  ├── portfolio_service.py (already has paper trading)
  ├── paper_trading_service.py (already exists)
  ├── reddit/reddit_scraper.py (enhance)
  ├── backtesting/
  │   ├── backtest_engine.py (exists)
  │   ├── backtest_service.py (new - orchestrator)
  │   └── strategies/ (exists)
  ├── news_service.py (new)
  └── company_info_service.py (new)
```

### Frontend (midas-dashboard)
```
src/
  ├── components/
  │   ├── TopMoverFetcher.tsx (enhance)
  │   ├── Portfolio.tsx (enhance)
  │   ├── ShortsSqueezeView.tsx (enhance)
  │   ├── ResearchView.tsx (enhance)
  │   ├── BacktestingView.tsx (new)
  │   ├── BacktestResults.tsx (new)
  │   ├── NewsSection.tsx (new)
  │   └── CompanyInfo.tsx (new)
  └── services/
      └── api.tsx (add new endpoints)
```

---

## Next Steps

1. ✅ Create this plan
2. ⏳ Enhance Top Movers with indicators
3. ⏳ Integrate paper trading into Portfolio
4. ⏳ Enhance Shorts view with indicators
5. ⏳ Add news to Research view
6. ⏳ Build Backtesting UI

---

## Notes

- Paper trading service already fully implemented
- Technical indicator calculation already exists
- Backtesting engine already exists, needs UI
- All views should have consistent look/feel
- All views should support paper trading actions

