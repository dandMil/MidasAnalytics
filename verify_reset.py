#!/usr/bin/env python3
"""
Verify Portfolio Reset - Checks database and optionally API
"""

import sqlite3
import os
import sys
from datetime import datetime

DB_FILE = "portfolio.db"

def check_database():
    """Check database directly"""
    print("=" * 70)
    print("DATABASE VERIFICATION")
    print("=" * 70)
    print()
    
    if not os.path.exists(DB_FILE):
        print(f"❌ Database file not found: {DB_FILE}")
        print(f"   Current directory: {os.getcwd()}")
        return None
    
    print(f"✅ Database found: {os.path.abspath(DB_FILE)}")
    print(f"   Size: {os.path.getsize(DB_FILE):,} bytes")
    print()
    
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Check paper_portfolio
    try:
        cur.execute("SELECT COUNT(*) FROM paper_portfolio")
        count = cur.fetchone()[0]
        print(f"📊 Paper Portfolio Positions: {count}")
        
        if count > 0:
            cur.execute("SELECT ticker, shares, entry_price FROM paper_portfolio LIMIT 10")
            positions = cur.fetchall()
            print("\n   ⚠️  Current Positions (portfolio NOT empty):")
            for pos in positions:
                print(f"      - {pos[0]}: {pos[1]} shares @ ${pos[2]:.2f}")
            
            if count > 10:
                print(f"      ... and {count - 10} more positions")
        else:
            print("   ✅ Portfolio is EMPTY (reset successful!)")
    except Exception as e:
        print(f"   ❌ Error checking paper_portfolio: {e}")
        import traceback
        traceback.print_exc()
        count = None
    
    # Check regular portfolio
    try:
        cur.execute("SELECT COUNT(*) FROM portfolio")
        reg_count = cur.fetchone()[0]
        if reg_count > 0:
            print(f"\n⚠️  Regular Portfolio Positions: {reg_count}")
            cur.execute("SELECT ticker, shares, price FROM portfolio LIMIT 5")
            positions = cur.fetchall()
            for pos in positions:
                print(f"      - {pos[0]}: {pos[1]} shares @ ${pos[2]:.2f}")
    except:
        pass  # Table might not exist
    
    # Check account
    try:
        cur.execute("SELECT starting_capital, cash_balance, portfolio_value, total_pnl FROM paper_account ORDER BY id DESC LIMIT 1")
        account = cur.fetchone()
        if account:
            print(f"\n💰 Account Status:")
            print(f"   Starting Capital: ${account[0]:,.2f}")
            print(f"   Cash Balance: ${account[1]:,.2f}")
            print(f"   Portfolio Value: ${account[2]:,.2f}")
            print(f"   Total P&L: ${account[3]:,.2f}")
    except Exception as e:
        print(f"\n   ⚠️  Account check error: {e}")
    
    conn.close()
    return count

def check_api_instructions():
    """Provide instructions for checking API"""
    print()
    print("=" * 70)
    print("API VERIFICATION INSTRUCTIONS")
    print("=" * 70)
    print()
    print("To check if the API returns the correct data, run:")
    print()
    print("  curl http://localhost:8000/midas/paper_trade/portfolio")
    print()
    print("Or in Python:")
    print()
    print("  import requests")
    print("  response = requests.get('http://localhost:8000/midas/paper_trade/portfolio')")
    print("  print(response.json())")
    print()
    print("Expected result: [] (empty array)")
    print()

def main():
    print()
    print("🔍 PORTFOLIO RESET VERIFICATION")
    print()
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check database
    db_count = check_database()
    
    # Summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    
    if db_count is None:
        print("❌ Could not check database")
    elif db_count == 0:
        print("✅ SUCCESS: Database shows EMPTY portfolio")
        print("   The reset worked correctly!")
        print()
        print("Next steps:")
        print("1. If your backend server is running, restart it")
        print("2. Hard refresh your browser (Cmd+Shift+R / Ctrl+Shift+R)")
        print("3. Check the API endpoint to verify it returns []")
    else:
        print(f"⚠️  WARNING: Database still has {db_count} positions")
        print("   The portfolio was NOT reset")
        print()
        print("To reset, run:")
        print("  python3 direct_reset.py")
    
    # API instructions
    check_api_instructions()
    
    print("=" * 70)
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Verification cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
