-- Reset Portfolio SQL Script
-- Run with: sqlite3 portfolio.db < reset_portfolio.sql

-- Clear all positions
DELETE FROM paper_portfolio;
DELETE FROM paper_transactions;
DELETE FROM portfolio;
DELETE FROM transactions;

-- Reset account
INSERT OR REPLACE INTO paper_account 
(starting_capital, cash_balance, portfolio_value, unrealized_pnl, realized_pnl, total_pnl, last_updated, trading_date)
VALUES (100000.0, 100000.0, 100000.0, 0.0, 0.0, 0.0, datetime('now'), date('now'));

-- Verify
SELECT 'Positions remaining: ' || COUNT(*) FROM paper_portfolio;
SELECT 'Cash balance: $' || cash_balance FROM paper_account ORDER BY id DESC LIMIT 1;
