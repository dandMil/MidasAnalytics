import os
import requests
from datetime import datetime, timedelta

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")


def n_days_ago(n: int) -> str:
    return (datetime.now() - timedelta(days=n)).strftime("%Y-%m-%d")


def get_price_history(ticker: str, days: int = 60) -> list[dict]:
    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{n_days_ago(days)}/{n_days_ago(0)}"
    params = {
        "adjusted": "true",
        "sort": "asc",
        "apiKey": POLYGON_API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"[Polygon] Failed to fetch price history: {response.text}")

    data = response.json()
    return data.get("results", [])


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

    data = response.json()
    return data.get("results", [])


def get_top_movers(direction: str = "gainers") -> list[dict]:
    assert direction in ["gainers", "losers"], "Direction must be 'gainers' or 'losers'"
    url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/{direction}"
    params = {"apiKey": POLYGON_API_KEY}

    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"[Polygon] Failed to fetch top movers: {response.text}")

    data = response.json()
    tickers = data.get("tickers", [])

    return [
        {
            "ticker": t.get("ticker"),
            "price_change": t.get("todaysChangePercent"),
            "volume": t.get("day", {}).get("v", 0),
            "close_price": t.get("day", {}).get("c", 0)
        }
        for t in tickers
    ]
