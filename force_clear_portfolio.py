#!/usr/bin/env python3
"""
Force Clear Portfolio - Directly clears all portfolio data
"""

import sqlite3
import os
import shutil
from datetime import datetime, date

DB_FILE = "portfolio.db"
BACKUP_DIR = "portfolio_backups"

print("=" * 70)
print("FORCE CLEARING PORTFOLIO")
print("=" * 70)
print()

if not os.path.exists(DB_FILE):
    print(f"❌ Database not found: {DB_FILE}")
    exit(1)

print(f"📁 Database: {os.path.abspath(DB_FILE)}")

# Backup
print("\n💾 Creating backup...")
os.makedirs(BACKUP_DIR, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = os.path.join(BACKUP_DIR, f"portfolio_backup_{timestamp}.db")
shutil.copy2(DB_FILE, backup_path)
print(f"✅ Backup: {backup_path}")

# Connect and clear
print("\n🗑️  Clearing all portfolio data...")
conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

# Get counts before
cur.execute("SELECT COUNT(*) FROM paper_portfolio")
before_count = cur.fetchone()[0]
print(f"   Before: {before_count} positions in paper_portfolio")

# Clear all tables
tables = ['paper_portfolio', 'paper_transactions', 'portfolio', 'transactions']
total_cleared = 0

for table in tables:
    try:
        cur.execute(f"DELETE FROM {table}")
        cleared = cur.rowcount
        total_cleared += cleared
        if cleared > 0:
            print(f"   ✅ Cleared {cleared} rows from {table}")
    except sqlite3.OperationalError as e:
        if "no such table" not in str(e).lower():
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

# Verify
cur.execute("SELECT COUNT(*) FROM paper_portfolio")
after_count = cur.fetchone()[0]
print(f"   After: {after_count} positions in paper_portfolio")

conn.close()

print()
print("=" * 70)
if after_count == 0:
    print("✅ SUCCESS: Portfolio cleared!")
else:
    print(f"⚠️  WARNING: Still {after_count} positions remaining")
print("=" * 70)
print(f"💾 Backup: {backup_path}")
print(f"🗑️  Total rows cleared: {total_cleared}")
print()
print("⚠️  Next steps:")
print("1. Restart your backend server (if running)")
print("2. Hard refresh browser (Cmd+Shift+R / Ctrl+Shift+R)")
print()
