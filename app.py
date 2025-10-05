# app.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from openai import OpenAI
import os
from fastapi import APIRouter, Query
from services.reddit.reddit_scraper import RedditScraper
from routes.daily_summary_routes import router as daily_summary_router
from services.reddit import reddit_scraper as scrapper
from services.top_mover_service import fetch_top_movers
from services.technical_indicator_service import calculate_technical_indicators
from services.portfolio_service import purchase_asset, fetch_portfolio
from services.trade_recommendation_service import (
    calculate_trade_recommendations,
    fetch_trade_recommendation
)
from services.daily_summary.daily_summary_service import generate_daily_summary

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
def get_top_movers(mover: str = "gainers"):
    try:
        result = fetch_top_movers(mover)
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


@app.get("/midas/asset/stock_screener")
def get_stock_screener(
    sector: str = "all",  # "tech", "bio", "finance", "energy", "all"
    min_1m_performance: float = 10.0,
    min_3m_performance: float = 20.0,
    min_6m_performance: float = 30.0,
    min_price: float = 1.0,
    max_price: float = 50.0,
    min_rsi: float = 0.0,
    max_rsi: float = 100.0,
    rsi_signal: str = "all",  # "all", "oversold", "overbought", "neutral"
    limit: int = 50
):
    try:
        from services.stock_screener_service import screen_stocks
        
        filters = {
            "sector": sector,
            "min_1m_performance": min_1m_performance,
            "min_3m_performance": min_3m_performance,
            "min_6m_performance": min_6m_performance,
            "min_price": min_price,
            "max_price": max_price,
            "min_rsi": min_rsi,
            "max_rsi": max_rsi,
            "rsi_signal": rsi_signal,
            "limit": limit
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
