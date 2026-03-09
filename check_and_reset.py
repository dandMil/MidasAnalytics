#!/usr/bin/env python3
"""
Check and Reset Portfolio - Direct Database Access
"""

import sqlite3
import os
import shutil
from datetime import datetime, date

DB_FILE = "portfolio.db"

def main():
    print("=" * 70)
    print("PORTFOLIO CHECK & RESET")
    print("=" * 70)
    print()
    
    if not os.path.exists(DB_FILE):
        print("❌ Database file not found!")
        return
    
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Check what tables exist
    print("📋 Checking database tables...")
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cur.fetchall()]
    print(f"   Found tables: {', '.join(tables)}")
    print()
    
    # Check paper_portfolio
    print("📊 Checking paper_portfolio...")
    try:
        cur.execute("SELECT COUNT(*) FROM paper_portfolio")
        count = cur.fetchone()[0]
        print(f"   Positions: {count}")
        
        if count > 0:
            cur.execute("SELECT ticker, shares, entry_price FROM paper_portfolio LIMIT 10")
            positions = cur.fetchall()
            print("   Current positions:")
            for pos in positions:
                print(f"      - {pos[0]}: {pos[1]} shares @ ${pos[2]:.2f}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    
    # Check regular portfolio
    print("📊 Checking portfolio (regular)...")
    try:
        cur.execute("SELECT COUNT(*) FROM portfolio")
        count = cur.fetchone()[0]
        print(f"   Positions: {count}")
        
        if count > 0:
            cur.execute("SELECT ticker, shares, price FROM portfolio LIMIT 10")
            positions = cur.fetchall()
            print("   Current positions:")
            for pos in positions:
                print(f"      - {pos[0]}: {pos[1]} shares @ ${pos[2]:.2f}")
    except Exception as e:
        print(f"   Table doesn't exist or error: {e}")
    
    print()
    
    # Check account
    print("💰 Checking account...")
    try:
        cur.execute("SELECT starting_capital, cash_balance, portfolio_value FROM paper_account ORDER BY id DESC LIMIT 1")
        account = cur.fetchone()
        if account:
            print(f"   Starting Capital: ${account[0]:,.2f}")
            print(f"   Cash Balance: ${account[1]:,.2f}")
            print(f"   Portfolio Value: ${account[2]:,.2f}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print()
    print("=" * 70)
    
    # Ask to reset
    response = input("\n🔄 Reset portfolio? (y/n): ").strip().lower()
    
    if response == 'y':
        print("\n💾 Creating backup...")
        backup_dir = "portfolio_backups"
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_dir}/portfolio_backup_{timestamp}.db"
        shutil.copy2(DB_FILE, backup_file)
        print(f"   ✅ Backup: {backup_file}")
        
        print("\n🗑️  Clearing all portfolio data...")
        
        # Clear all portfolio tables
        cleared = 0
        for table in ['paper_portfolio', 'paper_transactions', 'portfolio', 'transactions']:
            try:
                cur.execute(f"DELETE FROM {table}")
                rows = cur.rowcount
                if rows > 0:
                    print(f"   ✅ Cleared {rows} rows from {table}")
                    cleared += rows
            except Exception as e:
                print(f"   ⚠️  {table}: {e}")
        
        # Reset account
        print("\n💰 Resetting account...")
        today = date.today().isoformat()
        cur.execute("""
            INSERT OR REPLACE INTO paper_account 
            (starting_capital, cash_balance, portfolio_value, unrealized_pnl, realized_pnl, total_pnl, last_updated, trading_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (100000.0, 100000.0, 100000.0, 0.0, 0.0, 0.0, datetime.now().isoformat(), today))
        
        conn.commit()
        
        print("\n✅ RESET COMPLETE!")
        print(f"   💰 Starting Capital: $100,000.00")
        print(f"   💾 Backup: {backup_file}")
        print(f"   🗑️  Cleared: {cleared} total rows")
    else:
        print("\n❌ Reset cancelled")
    
    conn.close()
    print()

if __name__ == "__main__":
    main()
