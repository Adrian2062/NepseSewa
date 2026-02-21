import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

from myapp.models import Stock, NEPSEPrice
from django.db.models.functions import Trim

def cleanup():
    print("--- Starting Symbol Cleanup ---")
    
    # 1. Cleanup Stocks
    stocks = Stock.objects.all()
    stock_count = 0
    for s in stocks:
        clean_sym = s.symbol.strip().upper()
        if s.symbol != clean_sym:
            print(f"Fixing Stock: '{s.symbol}' -> '{clean_sym}'")
            s.symbol = clean_sym
            s.save()
            stock_count += 1
    print(f"Cleaned {stock_count} Stocks.")

    # 2. Cleanup NEPSEPrice (might be many)
    # We'll use a bulk update approach if possible, but for safest results across all DBs:
    print("Cleaning NEPSEPrice symbols (this might take a moment)...")
    from django.db.models import F
    
    # In Postgres/SQLite, we can try to do this efficiently
    try:
        updated_count = NEPSEPrice.objects.annotate(trimmed=Trim('symbol')).exclude(symbol=F('trimmed')).update(symbol=Trim('symbol'))
        print(f"Cleaned {updated_count} NEPSEPrice records via bulk update.")
    except Exception as e:
        print(f"Bulk update failed, falling back to iteration. Error: {e}")
        # Fallback for complex DBs
        prices = NEPSEPrice.objects.all()
        p_count = 0
        for p in prices:
            clean = p.symbol.strip().upper()
            if p.symbol != clean:
                p.symbol = clean
                p.save()
                p_count += 1
        print(f"Cleaned {p_count} NEPSEPrice records manually.")

if __name__ == "__main__":
    cleanup()
