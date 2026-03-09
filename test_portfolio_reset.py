#!/usr/bin/env python3
"""
Test Portfolio Reset - Verifies database and API state
"""

import sqlite3
import os
import requests
import json
from datetime import datetime

DB_FILE = "portfolio.db"
API_BASE = "http://localhost:8000"

def check_database():
    """Check database directly"""
    print("=" * 70)
    print("DATABASE CHECK")
    print("=" * 70)
    
    if not os.path.exists(DB_FILE):
        print(f"❌ Database file not found: {DB_FILE}")
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
            print("\n   Current Positions:")
            for pos in positions:
                print(f"      - {pos[0]}: {pos[1]} shares @ ${pos[2]:.2f}")
        else:
            print("   ✅ Portfolio is empty")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        count = None
    
    # Check account
    try:
        cur.execute("SELECT starting_capital, cash_balance, portfolio_value FROM paper_account ORDER BY id DESC LIMIT 1")
        account = cur.fetchone()
        if account:
            print(f"\n💰 Account:")
            print(f"   Starting Capital: ${account[0]:,.2f}")
            print(f"   Cash Balance: ${account[1]:,.2f}")
            print(f"   Portfolio Value: ${account[2]:,.2f}")
    except Exception as e:
        print(f"   ⚠️  Account check error: {e}")
    
    conn.close()
    return count

def check_api():
    """Check API endpoint"""
    print()
    print("=" * 70)
    print("API ENDPOINT CHECK")
    print("=" * 70)
    
    try:
        url = f"{API_BASE}/midas/paper_trade/portfolio"
        print(f"🌐 Calling: {url}")
        print()
        
        response = requests.get(url, timeout=5)
        
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                count = len(data)
                print(f"📊 API Returns: {count} positions")
                
                if count > 0:
                    print("\n   Positions from API:")
                    for i, pos in enumerate(data[:5], 1):
                        ticker = pos.get('ticker', 'N/A')
                        shares = pos.get('shares', 0)
                        entry_price = pos.get('entry_price', 0)
                        print(f"      {i}. {ticker}: {shares} shares @ ${entry_price:.2f}")
                    
                    if count > 5:
                        print(f"      ... and {count - 5} more")
                else:
                    print("   ✅ API returns empty portfolio (correct!)")
                
                return count
            else:
                print(f"   ⚠️  Unexpected response format: {type(data)}")
                print(f"   Response: {json.dumps(data, indent=2)[:500]}")
                return None
        else:
            print(f"   ❌ API Error: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Cannot connect to API at {API_BASE}")
        print("   ⚠️  Is your backend server running?")
        return None
    except requests.exceptions.Timeout:
        print(f"   ❌ API request timed out")
        return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def check_account_api():
    """Check account API endpoint"""
    print()
    print("=" * 70)
    print("ACCOUNT API CHECK")
    print("=" * 70)
    
    try:
        url = f"{API_BASE}/midas/paper_trade/account"
        print(f"🌐 Calling: {url}")
        
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"💰 Account from API:")
            print(f"   Starting Capital: ${data.get('starting_capital', 0):,.2f}")
            print(f"   Cash Balance: ${data.get('cash_balance', 0):,.2f}")
            print(f"   Portfolio Value: ${data.get('portfolio_value', 0):,.2f}")
            print(f"   Total P&L: ${data.get('total_pnl', 0):,.2f}")
            return data
        else:
            print(f"   ❌ Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
        return None

def main():
    print()
    print("🔍 PORTFOLIO RESET VERIFICATION TEST")
    print()
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check database
    db_count = check_database()
    
    # Check API
    api_count = check_api()
    
    # Check account API
    account_data = check_account_api()
    
    # Summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    if db_count is not None and api_count is not None:
        if db_count == 0 and api_count == 0:
            print("✅ SUCCESS: Both database and API show empty portfolio")
            print("   Your portfolio has been reset correctly!")
        elif db_count == api_count:
            print(f"⚠️  WARNING: Both database and API show {db_count} positions")
            print("   The portfolio was NOT reset, or positions were re-added")
        else:
            print(f"⚠️  MISMATCH: Database has {db_count} positions, API returns {api_count}")
            print("   There may be a caching issue or server needs restart")
    elif db_count is not None:
        if db_count == 0:
            print("✅ Database is empty")
            print("⚠️  Could not verify API (server may not be running)")
        else:
            print(f"⚠️  Database has {db_count} positions")
            print("⚠️  Could not verify API (server may not be running)")
    else:
        print("❌ Could not check database")
    
    print()
    print("=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    
    if db_count and db_count > 0:
        print("1. Run the reset script: python3 direct_reset.py")
    elif db_count == 0 and api_count and api_count > 0:
        print("1. Restart your backend server to clear API cache")
        print("2. Hard refresh your browser (Cmd+Shift+R / Ctrl+Shift+R)")
    elif db_count == 0 and (api_count is None or api_count == 0):
        print("1. ✅ Portfolio is reset correctly!")
        print("2. If frontend still shows old data, hard refresh browser")
        print("3. Check browser console for any errors")
    
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Test cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
