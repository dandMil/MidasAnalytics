# services/trade_recommendation_service.py

import sqlite3
from datetime import datetime
from services.technical_indicator_service import calculate_technical_indicators

DB_FILE = "portfolio.db"

PROFIT_TARGET_PERCENTAGE = 10.0
STOP_LOSS_PERCENTAGE = 5.0

HIGH_VOLATILITY_THRESHOLD = 1.5
LOW_VOLATILITY_THRESHOLD = 0.5

PROFIT_TARGET_MULTIPLIER = 3.0
STOP_LOSS_MULTIPLIER = 2.0

PERCENTAGE_BASED = "PERCENTAGE_BASED"
VOLATILITY_BASED = "VOLATILITY_BASED"

def round_sig(value, sig=3):
    if value == 0: return 0
    from math import log10, floor
    return round(value, sig - int(floor(log10(abs(value)))) - 1)

def select_strategy(atr, so, rsi, macd, roc):
    high_volatility = atr > HIGH_VOLATILITY_THRESHOLD
    strong_momentum = abs(macd) > 1.0 or abs(roc) > 10.0
    extreme_signals = rsi > 70 or rsi < 30 or so > 80 or so < 20
    return VOLATILITY_BASED if high_volatility or strong_momentum or extreme_signals else PERCENTAGE_BASED

def calculate_trade_recommendations(ticker: str, entry_price: float) -> dict:
    indicators = calculate_technical_indicators(ticker, "stock")

    atr = indicators["atr"]
    so = indicators["stochastic_oscillator"]
    rsi = indicators["relative_strength_index"]
    macd = indicators["macd"]
    roc = indicators["price_rate_of_change"]

    strategy = select_strategy(atr, so, rsi, macd, roc)

    if strategy == PERCENTAGE_BASED:
        take_profit = entry_price * (1 + PROFIT_TARGET_PERCENTAGE / 100)
        stop_loss = entry_price * (1 - STOP_LOSS_PERCENTAGE / 100)
    else:
        take_profit = entry_price + PROFIT_TARGET_MULTIPLIER * atr
        stop_loss = entry_price - STOP_LOSS_MULTIPLIER * atr

    expected_profit = take_profit - entry_price
    expected_loss = entry_price - stop_loss

    return {
        "ticker": ticker,
        "strategy": strategy,
        "price_entry": round_sig(entry_price),
        "take_profit": round_sig(take_profit),
        "stop_loss": round_sig(stop_loss),
        "expected_profit": round_sig(expected_profit),
        "expected_loss": round_sig(expected_loss),
        "recommendation_date": datetime.now().isoformat()
    }

def save_trade_recommendation(rec: dict, shares: int):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS trade_recommendations (
            ticker TEXT PRIMARY KEY,
            strategy TEXT,
            price_entry REAL,
            take_profit REAL,
            stop_loss REAL,
            expected_profit REAL,
            expected_loss REAL,
            shares INTEGER,
            recommendation_date TEXT
        )
    """)

    cur.execute("DELETE FROM trade_recommendations WHERE ticker = ?", (rec['ticker'],))

    cur.execute("""
        INSERT INTO trade_recommendations
        (ticker, strategy, price_entry, take_profit, stop_loss,
         expected_profit, expected_loss, shares, recommendation_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        rec['ticker'], rec['strategy'], rec['price_entry'], rec['take_profit'],
        rec['stop_loss'], rec['expected_profit'] * shares,
        rec['expected_loss'] * shares, shares, rec['recommendation_date']
    ))

    conn.commit()
    conn.close()

def fetch_trade_recommendation(ticker: str) -> dict:
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("SELECT * FROM trade_recommendations WHERE ticker = ?", (ticker,))
    row = cur.fetchone()
    conn.close()

    if row:
        return {
            "ticker": row[0],
            "strategy": row[1],
            "price_entry": row[2],
            "take_profit": row[3],
            "stop_loss": row[4],
            "expected_profit": row[5],
            "expected_loss": row[6],
            "shares": row[7],
            "recommendation_date": row[8]
        }
    return {}
