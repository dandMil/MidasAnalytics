import os
import requests
from datetime import datetime, timedelta
from typing import Optional, List

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")


def n_days_ago(n: int) -> str:
    return (datetime.now() - timedelta(days=n)).strftime("%Y-%m-%d")


def get_price_history(ticker: str, days: int = 60) -> list[dict]:
    POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

    print(f'POLYGON API {POLYGON_API_KEY}')
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{n_days_ago(days)}/{n_days_ago(0)}"
    params = {
        "adjusted": "true",
        "sort": "asc",
        "apiKey": POLYGON_API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"[Polygon] Failed to fetch price history: {response.text}")

    return response.json().get("results", [])


def get_bars(ticker: str, start_days_ago: int = 30, end_days_ago: int = 0) -> list[dict]:
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{n_days_ago(start_days_ago)}/{n_days_ago(end_days_ago)}"
    params = {
        "adjusted": "true",
        "sort": "asc",
        "apiKey": POLYGON_API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"[Polygon] Failed to fetch bars: {response.text}")

    return response.json().get("results", [])


def get_top_movers(direction: str = "gainers") -> list[dict]:
    POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

    print(f'POLYGON API {POLYGON_API_KEY}')

    assert direction in ["gainers", "losers"], "Direction must be 'gainers' or 'losers'"
    url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/{direction}"
    params = {"apiKey": POLYGON_API_KEY}

    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"[Polygon] Failed to fetch top movers: {response.text}")

    tickers = response.json().get("tickers", [])

    return [
        {
            "ticker": t.get("ticker"),
            "price_change": t.get("todaysChangePercent"),
            "volume": t.get("day", {}).get("v", 0),
            "close_price": t.get("day", {}).get("c", 0)
        }
        for t in tickers
    ]


def get_market_snapshot(tickers: Optional[List[str]] = None, include_otc: bool = False) -> dict:
    """
    Get a comprehensive snapshot of the entire U.S. stock market
    
    Args:
        tickers: Optional list of specific tickers to get snapshots for. 
                 If None or empty, returns all tickers.
        include_otc: Whether to include OTC securities. Default is False.
    
    Returns:
        Dictionary containing the snapshot response
    """
    POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
    
    url = "https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers"
    
    params = {
        "apiKey": POLYGON_API_KEY
    }
    
    # Add tickers parameter if provided
    if tickers and len(tickers) > 0:
        params["tickers"] = ",".join(tickers)
    
    # Add include_otc parameter
    if include_otc:
        params["include_otc"] = "true"
    
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        raise Exception(f"[Polygon] Failed to fetch market snapshot: {response.text}")
    
    return response.json()
