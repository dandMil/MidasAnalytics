#!/usr/bin/env python3
"""
Reset Portfolio Script (Non-Interactive)

Automatically resets the portfolio with backup.
"""

import os
import sys
from services.paper_trading_service import reset_paper_account

def main():
    db_file = "portfolio.db"
    
    print("=" * 60)
    print("RESETTING PORTFOLIO")
    print("=" * 60)
    
    if not os.path.exists(db_file):
        print("📊 No portfolio database found - already empty")
        return
    
    print("🔄 Resetting portfolio (backup will be created automatically)...")
    
    try:
        result = reset_paper_account(starting_capital=100000.0, create_backup=True)
        
        print("\n✅ RESET COMPLETE!")
        print(f"💰 Starting Capital: ${result['starting_capital']:,.2f}")
        print(f"💵 Cash Balance: ${result['cash_balance']:,.2f}")
        
        if result.get('backup_created'):
            print(f"💾 Backup: {result['backup_path']}")
        
        print("\n✅ Portfolio is now reset and ready for new trades!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
