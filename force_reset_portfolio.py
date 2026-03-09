#!/usr/bin/env python3
"""
Force Reset Portfolio - Clears ALL portfolio data

This script will:
1. Create a backup
2. Clear ALL portfolio tables (paper and regular)
3. Reset account to $100,000
"""

import os
import sys
import sqlite3
import shutil
from datetime import datetime, date

DB_FILE = "portfolio.db"
BACKUP_DIR = "portfolio_backups"

def main():
    print("=" * 60)
    print("FORCE RESET PORTFOLIO")
    print("=" * 60)
    print()
    
    if not os.path.exists(DB_FILE):
        print("📊 No portfolio database found - already empty")
        return
    
    # Create backup
    print("💾 Step 1: Creating backup...")
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"portfolio_backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    try:
        shutil.copy2(DB_FILE, backup_path)
        backup_size = os.path.getsize(backup_path)
        print(f"   ✅ Backup created: {backup_path} ({backup_size:,} bytes)")
    except Exception as e:
        print(f"   ❌ Backup failed: {e}")
        return
    
    print()
    print("🔄 Step 2: Clearing ALL portfolio data...")
    
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Get table names first
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cur.fetchall()]
    print(f"   Found tables: {', '.join(tables)}")
    
    # Clear all portfolio-related tables
    tables_to_clear = [
        'paper_portfolio',
        'paper_transactions',
        'portfolio',
        'transactions'
    ]
    
    cleared_count = 0
    for table in tables_to_clear:
        try:
            cur.execute(f"DELETE FROM {table}")
            count = cur.rowcount
            if count > 0:
                print(f"   ✅ Cleared {count} rows from {table}")
                cleared_count += count
        except sqlite3.OperationalError as e:
            print(f"   ⚠️  Table {table} doesn't exist or error: {e}")
    
    # Reset paper account
    print()
    print("💰 Step 3: Resetting account balance...")
    today = date.today().isoformat()
    cur.execute("""
        INSERT OR REPLACE INTO paper_account 
        (starting_capital, cash_balance, portfolio_value, unrealized_pnl, realized_pnl, total_pnl, last_updated, trading_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (100000.0, 100000.0, 100000.0, 0.0, 0.0, 0.0, datetime.now().isoformat(), today))
    
    conn.commit()
    conn.close()
    
    print()
    print("=" * 60)
    print("✅ PORTFOLIO RESET COMPLETE!")
    print("=" * 60)
    print(f"💰 Starting Capital: $100,000.00")
    print(f"💾 Backup: {backup_path}")
    print(f"🗑️  Cleared: {cleared_count} total rows")
    print()
    print("Your portfolio has been completely reset!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
