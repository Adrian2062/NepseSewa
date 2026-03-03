import psycopg2
import sys

def cleanup():
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            dbname='nepse_sewa',
            user='postgres',
            password='Adrian@2062'
        )
        conn.autocommit = True
        cur = conn.cursor()

        print("Connected to PostgreSQL successfully.")

        # Identify bad symbols
        cur.execute("SELECT symbol FROM stocks WHERE symbol ~ '^[0-9]';")
        bad_symbols = [row[0] for row in cur.fetchall()]
        print(f"Found {len(bad_symbols)} corrupted symbols: {bad_symbols}")

        if not bad_symbols:
            print("No numeric symbols found in 'stocks' table.")
        else:
            # Delete from nepse_prices first (due to FK if any, though likely just symbol string)
            cur.execute("DELETE FROM nepse_prices WHERE symbol ~ '^[0-9]';")
            print(f"Deleted records from nepse_prices matching numeric symbols.")

            # Delete from stocks
            cur.execute("DELETE FROM stocks WHERE symbol ~ '^[0-9]';")
            print(f"Deleted records from stocks matching numeric symbols.")

        # Also check for 'Uncategorized' if needed, but the user specifically showed numeric symbols.
        
        cur.close()
        conn.close()
        print("Cleanup completed successfully.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    cleanup()
