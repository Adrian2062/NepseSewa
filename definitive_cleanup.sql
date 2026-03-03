-- Definitive Cleanup SQL
DELETE FROM nepse_prices WHERE symbol ~ '^[0-9]';
DELETE FROM stocks WHERE symbol ~ '^[0-9]';
DELETE FROM orders WHERE symbol ~ '^[0-9]';
DELETE FROM portfolio WHERE symbol ~ '^[0-9]';
DELETE FROM trade_executions WHERE symbol ~ '^[0-9]';
DELETE FROM trades WHERE symbol ~ '^[0-9]';
DELETE FROM watchlist WHERE symbol ~ '^[0-9]';
DELETE FROM stock_recommendations WHERE symbol ~ '^[0-9]';

-- Check counts
SELECT 'Remaining Numeric Stocks' as category, count(*) FROM stocks WHERE symbol ~ '^[0-9]';
SELECT 'Total Stocks' as category, count(*) FROM stocks;
