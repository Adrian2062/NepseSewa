import os
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

from myapp.models import Stock, NEPSEPrice, Sector

def check_stock(symbol):
    print(f"\n--- Checking {symbol} ---")
    s = Stock.objects.filter(symbol__iexact=symbol).first()
    if s:
        print(f"Stock Table: Symbol={repr(s.symbol)}, Sector={repr(s.sector.name if s.sector else 'None')}, Locked={s.sector_locked}")
    else:
        print(f"Stock Table: {symbol} NOT FOUND")
    
    latest_price = NEPSEPrice.objects.filter(symbol__iexact=symbol).order_by('-timestamp').first()
    if latest_price:
        print(f"Price Table: Symbol={repr(latest_price.symbol)}, Date={latest_price.timestamp.date()}, LTP={latest_price.ltp}")
    else:
        print(f"Price Table: {symbol} NO PRICES FOUND")

check_stock('RSML')
check_stock('SABBL')

print("\n--- Sectors ---")
for sec in Sector.objects.all():
    print(f"'{sec.name}'")
