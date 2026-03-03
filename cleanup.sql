-- Final Cleanup Query for PostgreSQL
DELETE FROM nepse_prices WHERE symbol ~ '^[^A-Za-z]';
DELETE FROM stocks WHERE symbol ~ '^[^A-Za-z]';
SELECT count(*) as remaining_stocks FROM stocks;
