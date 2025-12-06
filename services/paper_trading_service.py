# services/paper_trading_service.py

import sqlite3
from datetime import datetime, date
from typing import Dict, List, Optional
from services.trade_recommendation_service import calculate_trade_recommendations
from utils.polygon_client import get_price_history

DB_FILE = "portfolio.db"
DEFAULT_STARTING_CAPITAL = 100000.0  # $100k default paper trading account

def initialize_paper_trading_db():
    """Initialize paper trading tables"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Paper portfolio table (separate from real portfolio)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS paper_portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT UNIQUE,
            shares INTEGER,
            entry_price REAL,
            stop_loss REAL,
            take_profit REAL,
            type TEXT,
            updated_at TEXT
        )
    """)
    
    # Paper transactions table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS paper_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            shares INTEGER,
            price REAL,
            stop_loss REAL,
            take_profit REAL,
            transaction_type TEXT,
            realized_pnl REAL,
            realized_pnl_percent REAL,
            created_at TEXT
        )
    """)
    
    # Paper account table (cash balance and daily tracking)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS paper_account (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            starting_capital REAL,
            cash_balance REAL,
            portfolio_value REAL,
            unrealized_pnl REAL,
            realized_pnl REAL,
            total_pnl REAL,
            last_updated TEXT,
            trading_date TEXT,
            UNIQUE(trading_date)
        )
    """)
    
    # Initialize account if it doesn't exist
    cur.execute("SELECT COUNT(*) FROM paper_account")
    if cur.fetchone()[0] == 0:
        cur.execute("""
            INSERT INTO paper_account 
            (starting_capital, cash_balance, portfolio_value, unrealized_pnl, realized_pnl, total_pnl, last_updated, trading_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (DEFAULT_STARTING_CAPITAL, DEFAULT_STARTING_CAPITAL, DEFAULT_STARTING_CAPITAL, 0.0, 0.0, 0.0, 
              datetime.now().isoformat(), date.today().isoformat()))
    
    conn.commit()
    conn.close()


def get_current_price(ticker: str) -> float:
    """Get current price for a ticker"""
    try:
        bars = get_price_history(ticker, days=1)
        if bars and len(bars) > 0:
            return bars[-1].get('c', 0)  # Close price
    except Exception as e:
        print(f"Error fetching price for {ticker}: {e}")
    return 0.0


def calculate_dollar_cost_average(old_price: float, new_price: float, old_shares: int, new_shares: int) -> float:
    """Calculate dollar-cost average price"""
    if old_shares + new_shares == 0:
        return new_price
    total_investment = (old_price * old_shares) + (new_price * new_shares)
    total_shares = old_shares + new_shares
    return total_investment / total_shares


def get_paper_account() -> Dict:
    """Get current paper trading account status"""
    initialize_paper_trading_db()
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT starting_capital, cash_balance, portfolio_value, unrealized_pnl, realized_pnl, total_pnl, 
               last_updated, trading_date
        FROM paper_account
        ORDER BY id DESC
        LIMIT 1
    """)
    
    row = cur.fetchone()
    conn.close()
    
    if not row:
        # Initialize account
        initialize_paper_trading_db()
        return get_paper_account()
    
    starting_capital, cash_balance, portfolio_value, unrealized_pnl, realized_pnl, total_pnl, last_updated, trading_date = row
    
    return {
        "starting_capital": starting_capital,
        "cash_balance": cash_balance,
        "portfolio_value": portfolio_value,
        "unrealized_pnl": unrealized_pnl,
        "realized_pnl": realized_pnl,
        "total_pnl": total_pnl,
        "total_return_percent": ((total_pnl / starting_capital) * 100) if starting_capital > 0 else 0,
        "last_updated": last_updated,
        "trading_date": trading_date
    }


def update_paper_account():
    """Recalculate and update paper account balances"""
    initialize_paper_trading_db()
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Get all positions
    cur.execute("SELECT ticker, shares, entry_price FROM paper_portfolio")
    positions = cur.fetchall()
    
    # Calculate portfolio value and unrealized P&L
    portfolio_value = 0.0
    total_cost_basis = 0.0
    
    for ticker, shares, entry_price in positions:
        current_price = get_current_price(ticker)
        position_value = shares * current_price
        cost_basis = shares * entry_price
        portfolio_value += position_value
        total_cost_basis += cost_basis
    
    # Get cash balance from account
    cur.execute("SELECT cash_balance, starting_capital FROM paper_account ORDER BY id DESC LIMIT 1")
    account_row = cur.fetchone()
    
    if account_row:
        cash_balance = account_row[0]
        starting_capital = account_row[1]
    else:
        cash_balance = DEFAULT_STARTING_CAPITAL
        starting_capital = DEFAULT_STARTING_CAPITAL
    
    # Calculate P&L
    unrealized_pnl = portfolio_value - total_cost_basis
    
    # Get realized P&L from transactions (sum of all realized_pnl)
    cur.execute("SELECT COALESCE(SUM(realized_pnl), 0) FROM paper_transactions WHERE transaction_type = 'SELL'")
    realized_pnl_row = cur.fetchone()
    realized_pnl = realized_pnl_row[0] if realized_pnl_row else 0.0
    
    total_pnl = unrealized_pnl + realized_pnl
    total_portfolio_value = cash_balance + portfolio_value
    
    # Update or insert account record for today
    today = date.today().isoformat()
    cur.execute("""
        INSERT OR REPLACE INTO paper_account 
        (starting_capital, cash_balance, portfolio_value, unrealized_pnl, realized_pnl, total_pnl, last_updated, trading_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (starting_capital, cash_balance, total_portfolio_value, unrealized_pnl, realized_pnl, total_pnl,
          datetime.now().isoformat(), today))
    
    conn.commit()
    conn.close()
    
    return {
        "starting_capital": starting_capital,
        "cash_balance": cash_balance,
        "portfolio_value": portfolio_value,
        "total_portfolio_value": total_portfolio_value,
        "unrealized_pnl": unrealized_pnl,
        "realized_pnl": realized_pnl,
        "total_pnl": total_pnl,
        "total_return_percent": ((total_pnl / starting_capital) * 100) if starting_capital > 0 else 0
    }


def do_paper_transaction(ticker: str, shares: int, current_price: float, stop_loss: float = None, take_profit: float = None) -> Dict:
    """
    Execute a paper trading transaction (buy or sell).
    
    Args:
        ticker: Stock ticker symbol
        shares: Number of shares (positive for buy, negative for sell)
        current_price: Current price per share
        stop_loss: Stop loss price (optional)
        take_profit: Take profit price (optional)
    
    Returns:
        Dictionary with transaction result
    """
    initialize_paper_trading_db()
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Get account info
    account = get_paper_account()
    cash_balance = account["cash_balance"]
    
    transaction_type = "BUY" if shares > 0 else "SELL"
    abs_shares = abs(shares)
    
    if transaction_type == "BUY":
        # Check if we have enough cash
        cost = abs_shares * current_price
        if cost > cash_balance:
            conn.close()
            return {
                "success": False,
                "message": f"Insufficient cash. Need ${cost:.2f}, have ${cash_balance:.2f}",
                "error": "INSUFFICIENT_CASH",
                "cash_balance": cash_balance,
                "required": cost
            }
        
        # Check current position
        cur.execute("SELECT shares, entry_price FROM paper_portfolio WHERE ticker = ?", (ticker,))
        row = cur.fetchone()
        
        if row:
            # Existing position - dollar cost average
            old_shares, old_price = row
            new_entry_price = calculate_dollar_cost_average(old_price, current_price, old_shares, abs_shares)
            new_shares = old_shares + abs_shares
            
            cur.execute("""
                UPDATE paper_portfolio
                SET shares = ?, entry_price = ?, stop_loss = ?, take_profit = ?, updated_at = ?
                WHERE ticker = ?
            """, (new_shares, new_entry_price, stop_loss, take_profit, datetime.now().isoformat(), ticker))
        else:
            # New position
            cur.execute("""
                INSERT INTO paper_portfolio (ticker, shares, entry_price, stop_loss, take_profit, type, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (ticker, abs_shares, current_price, stop_loss, take_profit, "stock", datetime.now().isoformat()))
        
        # Deduct cash
        new_cash_balance = cash_balance - cost
        
        # Update account cash
        today = date.today().isoformat()
        cur.execute("""
            UPDATE paper_account 
            SET cash_balance = ?, last_updated = ?
            WHERE trading_date = ?
        """, (new_cash_balance, datetime.now().isoformat(), today))
        
        message = f"Purchased {abs_shares} shares of {ticker} at ${current_price:.2f} for ${cost:.2f}"
        realized_pnl = None
        realized_pnl_percent = None
        
    else:  # SELL
        # Check position
        cur.execute("SELECT shares, entry_price FROM paper_portfolio WHERE ticker = ?", (ticker,))
        row = cur.fetchone()
        
        if not row or row[0] == 0:
            conn.close()
            return {
                "success": False,
                "message": f"No position in {ticker} to sell",
                "error": "NO_POSITION"
            }
        
        current_shares, entry_price = row
        
        if current_shares < abs_shares:
            conn.close()
            return {
                "success": False,
                "message": f"Only {current_shares} shares available, cannot sell {abs_shares}",
                "error": "INSUFFICIENT_SHARES",
                "available_shares": current_shares
            }
        
        # Calculate P&L
        cost_basis = entry_price * abs_shares
        sale_value = current_price * abs_shares
        realized_pnl = sale_value - cost_basis
        realized_pnl_percent = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
        
        # Update position
        new_shares = current_shares - abs_shares
        if new_shares > 0:
            cur.execute("""
                UPDATE paper_portfolio
                SET shares = ?, updated_at = ?
                WHERE ticker = ?
            """, (new_shares, datetime.now().isoformat(), ticker))
        else:
            cur.execute("DELETE FROM paper_portfolio WHERE ticker = ?", (ticker,))
        
        # Add cash
        new_cash_balance = cash_balance + sale_value
        
        # Update account cash
        today = date.today().isoformat()
        cur.execute("""
            UPDATE paper_account 
            SET cash_balance = ?, last_updated = ?
            WHERE trading_date = ?
        """, (new_cash_balance, datetime.now().isoformat(), today))
        
        message = f"Sold {abs_shares} shares of {ticker} at ${current_price:.2f} | Realized P&L: ${realized_pnl:.2f} ({realized_pnl_percent:+.2f}%)"
    
    # Record transaction
    cur.execute("""
        INSERT INTO paper_transactions (ticker, shares, price, stop_loss, take_profit, transaction_type, 
                                       realized_pnl, realized_pnl_percent, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (ticker, shares, current_price, stop_loss, take_profit, transaction_type, 
          realized_pnl, realized_pnl_percent, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    # Update account totals
    account = update_paper_account()
    
    # Get trade recommendation for buys
    recommendation = None
    if transaction_type == "BUY":
        try:
            recommendation = calculate_trade_recommendations(ticker, current_price)
        except Exception as e:
            # If recommendation fails, continue without it
            print(f"Warning: Could not generate trade recommendation for {ticker}: {e}")
            recommendation = None
    
    return {
        "success": True,
        "message": message,
        "ticker": ticker,
        "shares": abs_shares,
        "price": current_price,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "transaction_type": transaction_type,
        "realized_pnl": realized_pnl,
        "realized_pnl_percent": realized_pnl_percent,
        "cash_balance": account["cash_balance"],
        "portfolio_value": account["total_portfolio_value"],
        "unrealized_pnl": account["unrealized_pnl"],
        "total_pnl": account["total_pnl"],
        "recommendation": recommendation
    }


def get_paper_portfolio() -> List[Dict]:
    """Get paper trading portfolio with current values and P&L"""
    initialize_paper_trading_db()
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    cur.execute("SELECT ticker, shares, entry_price, stop_loss, take_profit, updated_at FROM paper_portfolio")
    positions = cur.fetchall()
    conn.close()
    
    portfolio = []
    for ticker, shares, entry_price, stop_loss, take_profit, updated_at in positions:
        current_price = get_current_price(ticker)
        position_value = shares * current_price
        cost_basis = shares * entry_price
        unrealized_pnl = position_value - cost_basis
        unrealized_pnl_percent = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
        
        portfolio.append({
            "ticker": ticker,
            "shares": shares,
            "entry_price": round(entry_price, 2),
            "current_price": round(current_price, 2),
            "position_value": round(position_value, 2),
            "cost_basis": round(cost_basis, 2),
            "unrealized_pnl": round(unrealized_pnl, 2),
            "unrealized_pnl_percent": round(unrealized_pnl_percent, 2),
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "updated_at": updated_at
        })
    
    return portfolio


def get_paper_transactions(limit: int = 50) -> List[Dict]:
    """Get paper trading transaction history"""
    initialize_paper_trading_db()
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT ticker, shares, price, transaction_type, realized_pnl, realized_pnl_percent, created_at
        FROM paper_transactions
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    
    transactions = cur.fetchall()
    conn.close()
    
    return [
        {
            "ticker": t[0],
            "shares": abs(t[1]),
            "price": round(t[2], 2),
            "transaction_type": t[3],
            "realized_pnl": round(t[4], 2) if t[4] else None,
            "realized_pnl_percent": round(t[5], 2) if t[5] else None,
            "created_at": t[6]
        }
        for t in transactions
    ]


def reset_paper_account(starting_capital: float = DEFAULT_STARTING_CAPITAL) -> Dict:
    """Reset paper trading account (clear positions and reset cash)"""
    initialize_paper_trading_db()
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Clear positions
    cur.execute("DELETE FROM paper_portfolio")
    
    # Clear transactions
    cur.execute("DELETE FROM paper_transactions")
    
    # Reset account
    today = date.today().isoformat()
    cur.execute("""
        INSERT OR REPLACE INTO paper_account 
        (starting_capital, cash_balance, portfolio_value, unrealized_pnl, realized_pnl, total_pnl, last_updated, trading_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (starting_capital, starting_capital, starting_capital, 0.0, 0.0, 0.0,
          datetime.now().isoformat(), today))
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "message": f"Paper trading account reset with ${starting_capital:,.2f}",
        "starting_capital": starting_capital,
        "cash_balance": starting_capital
    }

