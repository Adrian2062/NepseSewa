@echo off
set PGPASSWORD=Adrian@2062
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -U postgres -d nepse_sewa -c "DELETE FROM nepse_prices WHERE symbol ~ '^[^A-Za-z]';"
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -U postgres -d nepse_sewa -c "DELETE FROM stocks WHERE symbol ~ '^[^A-Za-z]';"
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -U postgres -d nepse_sewa -c "SELECT count(*) as remaining_stocks FROM stocks;"
