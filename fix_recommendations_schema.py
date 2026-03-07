import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

def fix_schema():
    with connection.cursor() as cursor:
        print("Checking stock_recommendations table schema...")
        
        # 1. Make extra_data nullable if it exists
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'stock_recommendations' AND column_name = 'extra_data'")
        if cursor.fetchone():
            print("Making 'extra_data' nullable...")
            cursor.execute("ALTER TABLE stock_recommendations ALTER COLUMN extra_data DROP NOT NULL")
        
        # 2. Add defaults or make other institutional columns nullable
        # Based on schema inspection: id, symbol, current_price, predicted_next_close, recommendation, trend, last_updated are NOT NULL.
        # Everything else should be nullable.
        
        columns_to_fix = ['rsi', 'expected_move', 'confidence', 'market_condition', 'reason', 'rmse', 'mae', 'predicted_return', 'market_state', 'valid_until']
        
        for col in columns_to_fix:
            cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = 'stock_recommendations' AND column_name = '{col}'")
            if cursor.fetchone():
                print(f"Ensuring '{col}' is nullable...")
                cursor.execute(f"ALTER TABLE stock_recommendations ALTER COLUMN {col} DROP NOT NULL")

    print("SUCCESS: Database schema fixed for stock_recommendations.")

if __name__ == "__main__":
    fix_schema()
