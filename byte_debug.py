import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

from myapp.models import Stock, Sector

def dump_string(label, s):
    if s is None:
        print(f"{label}: None")
        return
    print(f"{label}: '{s}'")
    print(f"  Length: {len(s)}")
    print(f"  Bytes:  {s.encode('utf-8')}")

print("--- TARGET DATA DUMP ---")
for sym in ['RSML', 'SABBL']:
    stock = Stock.objects.filter(symbol__iexact=sym).first()
    if stock:
        dump_string(f"{sym} Symbol", stock.symbol)
        dump_string(f"{sym} Sector Name", stock.sector.name if stock.sector else None)
    else:
        print(f"{sym} NOT FOUND IN STOCK TABLE")

print("\n--- SECTOR TABLE DUMP ---")
for s in Sector.objects.all():
    dump_string("Sector", s.name)
