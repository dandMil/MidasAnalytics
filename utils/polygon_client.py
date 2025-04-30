import os
import requests
from datetime import datetime, timedelta

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")


def n_days_ago(n: int) -> str:
    return (datetime.now() - timedelta(days=n)).strftime("%Y-%m-%d")


def get_price_history(ticker: str, days: int = 60) -> dict:
    """
    Fetch historical daily price data from Polygon.
    Equivalent to buildPriceTickerUrl.
    """
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{n_days_ago(days)}/{n_days_ago(0)}"
    params = {
        "adjusted": "true",
        "sort": "asc",
        "apiKey": POLYGON_API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Polygon API error: {response.status_code} - {response.text}")
    return response.json()


def get_bars(ticker: str, start_days_ago: int = 30, end_days_ago: int = 0) -> dict:
    """
    Fetch OHLCV bars between two dates.
    Equivalent to buildBarsTickerUrl.
    """
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{n_days_ago(start_days_ago)}/{n_days_ago(end_days_ago)}"
    params = {
        "adjusted": "true",
        "sort": "asc",
        "apiKey": POLYGON_API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Polygon API error: {response.status_code} - {response.text}")
    return response.json()


def get_top_movers(direction: str = "gainers") -> dict:
    """
    Fetch top gainers or losers.
    Equivalent to buildTopMoversUrl.
    """
    assert direction in ["gainers", "losers"]
    url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/{direction}"
    params = {
        "apiKey": POLYGON_API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Polygon API error: {response.status_code} - {response.text}")
    return response.json()
