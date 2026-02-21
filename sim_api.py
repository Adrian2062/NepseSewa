import os
import django
from django.db.models.functions import Trim
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

from myapp.models import Stock, NEPSEPrice, Sector

def simulate_view(target_symbols=['RSML', 'SABBL']):
    print(f"--- Simulating View for {target_symbols} ---")
    
    # 1. Get Latest Date
    latest_entry = NEPSEPrice.objects.order_by('-timestamp').first()
    if not latest_entry:
        print("No prices in DB.")
        return
    filter_date = latest_entry.timestamp.date()
    print(f"Latest Price Date: {filter_date}")

    # 2. Fetch Prices for these symbols
    # (We simulate the unique_prices logic)
    qs = NEPSEPrice.objects.filter(timestamp__date=filter_date)
    all_prices = qs.values('symbol', 'ltp').order_by('symbol', '-timestamp')
    
    unique_prices = {}
    for p in all_prices:
        sym = p['symbol'].strip().upper()
        if sym not in unique_prices:
            unique_prices[sym] = p

    print(f"Symbols in unique_prices (top 5): {list(unique_prices.keys())[:5]}")
    
    for tsym in target_symbols:
        found = tsym in unique_prices
        print(f"Is {tsym} in unique_prices? {found}")

    # 3. Stock Meta Lookup
    found_symbols = list(unique_prices.keys())
    stock_qs = Stock.objects.annotate(clean_sym=Trim('symbol')).filter(clean_sym__in=found_symbols).select_related('sector')
    
    stock_info = {s.clean_sym.upper(): {
        'sector': s.sector.name if s.sector else 'Others',
        'company_name': s.company_name
    } for s in stock_qs}

    print("\n--- Metadata Results ---")
    for tsym in target_symbols:
        info = stock_info.get(tsym)
        if info:
            print(f"{tsym} Found in Stock Table: Sector='{info['sector']}', Company='{info['company_name']}'")
        else:
            print(f"{tsym} NOT FOUND in Stock Table batches.")
            # Let's see why by looking for it directly
            s_direct = Stock.objects.filter(symbol__icontains=tsym).first()
            if s_direct:
                print(f"  DIRECT LOOKUP found: symbol='{repr(s_direct.symbol)}', sector='{s_direct.sector.name if s_direct.sector else 'None'}'")
            else:
                print(f"  DIRECT LOOKUP also failed for {tsym}")

simulate_view()
