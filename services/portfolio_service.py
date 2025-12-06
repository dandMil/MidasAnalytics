# services/portfolio_service.py

import sqlite3
from datetime import datetime
from services.trade_recommendation_service import calculate_trade_recommendations

DB_FILE = "portfolio.db"

def initialize_portfolio_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Create portfolio table with new schema
    cur.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT UNIQUE,
            shares INTEGER,
            price REAL,
            stop_loss REAL,
            take_profit REAL,
            type TEXT,
            updated_at TEXT
        )
    """)
    
    # Migrate existing table to add new columns if they don't exist
    try:
        cur.execute("ALTER TABLE portfolio ADD COLUMN stop_loss REAL")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cur.execute("ALTER TABLE portfolio ADD COLUMN take_profit REAL")
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Create transactions table for transaction history
    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            shares INTEGER,
            price REAL,
            stop_loss REAL,
            take_profit REAL,
            transaction_type TEXT,
            created_at TEXT
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


def do_transaction(ticker: str, shares: int, current_price: float, stop_loss: float = None, take_profit: float = None):
    """
    Execute a transaction (buy or sell) and update portfolio.
    
    Args:
        ticker: Stock ticker symbol
        shares: Number of shares (positive for buy, negative for sell)
        current_price: Current price per share
        stop_loss: Stop loss price (optional)
        take_profit: Take profit price (optional)
    
    Returns:
        Dictionary with transaction result
    """
    initialize_portfolio_db()
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Determine transaction type
    transaction_type = "BUY" if shares > 0 else "SELL"
    abs_shares = abs(shares)
    
    # Check current portfolio position
    cur.execute("SELECT shares, price FROM portfolio WHERE ticker = ?", (ticker,))
    row = cur.fetchone()
    
    current_shares = row[0] if row else 0
    current_avg_price = row[1] if row else 0
    
    if transaction_type == "BUY":
        # Buying shares
        if row:
            # Existing position - calculate new average price
            old_shares, old_price = row
            avg_price = calculate_dollar_cost_average(old_price, current_price, old_shares, abs_shares)
            new_shares = old_shares + abs_shares
            
            # Update portfolio with new average price and stop_loss/take_profit
            cur.execute("""
                UPDATE portfolio
                SET shares = ?, price = ?, stop_loss = ?, take_profit = ?, updated_at = ?
                WHERE ticker = ?
            """, (new_shares, avg_price, stop_loss, take_profit, datetime.now().isoformat(), ticker))
        else:
            # New position
            cur.execute("""
                INSERT INTO portfolio (ticker, shares, price, stop_loss, take_profit, type, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (ticker, abs_shares, current_price, stop_loss, take_profit, "stock", datetime.now().isoformat()))
        
        message = f"Purchased {abs_shares} shares of {ticker} at ${current_price:.2f}"
        
    else:  # SELL
        # Selling shares
        if not row or current_shares == 0:
            conn.close()
            return {
                "success": False,
                "message": f"Cannot sell {abs_shares} shares of {ticker} - no position exists",
                "error": "INSUFFICIENT_POSITION"
            }
        
        if current_shares < abs_shares:
            conn.close()
            return {
                "success": False,
                "message": f"Cannot sell {abs_shares} shares - only {current_shares} shares available",
                "error": "INSUFFICIENT_SHARES",
                "available_shares": current_shares
            }
        
        # Calculate P&L for this transaction
        cost_basis = current_avg_price * abs_shares
        sale_value = current_price * abs_shares
        profit_loss = sale_value - cost_basis
        profit_loss_pct = ((current_price - current_avg_price) / current_avg_price * 100) if current_avg_price > 0 else 0
        
        new_shares = current_shares - abs_shares
        
        if new_shares > 0:
            # Partial sale - keep position with same average price
            cur.execute("""
                UPDATE portfolio
                SET shares = ?, updated_at = ?
                WHERE ticker = ?
            """, (new_shares, datetime.now().isoformat(), ticker))
        else:
            # Full sale - remove from portfolio
            cur.execute("DELETE FROM portfolio WHERE ticker = ?", (ticker,))
        
        message = f"Sold {abs_shares} shares of {ticker} at ${current_price:.2f} | P&L: ${profit_loss:.2f} ({profit_loss_pct:+.2f}%)"
    
    # Record transaction in history
    cur.execute("""
        INSERT INTO transactions (ticker, shares, price, stop_loss, take_profit, transaction_type, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (ticker, shares, current_price, stop_loss, take_profit, transaction_type, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    # Calculate trade recommendation for new positions
    recommendation = None
    if transaction_type == "BUY":
        recommendation = calculate_trade_recommendations(ticker, current_price)
    
    return {
        "success": True,
        "message": message,
        "ticker": ticker,
        "shares": abs_shares,
        "price": current_price,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "transaction_type": transaction_type,
        "recommendation": recommendation
    }
