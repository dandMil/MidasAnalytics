#!/usr/bin/env python3
"""
Reset Portfolio Script

This script will:
1. Create a backup of the current portfolio database
2. Reset the portfolio (clear all positions and transactions)
3. Reset account balance to $100,000

Usage:
    python3 reset_portfolio.py
"""

import os
import sys
from datetime import datetime
from services.paper_trading_service import reset_paper_account, backup_portfolio_db

def main():
    db_file = "portfolio.db"
    
    print("=" * 60)
    print("PORTFOLIO RESET SCRIPT")
    print("=" * 60)
    print()
    
    # Check if database exists
    if not os.path.exists(db_file):
        print("📊 No portfolio database found")
        print("✅ Portfolio is already empty - ready for new trades")
        return
    
    db_size = os.path.getsize(db_file)
    print(f"📊 Found portfolio database ({db_size:,} bytes)")
    print()
    
    # Create backup
    print("💾 Step 1: Creating backup...")
    backup_path = backup_portfolio_db()
    
    if backup_path:
        backup_size = os.path.getsize(backup_path)
        print(f"   ✅ Backup created successfully!")
        print(f"   📁 Location: {backup_path}")
        print(f"   📦 Size: {backup_size:,} bytes ({backup_size / 1024:.2f} KB)")
    else:
        print("   ⚠️  Warning: Backup creation failed")
        response = input("   Continue with reset anyway? (y/n): ")
        if response.lower() != 'y':
            print("   ❌ Reset cancelled")
            return
    
    print()
    print("🔄 Step 2: Resetting portfolio...")
    
    # Reset portfolio
    result = reset_paper_account(starting_capital=100000.0, create_backup=False)
    
    print()
    print("=" * 60)
    print("✅ PORTFOLIO RESET COMPLETE")
    print("=" * 60)
    print()
    print(f"💰 Starting Capital: ${result['starting_capital']:,.2f}")
    print(f"💵 Cash Balance: ${result['cash_balance']:,.2f}")
    if backup_path:
        print(f"💾 Backup: {backup_path}")
    print()
    print("Your portfolio has been reset and is ready for new trades!")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Reset cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
