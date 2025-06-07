# utils/market_data.py

import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")


def fetch_polygon_ohlcv(ticker: str, days: int = 60):
    import requests
    import os
    from datetime import datetime, timedelta

    api_key = os.getenv("POLYGON_API_KEY")
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)

    url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_date}/{end_date}"
    params = {"adjusted": "true", "sort": "asc", "apiKey": api_key}
    response = requests.get(url, params=params)
    data = response.json()

    bars = data.get("results", [])

    # Convert Polygon keys to expected OHLCV keys
    mapped_data = [
        {
            "timestamp": bar["t"],
            "open": bar["o"],
            "high": bar["h"],
            "low": bar["l"],
            "close": bar["c"],
            "volume": bar["v"]
        }
        for bar in bars
    ]

    return mapped_data



# def fetch_polygon_ohlcv(ticker: str, days_back: int = 90) -> list[dict]:
#     """
#     Fetches historical OHLCV bars for a given ticker from Polygon.io.
#
#     Args:
#         ticker (str): Stock ticker (e.g., "AAPL").
#         days_back (int): Number of days back from today.
#
#     Returns:
#         List[dict]: OHLCV data in dict format (c, o, h, l, v, t).
#     """
#     end_date = datetime.today()
#     start_date = end_date - timedelta(days=days_back)
#
#     url = f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
#
#     params = {
#         "adjusted": "true",
#         "sort": "asc",
#         "apiKey": POLYGON_API_KEY
#     }
#
#     try:
#         response = requests.get(url, params=params)
#         response.raise_for_status()
#         data = response.json()
#
#         bars = data.get("results", [])
#         return [
#             {
#                 "t": bar["t"],  # timestamp
#                 "o": bar["o"],  # open
#                 "h": bar["h"],  # high
#                 "l": bar["l"],  # low
#                 "c": bar["c"],  # close
#                 "v": bar["v"],  # volume
#             }
#             for bar in bars
#         ]
#
#     except requests.exceptions.RequestException as e:
#         print(f"[Polygon] API request failed: {e}")
#         return []
#     except (KeyError, ValueError) as e:
#         print(f"[Polygon] Error parsing response: {e}")
#         return []
