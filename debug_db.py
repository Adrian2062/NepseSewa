import psycopg2
import re

try:
    conn = psycopg2.connect(
        dbname="nepse_sewa",
        user="postgres",
        password="Adrian@2062",
        host="localhost"
    )
    cur = conn.cursor()
    
    # 1. Check latest timestamp
    cur.execute("SELECT MAX(timestamp) FROM myapp_nepseprice")
    latest_ts = cur.fetchone()[0]
    print(f"Latest timestamp in NEPSEPrice: {latest_ts}")
    
    # 2. Check top 10 gainers in that timestamp
    cur.execute("""
        SELECT symbol, change_pct 
        FROM myapp_nepseprice 
        WHERE timestamp = %s 
        ORDER BY change_pct DESC 
        LIMIT 10
    """, (latest_ts,))
    print("\nTop 10 Gainers in DB:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}%")
        
    # 3. Search for ANY symbol containing digits
    cur.execute("SELECT DISTINCT symbol FROM myapp_nepseprice WHERE symbol ~ '[0-9]'")
    bad_symbols = [r[0] for r in cur.fetchall()]
    print(f"\nSymbols containing digits in NEPSEPrice: {bad_symbols}")
    
    cur.execute("SELECT DISTINCT symbol FROM stocks WHERE symbol ~ '[0-9]'")
    bad_stocks = [r[0] for r in cur.fetchall()]
    print(f"Symbols containing digits in Stocks: {bad_stocks}")
    
    # 4. If found, delete them
    if bad_symbols:
        print(f"\nDeleting {len(bad_symbols)} bad symbols from prices...")
        cur.execute("DELETE FROM myapp_nepseprice WHERE symbol ~ '[0-9]'")
        print(f"Deleted {cur.rowcount} records.")
        
    if bad_stocks:
        print(f"Deleting {len(bad_stocks)} bad symbols from stocks...")
        cur.execute("DELETE FROM stocks WHERE symbol ~ '[0-9]'")
        print(f"Deleted {cur.rowcount} records.")
        
    conn.commit()
    cur.close()
    conn.close()
    print("\nCleanup and investigation finished.")

except Exception as e:
    print(f"Error: {e}")
