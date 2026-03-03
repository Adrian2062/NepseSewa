@echo off
set PGPASSWORD=Adrian@2062
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -U postgres -d nepse_sewa -f definitive_cleanup.sql
