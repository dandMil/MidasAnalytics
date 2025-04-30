# services/portfolio_service.py

import sqlite3
from datetime import datetime
from services.trade_recommendation_service import calculate_trade_recommendations

DB_FILE = "portfolio.db"

def initialize_portfolio_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT UNIQUE,
            shares INTEGER,
            price REAL,
            type TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def calculate_dollar_cost_average(old_price, new_price, old_shares, new_shares):
    total_investment = (old_price * old_shares) + (new_price * new_shares)
    total_shares = old_shares + new_shares
    return total_investment / total_shares

def purchase_asset(ticker, shares, price):
    initialize_portfolio_db()
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("SELECT shares, price FROM portfolio WHERE ticker = ?", (ticker,))
    row = cur.fetchone()

    if row:
        old_shares, old_price = row
        avg_price = calculate_dollar_cost_average(old_price, price, old_shares, shares)
        new_shares = old_shares + shares
        cur.execute("""
            UPDATE portfolio
            SET shares = ?, price = ?, updated_at = ?
            WHERE ticker = ?
        """, (new_shares, avg_price, datetime.now().isoformat(), ticker))
    else:
        cur.execute("""
            INSERT INTO portfolio (ticker, shares, price, type, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (ticker, shares, price, "stock", datetime.now().isoformat()))

    conn.commit()
    conn.close()

    # Also save trade recommendation
    recommendation = calculate_trade_recommendations(ticker, price)
    # You can store this in a separate trade_recommendation table or return it

    return {"message": "Purchase successful", "recommendation": recommendation}


def fetch_portfolio():
    initialize_portfolio_db()
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("SELECT ticker, shares, price FROM portfolio")
    rows = cur.fetchall()
    conn.close()

    results = []
    for ticker, shares, entry_price in rows:
        try:
            # Fetch current price (can replace with Polygon later)
            import yfinance as yf
            df = yf.download(ticker, period="5d", interval="1d")
            current_price = df['Close'].iloc[-1]

            recommendation = calculate_trade_recommendations(ticker, entry_price)

            results.append({
                "ticker": ticker,
                "shares": shares,
                "entry_price": round(entry_price, 2),
                "current_price": round(current_price, 2),
                "recommendation": recommendation
            })

        except Exception as e:
            results.append({
                "ticker": ticker,
                "error": str(e)
            })

    return results
