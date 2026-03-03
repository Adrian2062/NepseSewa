import psycopg2
import re

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    dbname='nepse_sewa',
    user='postgres',
    password='Adrian@2062'
)

cur = conn.cursor()

# Delete corrupted nepse_prices
cur.execute("DELETE FROM nepse_prices WHERE symbol ~ '^[^A-Za-z]'")
deleted_prices = cur.rowcount
print(f"Deleted {deleted_prices} corrupted NEPSEPrice records.")

# Delete corrupted stocks
cur.execute("DELETE FROM stocks WHERE symbol ~ '^[^A-Za-z]'")
deleted_stocks = cur.rowcount
print(f"Deleted {deleted_stocks} corrupted Stock records.")

conn.commit()

# Verification
cur.execute("SELECT COUNT(*) FROM stocks")
total = cur.fetchone()[0]
print(f"Remaining stocks: {total}")

cur.execute("SELECT symbol FROM stocks WHERE symbol ~ '^[0-9]' LIMIT 5")
leftovers = cur.fetchall()
if leftovers:
    print(f"WARNING: Still found numeric symbols: {leftovers}")
else:
    print("Verification passed: No numeric-only symbols remain.")

cur.close()
conn.close()
print("Done!")
