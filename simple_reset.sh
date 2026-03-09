#!/bin/bash
# Simple Portfolio Reset Script

cd /Users/dandmil/Desktop/Projects/MidasAnalytics

echo "=================================="
echo "RESETTING PORTFOLIO"
echo "=================================="
echo ""

# Check if database exists
if [ ! -f "portfolio.db" ]; then
    echo "❌ Database not found!"
    exit 1
fi

# Create backup
echo "💾 Creating backup..."
mkdir -p portfolio_backups
BACKUP_FILE="portfolio_backups/portfolio_backup_$(date +%Y%m%d_%H%M%S).db"
cp portfolio.db "$BACKUP_FILE"
echo "✅ Backup: $BACKUP_FILE"
echo ""

# Reset using SQL
echo "🗑️  Clearing portfolio..."
sqlite3 portfolio.db << EOF
DELETE FROM paper_portfolio;
DELETE FROM paper_transactions;
DELETE FROM portfolio;
DELETE FROM transactions;
INSERT OR REPLACE INTO paper_account 
(starting_capital, cash_balance, portfolio_value, unrealized_pnl, realized_pnl, total_pnl, last_updated, trading_date)
VALUES (100000.0, 100000.0, 100000.0, 0.0, 0.0, 0.0, datetime('now'), date('now'));
EOF

# Verify
echo ""
echo "✅ Verification:"
sqlite3 portfolio.db "SELECT 'Positions: ' || COUNT(*) FROM paper_portfolio;"
sqlite3 portfolio.db "SELECT 'Cash: $' || cash_balance FROM paper_account ORDER BY id DESC LIMIT 1;"

echo ""
echo "=================================="
echo "✅ RESET COMPLETE!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Restart your backend server"
echo "2. Hard refresh browser (Cmd+Shift+R)"
echo ""
