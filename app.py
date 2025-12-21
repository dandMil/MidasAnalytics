# app.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from openai import OpenAI
import os
import logging
from datetime import datetime
from fastapi import APIRouter, Query
from services.reddit.reddit_scraper import RedditScraper
from routes.daily_summary_routes import router as daily_summary_router
from services.reddit import reddit_scraper as scrapper
from services.top_mover_service import fetch_top_movers
from services.technical_indicator_service import calculate_technical_indicators
from services.portfolio_service import purchase_asset, fetch_portfolio, do_transaction
from services.paper_trading_service import (
    do_paper_transaction, get_paper_account, get_paper_portfolio, 
    get_paper_transactions, reset_paper_account, update_paper_account
)
from services.trade_recommendation_service import (
    calculate_trade_recommendations,
    fetch_trade_recommendation
)
from services.daily_summary.daily_summary_service import generate_daily_summary
from services.historical_screener_service import get_historical_rankings
from services.backtest_trade_simulator import simulate_trade
from services.backtest_session_cache import (
    create_session, get_session, find_session_by_date,
    update_session, add_trade_to_session,
    list_sessions, delete_session, clear_expired_sessions
)

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# FastAPI app setup
app = FastAPI()

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
# app.include_router(daily_summary_router)

# ------------------------------
# GPT / Reddit Endpoints
# ------------------------------

conversation_history = [{
    "role": "system",
    "content": "You are a financial advisor and stock market expert."
}]


@app.post("/query")
async def handle_query(request: Request):
    try:
        data = await request.json()
        query = data.get("query")
        if not query:
            raise HTTPException(status_code=400, detail="Query is required.")

        conversation_history.append({"role": "user", "content": query})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation_history,
            temperature=0.7,
            max_tokens=200
        )

        answer = response.choices[0].message.content.strip()
        conversation_history.append({"role": "assistant", "content": answer})

        return {"query": query, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# @app.get("/fetch_shorts")
# def fetch_shorts_data(lookback: int = 7):
#     try:
#         result = scrapper.scrape_reddit(days_back=lookback)
#         return {"data": list(result)}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@app.get("/fetch_shorts")
def fetch_shorts_data(lookback: int = Query(7, description="Number of days to look back")):
    scraper = RedditScraper(days_back=lookback)
    tickers = scraper.scrape()
    return {"data": tickers}


# ------------------------------
# Midas AI Trading Endpoints
# ------------------------------

@app.get("/midas/asset/top_movers")
def get_top_movers(mover: str = "gainers", include_indicators: bool = False):
    """
    Get top movers (gainers or losers) with optional technical indicators.
    
    Args:
        mover: "gainers" or "losers"
        include_indicators: If True, include technical indicators (RSI, MACD, ADR, signals, etc.)
    """
    try:
        result = fetch_top_movers(mover, include_indicators=include_indicators)
        # Ensure the result is wrapped in a data object as expected by frontend
        if isinstance(result, list):
            return {"data": result}
        elif isinstance(result, dict) and "data" in result:
            return result
        else:
            return {"data": [result] if result else []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/midas/asset/get_signal/{asset}/{type}")
def get_signal(asset: str, type: str):
    try:
        result = calculate_technical_indicators(asset, type)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/midas/asset/purchase")
async def purchase(request: Request):
    try:
        data = await request.json()
        ticker = data.get("name")
        shares = data.get("shares")
        price = data.get("price")
        result = purchase_asset(ticker, shares, price)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/midas/asset/get_portfolio")
def get_portfolio():
    try:
        result = fetch_portfolio()
        # Transform data to match frontend expectations
        if isinstance(result, list):
            transformed_result = []
            for item in result:
                if isinstance(item, dict):
                    # Ensure the structure matches what frontend expects
                    transformed_item = {
                        "ticker": item.get("ticker", ""),
                        "shares": item.get("shares", 0),
                        "currentPrice": item.get("currentPrice", 0),
                        "tradeRecommendation": {
                            "priceEntry": item.get("priceEntry", 0),
                            "stopLoss": item.get("stopLoss", 0),
                            "takeProfit": item.get("takeProfit", 0),
                            "expectedProfit": item.get("expectedProfit", 0),
                            "expectedLoss": item.get("expectedLoss", 0),
                            "strategy": item.get("strategy", "Market Analysis")
                        }
                    }
                    transformed_result.append(transformed_item)
            return transformed_result
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/midas/asset/get_trade_recommendation/{ticker}/{entryPrice}")
def get_trade_recommendation(ticker: str, entryPrice: float):
    try:
        rec = calculate_trade_recommendations(ticker, entryPrice)
        return rec
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/midas/asset/fetch_trade_recommendation/{ticker}")
def get_saved_trade_recommendation(ticker: str):
    try:
        rec = fetch_trade_recommendation(ticker)
        return rec
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/midas/daily_summary")
def get_daily_summary():
    response = generate_daily_summary()
    print(f'RESPONSE FOR DAILY SUMMARY {response}')
    return response


@app.get("/midas/asset/get_watch_list")
def get_watch_list():
    try:
        # For now, return a mock watchlist - this should be implemented with actual data
        watchlist = {
            "AAPL": {"ticker": "AAPL", "name": "Apple Inc.", "price": 150.00},
            "GOOGL": {"ticker": "GOOGL", "name": "Alphabet Inc.", "price": 2800.00},
            "MSFT": {"ticker": "MSFT", "name": "Microsoft Corporation", "price": 300.00},
            "TSLA": {"ticker": "TSLA", "name": "Tesla Inc.", "price": 200.00},
            "AMZN": {"ticker": "AMZN", "name": "Amazon.com Inc.", "price": 3200.00}
        }
        return watchlist
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/midas/asset/repeated_movers")
def get_repeated_movers():
    try:
        # For now, return mock repeated movers data
        repeated_movers = [
            {"ticker": "AAPL", "mentions": 15, "price_change": 2.5},
            {"ticker": "TSLA", "mentions": 12, "price_change": -1.8},
            {"ticker": "NVDA", "mentions": 10, "price_change": 3.2},
            {"ticker": "GOOGL", "mentions": 8, "price_change": 1.1},
            {"ticker": "MSFT", "mentions": 7, "price_change": 0.8}
        ]
        return repeated_movers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/midas/asset/volume")
def get_asset_volume(ticker: str, range_period: str = "1M"):
    try:
        # For now, return mock volume data
        import random
        from datetime import datetime, timedelta
        
        # Generate mock volume data for the specified range
        days = 30 if range_period == "1M" else 7 if range_period == "1W" else 1
        volume_data = []
        
        base_date = datetime.now() - timedelta(days=days)
        for i in range(days):
            date = base_date + timedelta(days=i)
            volume = random.randint(1000000, 10000000)  # Random volume between 1M and 10M
            volume_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "volume": volume
            })
        
        return volume_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/midas/crypto_summary")
def get_crypto_summary():
    try:
        # For now, return mock crypto data
        crypto_data = {
            "top_gainers": [
                {"ticker": "BTC", "close_price": 45000, "price_change": 5.2},
                {"ticker": "ETH", "close_price": 3200, "price_change": 3.8},
                {"ticker": "ADA", "close_price": 0.45, "price_change": 2.1}
            ],
            "top_losers": [
                {"ticker": "DOGE", "close_price": 0.08, "price_change": -2.5},
                {"ticker": "SHIB", "close_price": 0.00001, "price_change": -1.8}
            ],
            "reddit_mentions": [
                {"ticker": "BTC", "mentions": 25},
                {"ticker": "ETH", "mentions": 18},
                {"ticker": "DOGE", "mentions": 12}
            ]
        }
        return crypto_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/midas/purchase_asset")
async def purchase_asset_endpoint(request: Request):
    try:
        data = await request.json()
        ticker = data.get("ticker")
        shares = data.get("shares")
        current_price = data.get("current_price")
        stop_loss = data.get("stop_loss")
        take_profit = data.get("take_profit")
        
        result = purchase_asset(ticker, shares, current_price)
        return {"success": True, "message": f"Purchased {shares} shares of {ticker}", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/midas/sell_asset")
async def sell_asset_endpoint(request: Request):
    try:
        data = await request.json()
        ticker = data.get("ticker")
        shares = data.get("shares")
        current_price = data.get("current_price")
        stop_loss = data.get("stop_loss")
        take_profit = data.get("take_profit")
        
        # For now, just return success - implement actual selling logic
        return {"success": True, "message": f"Sold {shares} shares of {ticker}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/midas/do_transaction")
async def do_transaction_endpoint(request: Request):
    """
    Execute a transaction (buy or sell) with stop loss and take profit.
    
    Request body:
    {
        "ticker": "AAPL",
        "shares": 10,  # Positive for buy, negative for sell
        "current_price": 150.00,
        "stop_loss": 145.00,
        "take_profit": 160.00
    }
    """
    try:
        data = await request.json()
        ticker = data.get("ticker")
        shares = data.get("shares")
        current_price = data.get("current_price")
        stop_loss = data.get("stop_loss")
        take_profit = data.get("take_profit")
        
        # Validate required fields
        if not ticker:
            raise HTTPException(status_code=400, detail="ticker is required")
        if shares is None:
            raise HTTPException(status_code=400, detail="shares is required")
        if current_price is None:
            raise HTTPException(status_code=400, detail="current_price is required")
        
        # Execute transaction
        result = do_transaction(
            ticker=ticker,
            shares=int(shares),
            current_price=float(current_price),
            stop_loss=float(stop_loss) if stop_loss is not None else None,
            take_profit=float(take_profit) if take_profit is not None else None
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transaction failed: {str(e)}")


# ------------------------------
# Paper Trading Endpoints
# ------------------------------

@app.post("/midas/paper_trade/do_transaction")
async def do_paper_transaction_endpoint(request: Request):
    """
    Execute a paper trading transaction (buy or sell) with cash balance tracking.
    
    Request body:
    {
        "ticker": "AAPL",
        "shares": 10,  # Positive for buy, negative for sell
        "current_price": 150.00,
        "stop_loss": 145.00,
        "take_profit": 160.00
    }
    """
    try:
        data = await request.json()
        ticker = data.get("ticker")
        shares = data.get("shares")
        current_price = data.get("current_price")
        stop_loss = data.get("stop_loss")
        take_profit = data.get("take_profit")
        
        # Validate required fields
        if not ticker:
            raise HTTPException(status_code=400, detail="ticker is required")
        if shares is None:
            raise HTTPException(status_code=400, detail="shares is required")
        if current_price is None:
            raise HTTPException(status_code=400, detail="current_price is required")
        
        # Execute paper transaction
        result = do_paper_transaction(
            ticker=ticker,
            shares=int(shares),
            current_price=float(current_price),
            stop_loss=float(stop_loss) if stop_loss is not None else None,
            take_profit=float(take_profit) if take_profit is not None else None
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Paper transaction failed: {str(e)}")


@app.get("/midas/paper_trade/account")
def get_paper_account_endpoint():
    """Get paper trading account status (cash balance, P&L, portfolio value)"""
    try:
        account = update_paper_account()  # Update balances first
        return account
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get account: {str(e)}")


@app.get("/midas/paper_trade/portfolio")
def get_paper_portfolio_endpoint():
    """Get paper trading portfolio positions with current values and P&L"""
    try:
        portfolio = get_paper_portfolio()
        return portfolio
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get portfolio: {str(e)}")


@app.get("/midas/paper_trade/transactions")
def get_paper_transactions_endpoint(limit: int = 50):
    """Get paper trading transaction history"""
    try:
        transactions = get_paper_transactions(limit=limit)
        return transactions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get transactions: {str(e)}")


@app.post("/midas/paper_trade/reset")
async def reset_paper_account_endpoint(request: Request):
    """Reset paper trading account (clear all positions and reset to starting capital)"""
    try:
        data = await request.json() if request.body else {}
        starting_capital = data.get("starting_capital", 100000.0)
        
        result = reset_paper_account(starting_capital=float(starting_capital))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset account: {str(e)}")


@app.get("/midas/asset/stock_screener")
def get_stock_screener(
    sector: str = "all",  # "tech", "bio", "finance", "energy", "all"
    min_1m_performance: float = 10.0,
    min_3m_performance: float = 20.0,
    min_6m_performance: float = 30.0,
    max_1m_performance: float = None,  # Optional max performance filters
    max_3m_performance: float = None,
    max_6m_performance: float = None,
    min_price: float = 1.0,
    max_price: float = 50.0,
    min_rsi: float = 0.0,
    max_rsi: float = 100.0,
    min_adr: float = None,  # Optional ADR filters
    max_adr: float = None,
    rsi_signal: str = "all",  # "all", "oversold", "overbought", "neutral"
    sort_by: str = "adr",  # "adr", "rsi", "performance_1m", "performance_3m", "performance_6m"
    sort_order: str = "desc",  # "asc" or "desc"
    limit: int = 50,
    use_sample: bool = False,  # Set to true to sample (faster but less accurate). Default processes ALL tickers for true rankings.
    sample_size: int = 3000  # Number of stocks to sample if use_sample=true
):
    """
    Stock screener with automatic checkpoint/resume capability.
    Automatically checks for existing progress and resumes if available.
    Uses cache when available, only fetches new data when needed.
    """
    try:
        from services.stock_screener_service import screen_stocks
        
        filters = {
            "sector": sector,
            "min_1m_performance": min_1m_performance,
            "min_3m_performance": min_3m_performance,
            "min_6m_performance": min_6m_performance,
            "max_1m_performance": max_1m_performance,
            "max_3m_performance": max_3m_performance,
            "max_6m_performance": max_6m_performance,
            "min_price": min_price,
            "max_price": max_price,
            "min_rsi": min_rsi,
            "max_rsi": max_rsi,
            "min_adr": min_adr,
            "max_adr": max_adr,
            "rsi_signal": rsi_signal,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "limit": limit,
            "use_sample": use_sample,
            "sample_size": sample_size
        }
        
        results = screen_stocks(filters)
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/midas/asset/available_sectors")
def get_available_sectors():
    try:
        from services.stock_screener_service import get_available_sectors
        sectors = get_available_sectors()
        return sectors
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/midas/asset/universe_stats")
def get_universe_stats():
    try:
        from services.ticker_universe_service import ticker_universe
        stats = ticker_universe.get_universe_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/midas/asset/screener_info")
def get_screener_info():
    """Get information about the stock screener's universe and capabilities"""
    try:
        from services.ticker_universe_service import ticker_universe
        from services.stock_screener_service import SECTOR_TICKERS
        
        # Get universe stats
        universe_stats = ticker_universe.get_universe_stats()
        
        # Get available sectors
        available_sectors = {}
        for sector, tickers in SECTOR_TICKERS.items():
            available_sectors[sector] = {
                "name": sector.title(),
                "ticker_count": len(tickers),
                "sample_tickers": tickers[:5]  # Show first 5 as examples
            }
        
        return {
            "universe": {
                "total_tickers": universe_stats.get("total_tickers", 0),
                "exchanges": universe_stats.get("exchanges", {}),
                "types": universe_stats.get("types", {}),
                "last_updated": universe_stats.get("last_updated"),
                "screener_limit": 2000,  # Current limit for performance
                "coverage_percentage": round((2000 / universe_stats.get("total_tickers", 1)) * 100, 1)
            },
            "sectors": available_sectors,
            "capabilities": {
                "performance_filtering": True,
                "price_range_filtering": True,
                "rsi_filtering": True,
                "technical_analysis": True,
                "adr_sorting": True,
                "signal_analysis": True
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/midas/asset/sector_summary/{sector}")
def get_sector_summary(sector: str):
    try:
        from services.stock_screener_service import get_sector_performance_summary
        summary = get_sector_performance_summary(sector)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/midas/asset/shorts_squeeze")
def get_shorts_squeeze():
    try:
        from services.reddit.reddit_scraper import RedditScraper
        from services.technical_indicator_service import calculate_technical_indicators
        import random
        
        # Use Reddit scraper to get mentioned tickers
        scraper = RedditScraper(days_back=7)  # Look back 7 days
        mentioned_tickers = scraper.scrape()
        
        # Limit to top 20 tickers to avoid too many API calls
        top_tickers = mentioned_tickers[:20] if len(mentioned_tickers) > 20 else mentioned_tickers
        
        shorts_squeeze_data = []
        
        for ticker in top_tickers:
            try:
                # Get technical analysis for each ticker
                tech_data = calculate_technical_indicators(ticker, "stock")
                
                # Skip if we got an error
                if "error" in tech_data:
                    continue
                
                # Calculate shorts squeeze potential based on technical indicators
                rsi = tech_data.get("rsi", 50)
                macd = tech_data.get("macd", 0)
                macd_signal = tech_data.get("macd_signal", 0)
                price_change = tech_data.get("price_rate_of_change", 0)
                
                # Simple shorts squeeze scoring
                squeeze_score = 0
                if rsi < 30:  # Oversold
                    squeeze_score += 2
                elif rsi > 70:  # Overbought
                    squeeze_score -= 1
                
                if macd > macd_signal:  # Bullish MACD
                    squeeze_score += 1
                
                if price_change > 0:  # Positive price change
                    squeeze_score += 1
                
                # Determine squeeze signal
                if squeeze_score >= 3:
                    signal = "HIGH_SQUEEZE_POTENTIAL"
                elif squeeze_score >= 2:
                    signal = "MODERATE_SQUEEZE_POTENTIAL"
                elif squeeze_score >= 1:
                    signal = "LOW_SQUEEZE_POTENTIAL"
                else:
                    signal = "NEUTRAL"
                
                # Mock additional data that would come from a real shorts data provider
                short_interest = random.uniform(5, 25)  # Mock short interest %
                short_ratio = random.uniform(1, 5)  # Mock short ratio
                days_to_cover = random.uniform(1, 10)  # Mock days to cover
                
                shorts_squeeze_data.append({
                    "ticker": ticker,
                    "market_price": tech_data.get("market_price", 0),
                    "signal": signal,
                    "macd": tech_data.get("macd", 0),
                    "price_rate_of_change": tech_data.get("price_rate_of_change", 0),
                    "rsi": tech_data.get("rsi", 50),
                    "stochastic_oscillator": tech_data.get("stochastic_oscillator", 50),
                    "industry": "Technology",  # Mock industry
                    "company_name": ticker,
                    "sector": "Technology",  # Mock sector
                    "short_interest": round(short_interest, 2),
                    "short_ratio": round(short_ratio, 2),
                    "days_to_cover": round(days_to_cover, 2),
                    "squeeze_score": squeeze_score,
                    "reddit_mentions": random.randint(5, 50)  # Mock mention count
                })
                
            except Exception as e:
                print(f"Error processing ticker {ticker}: {e}")
                continue
        
        # Sort by squeeze score (highest first)
        shorts_squeeze_data.sort(key=lambda x: x["squeeze_score"], reverse=True)
        
        return shorts_squeeze_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------
# Backtesting Endpoints
# ------------------------------

@app.get("/midas/backtest/historical_rankings")
def get_historical_rankings_endpoint(
    reference_date: str = Query(..., description="Reference date in YYYY-MM-DD format"),
    top_n: int = Query(50, description="Number of top stocks to return"),
    sector: str = Query(None, description="Optional sector filter (tech, finance, energy, bio)"),
    min_price: float = Query(None, description="Optional minimum price filter"),
    max_price: float = Query(None, description="Optional maximum price filter"),
    min_adr: float = Query(None, description="Optional minimum ADR filter"),
    max_adr: float = Query(None, description="Optional maximum ADR filter"),
    # Performance filters (matching regular scanner)
    min_1m_performance: float = Query(None, description="Optional minimum 1-month performance filter (%)"),
    max_1m_performance: float = Query(None, description="Optional maximum 1-month performance filter (%)"),
    min_3m_performance: float = Query(None, description="Optional minimum 3-month performance filter (%)"),
    max_3m_performance: float = Query(None, description="Optional maximum 3-month performance filter (%)"),
    min_6m_performance: float = Query(None, description="Optional minimum 6-month performance filter (%)"),
    max_6m_performance: float = Query(None, description="Optional maximum 6-month performance filter (%)"),
    sort_by: str = Query("adr", description="Field to sort by (adr, rsi, performance_1m, etc.)"),
    sort_order: str = Query("desc", description="Sort order (asc or desc)"),
    # Optimization parameters
    use_sample: bool = Query(False, description="Use sampling for faster results (trades accuracy for speed)"),
    sample_size: int = Query(1000, description="Number of stocks to sample if use_sample=True"),
    max_universe_size: int = Query(None, description="Maximum number of stocks to process"),
    enable_rate_limiting: bool = Query(True, description="Enable rate limiting between API calls"),
    # Parallel processing parameters (for Pro tier)
    max_workers: int = Query(5, description="Number of concurrent worker threads (default: 5, recommended: 5-10 for Pro tier)"),
    rate_limit_per_minute: int = Query(200, description="API rate limit per minute (default: 200 for Pro tier, use 5 for free tier)")
):
    """
    Get historical stock rankings as they would have appeared at the reference_date.
    All calculations use only data available up to that date (no look-ahead bias).
    """
    try:
        logger.info(f"📥 Received request for historical rankings: reference_date={reference_date}, top_n={top_n}, sector={sector}")
        
        # Validate reference_date format
        try:
            ref_date_obj = datetime.strptime(reference_date, "%Y-%m-%d")
        except ValueError:
            logger.error(f"❌ Invalid date format: {reference_date}")
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        # Validate that reference_date is not in the future
        now = datetime.now()
        if ref_date_obj > now:
            logger.error(f"❌ Reference date is in the future: {reference_date} (today is {now.strftime('%Y-%m-%d')})")
            raise HTTPException(status_code=400, detail=f"Reference date cannot be in the future. Today is {now.strftime('%Y-%m-%d')}")
        
        logger.info(f"✅ Date validation passed: {reference_date}")
        
        filters = {}
        if min_price is not None:
            filters['min_price'] = min_price
        if max_price is not None:
            filters['max_price'] = max_price
        if min_adr is not None:
            filters['min_adr'] = min_adr
        if max_adr is not None:
            filters['max_adr'] = max_adr
        # Performance filters (matching regular scanner)
        if min_1m_performance is not None:
            filters['min_1m_performance'] = min_1m_performance
        if max_1m_performance is not None:
            filters['max_1m_performance'] = max_1m_performance
        if min_3m_performance is not None:
            filters['min_3m_performance'] = min_3m_performance
        if max_3m_performance is not None:
            filters['max_3m_performance'] = max_3m_performance
        if min_6m_performance is not None:
            filters['min_6m_performance'] = min_6m_performance
        if max_6m_performance is not None:
            filters['max_6m_performance'] = max_6m_performance
        
        # Optimization parameters
        opt_params = {}
        if use_sample is not None:
            opt_params['use_sample'] = use_sample
        if sample_size is not None:
            opt_params['sample_size'] = sample_size
        if max_universe_size is not None:
            opt_params['max_universe_size'] = max_universe_size
        if enable_rate_limiting is not None:
            opt_params['enable_rate_limiting'] = enable_rate_limiting
        
        # Parallel processing parameters (for Pro tier)
        opt_params['max_workers'] = max_workers
        opt_params['rate_limit_per_minute'] = rate_limit_per_minute
        
        # Check if session already exists
        filters_dict = {**filters}
        if sector:
            filters_dict['sector'] = sector
        if sort_by:
            filters_dict['sort_by'] = sort_by
        if sort_order:
            filters_dict['sort_order'] = sort_order
        
        existing_session = find_session_by_date(reference_date, filters_dict if filters_dict else None)
        
        if existing_session and existing_session.get('historical_rankings'):
            logger.info(f"📂 Found existing session for {reference_date}, returning cached rankings")
            return {
                "rankings": existing_session['historical_rankings'],
                "session_id": existing_session['session_id'],
                "from_cache": True
            }
        
        # Generate new rankings (this creates session early and updates it when complete)
        result = get_historical_rankings(
            reference_date=reference_date,
            top_n=top_n,
            sort_by=sort_by,
            sort_order=sort_order,
            sector=sector,
            min_price=filters.get('min_price'),
            max_price=filters.get('max_price'),
            min_adr=filters.get('min_adr'),
            max_adr=filters.get('max_adr'),
            min_1m_performance=filters.get('min_1m_performance'),
            max_1m_performance=filters.get('max_1m_performance'),
            min_3m_performance=filters.get('min_3m_performance'),
            max_3m_performance=filters.get('max_3m_performance'),
            min_6m_performance=filters.get('min_6m_performance'),
            max_6m_performance=filters.get('max_6m_performance'),
            **opt_params
        )
        
        # Handle both old format (list) and new format (dict with rankings and session_id)
        if isinstance(result, dict) and 'rankings' in result:
            return {
                "rankings": result['rankings'],
                "session_id": result.get('session_id'),
                "from_cache": False
            }
        else:
            # Fallback for old format (shouldn't happen, but handle gracefully)
            new_session = find_session_by_date(reference_date, filters_dict if filters_dict else None)
            session_id = new_session.get('session_id') if new_session else None
            return {
                "rankings": result,
                "session_id": session_id,
                "from_cache": False
            }
        
    except HTTPException:
        raise
    except ValueError as e:
        # ValueErrors are user-facing issues (like missing universe file)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"❌ Error in historical rankings endpoint: {e}")
        logger.error(f"Traceback: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Failed to get historical rankings: {str(e)}")


@app.post("/midas/backtest/simulate_trade")
async def simulate_trade_endpoint(request: Request):
    """
    Simulate a trade forward from entry date and track performance.
    """
    try:
        data = await request.json()
        
        # Validate required fields
        required_fields = ['ticker', 'entry_date', 'entry_price', 'quantity']
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Validate entry_date format
        try:
            datetime.strptime(data['entry_date'], "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid entry_date format. Use YYYY-MM-DD")
        
        # Validate exit_date format if provided
        if 'exit_date' in data and data['exit_date']:
            try:
                datetime.strptime(data['exit_date'], "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid exit_date format. Use YYYY-MM-DD")
        
        result = simulate_trade(
            ticker=data['ticker'],
            entry_date=data['entry_date'],
            entry_price=float(data['entry_price']),
            quantity=int(data['quantity']),
            stop_loss=float(data.get('stop_loss')) if data.get('stop_loss') else None,
            take_profit=float(data.get('take_profit')) if data.get('take_profit') else None,
            exit_date=data.get('exit_date'),
            max_hold_days=int(data.get('max_hold_days')) if data.get('max_hold_days') else None
        )
        
        # Save trade to session cache if session_id is provided
        if 'session_id' in data:
            try:
                trade_config = {
                    'entry_date': data['entry_date'],
                    'entry_price': float(data['entry_price']),
                    'quantity': int(data['quantity']),
                    'stop_loss': float(data.get('stop_loss')) if data.get('stop_loss') else None,
                    'take_profit': float(data.get('take_profit')) if data.get('take_profit') else None,
                    'exit_date': data.get('exit_date'),
                    'max_hold_days': int(data.get('max_hold_days')) if data.get('max_hold_days') else None
                }
                add_trade_to_session(data['session_id'], data['ticker'], trade_config, result)
                result['session_id'] = data['session_id']  # Include in response
            except Exception as e:
                logger.warning(f"⚠️  Failed to save trade to session: {e}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trade simulation failed: {str(e)}")


@app.post("/midas/backtest/run_strategy")
async def run_strategy_backtest_endpoint(request: Request):
    """
    Run a complete strategy backtest (for future use - full implementation later).
    """
    try:
        data = await request.json()
        return {
            "message": "Strategy backtesting not yet implemented",
            "received_params": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Strategy backtest failed: {str(e)}")


# ------------------------------
# Backtesting Session Management Endpoints
# ------------------------------

@app.get("/midas/backtest/sessions")
def list_backtest_sessions():
    """
    List all available backtesting sessions.
    """
    try:
        # Clean up expired sessions first
        clear_expired_sessions()
        
        sessions = list_sessions()
        return {
            "sessions": sessions,
            "count": len(sessions)
        }
    except Exception as e:
        logger.error(f"❌ Error listing sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")


@app.get("/midas/backtest/sessions/{session_id}")
def get_backtest_session(session_id: str):
    """
    Get a specific backtesting session by ID.
    """
    try:
        session = get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found or expired")
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")


@app.get("/midas/backtest/sessions/by_date/{reference_date}")
def find_backtest_session_by_date(
    reference_date: str,
    sector: str = Query(None),
    sort_by: str = Query(None)
):
    """
    Find a backtesting session by reference date and filters.
    """
    try:
        filters = {}
        if sector:
            filters['sector'] = sector
        if sort_by:
            filters['sort_by'] = sort_by
        
        session = find_session_by_date(reference_date, filters if filters else None)
        if not session:
            raise HTTPException(status_code=404, detail=f"No session found for {reference_date}")
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error finding session for {reference_date}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to find session: {str(e)}")


@app.delete("/midas/backtest/sessions/{session_id}")
def delete_backtest_session(session_id: str):
    """
    Delete a backtesting session.
    """
    try:
        success = delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        return {"message": f"Session {session_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")


@app.post("/midas/backtest/sessions/clear_expired")
def clear_expired_backtest_sessions():
    """
    Manually trigger cleanup of expired sessions.
    """
    try:
        deleted_count = clear_expired_sessions()
        return {
            "message": f"Cleaned up {deleted_count} expired sessions",
            "deleted_count": deleted_count
        }
    except Exception as e:
        logger.error(f"❌ Error clearing expired sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear expired sessions: {str(e)}")
