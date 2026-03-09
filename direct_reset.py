#!/usr/bin/env python3
"""
Direct Portfolio Reset - Bypasses all functions, directly manipulates database
"""

import sqlite3
import os
import shutil
from datetime import datetime, date

DB_FILE = "portfolio.db"
BACKUP_DIR = "portfolio_backups"

def main():
    print("=" * 70)
    print("DIRECT PORTFOLIO RESET")
    print("=" * 70)
    print()
    
    if not os.path.exists(DB_FILE):
        print(f"❌ Database file not found: {DB_FILE}")
        print(f"   Current directory: {os.getcwd()}")
        return
    
    print(f"📁 Database location: {os.path.abspath(DB_FILE)}")
    print(f"📦 Database size: {os.path.getsize(DB_FILE):,} bytes")
    print()
    
    # Create backup
    print("💾 Creating backup...")
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"portfolio_backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    try:
        shutil.copy2(DB_FILE, backup_path)
        print(f"   ✅ Backup created: {backup_path}")
    except Exception as e:
        print(f"   ❌ Backup failed: {e}")
        return
    
    # Connect and check current state
    print()
    print("📊 Checking current state...")
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Check paper_portfolio
    try:
        cur.execute("SELECT COUNT(*) FROM paper_portfolio")
        paper_count = cur.fetchone()[0]
        print(f"   Paper Portfolio: {paper_count} positions")
        
        if paper_count > 0:
            cur.execute("SELECT ticker, shares, entry_price FROM paper_portfolio LIMIT 5")
            positions = cur.fetchall()
            print("   Sample positions:")
            for pos in positions:
                print(f"      - {pos[0]}: {pos[1]} shares @ ${pos[2]:.2f}")
    except Exception as e:
        print(f"   Error checking paper_portfolio: {e}")
        paper_count = 0
    
    # Check regular portfolio
    try:
        cur.execute("SELECT COUNT(*) FROM portfolio")
        reg_count = cur.fetchone()[0]
        print(f"   Regular Portfolio: {reg_count} positions")
    except:
        reg_count = 0
    
    print()
    print("=" * 70)
    print("🔄 RESETTING...")
    print("=" * 70)
    
    # Clear all tables
    tables_cleared = {}
    for table in ['paper_portfolio', 'paper_transactions', 'portfolio', 'transactions']:
        try:
            cur.execute(f"DELETE FROM {table}")
            rows_deleted = cur.rowcount
            tables_cleared[table] = rows_deleted
            if rows_deleted > 0:
                print(f"   ✅ Cleared {rows_deleted} rows from {table}")
        except sqlite3.OperationalError as e:
            if "no such table" in str(e).lower():
                print(f"   ⚠️  Table {table} doesn't exist (skipping)")
            else:
                print(f"   ⚠️  Error clearing {table}: {e}")
        except Exception as e:
            print(f"   ❌ Error with {table}: {e}")
    
    # Reset account
    print()
    print("💰 Resetting account balance...")
    today = date.today().isoformat()
    try:
        cur.execute("""
            INSERT OR REPLACE INTO paper_account 
            (starting_capital, cash_balance, portfolio_value, unrealized_pnl, realized_pnl, total_pnl, last_updated, trading_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (100000.0, 100000.0, 100000.0, 0.0, 0.0, 0.0, datetime.now().isoformat(), today))
        print("   ✅ Account reset to $100,000.00")
    except Exception as e:
        print(f"   ❌ Error resetting account: {e}")
        import traceback
        traceback.print_exc()
    
    conn.commit()
    
    # Verify reset
    print()
    print("=" * 70)
    print("✅ VERIFICATION")
    print("=" * 70)
    
    cur.execute("SELECT COUNT(*) FROM paper_portfolio")
    after_count = cur.fetchone()[0]
    print(f"   Paper Portfolio positions: {after_count} (should be 0)")
    
    cur.execute("SELECT cash_balance, portfolio_value FROM paper_account ORDER BY id DESC LIMIT 1")
    account = cur.fetchone()
    if account:
        print(f"   Cash Balance: ${account[0]:,.2f}")
        print(f"   Portfolio Value: ${account[1]:,.2f}")
    
    conn.close()
    
    print()
    print("=" * 70)
    print("✅ RESET COMPLETE!")
    print("=" * 70)
    print(f"💾 Backup: {backup_path}")
    print(f"🗑️  Total rows cleared: {sum(tables_cleared.values())}")
    print()
    print("⚠️  IMPORTANT: Refresh your browser (Cmd+Shift+R / Ctrl+Shift+R)")
    print("   to clear any cached portfolio data!")
    print()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
