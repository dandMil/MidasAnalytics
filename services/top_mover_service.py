# services/top_movers_service.py
import os

import requests
import pandas as pd
import datetime
import sqlite3  # (or Postgres later)

# Constants
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY","default_secret_key")
POLYGON_TOP_MOVERS_URL = "https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/gainers"

DB_FILE = "watchlist.db"  # Simple SQLite file for now


# -------------------------
# Fetch Real-Time Top Movers
# -------------------------

def fetch_top_movers(mover_type: str):
    """
    Fetch top gainers or losers from Polygon and format for frontend.
    """
    if mover_type == "losers":
        url = "https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/losers"
    else:
        url = "https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/gainers"

    params = {"apiKey": POLYGON_API_KEY}
    response = requests.get(url, params=params)

    if response.status_code != 200:
        raise Exception("Failed to fetch movers")

    data = response.json()
    movers = []

    for ticker_info in data.get('tickers', []):
        day = ticker_info.get('day', {})
        movers.append({
            "ticker": ticker_info.get('ticker'),
            "todaysChangePerc": ticker_info.get('todaysChangePercent', 0.0),
            "todaysChange": ticker_info.get('todaysChange', 0.0),
            "updated": ticker_info.get('updated', 0),
            "day": {
                "o": day.get('o', 0.0),
                "h": day.get('h', 0.0),
                "l": day.get('l', 0.0),
                "c": day.get('c', 0.0),
                "v": day.get('v', 0),
                "vw": day.get('vw', 0.0)
            }
        })

    return movers


# -------------------------
# Save Movers into Watchlist Database
# -------------------------

def save_top_movers(movers, movement_type):
    """
    Save movers into SQLite (Watchlist).
    """
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id TEXT PRIMARY KEY,
            name TEXT,
            type TEXT,
            date_created TEXT,
            movement TEXT,
            price_change REAL,
            volume INTEGER,
            price REAL
        )
    """)

    for mover in movers:
        cur.execute("""
            INSERT INTO watchlist (id, name, type, date_created, movement, price_change, volume, price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            mover['ticker'],
            "Stock",
            datetime.datetime.now().isoformat(),
            movement_type,
            mover['price_change'],
            mover['volume'],
            mover['close_price']
        ))

    conn.commit()
    conn.close()


# -------------------------
# Full Daily Fetch and Save
# -------------------------

def fetch_and_save_top_movers():
    """
    Fetch gainers and losers daily and save them into watchlist.
    """
    gainers = fetch_top_movers("gainers")
    losers = fetch_top_movers("losers")

    save_top_movers(gainers, "gainers")
    save_top_movers(losers, "losers")


# -------------------------
# Find Repeated Movers
# -------------------------

def find_repeated_movers(days_back=5):
    """
    Find tickers that appeared more than once in the last X days.
    """
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    since_date = (datetime.datetime.now() - datetime.timedelta(days=days_back)).isoformat()

    cur.execute("""
        SELECT name, COUNT(name) as freq 
        FROM watchlist
        WHERE date_created > ?
        GROUP BY name
        HAVING freq > 1
    """, (since_date,))

    rows = cur.fetchall()
    conn.close()

    return [{"ticker": row[0], "count": row[1]} for row in rows]
