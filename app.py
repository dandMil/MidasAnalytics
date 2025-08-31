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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
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
        return {"data": result}
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
