import os
import django
from django.db.models import Q

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

from myapp.models import Stock, Sector

print("--- Sectors in DB ---")
for s in Sector.objects.all():
    print(f"'{s.name}'")

print("\n--- Stock Check ---")
for sym in ['RSML', 'SABBL']:
    s = Stock.objects.filter(symbol__iexact=sym).first()
    if s:
        sec_name = s.sector.name if s.sector else "None"
        print(f"Symbol: {s.symbol} (Stored as: {repr(s.symbol)})")
        print(f"Sector: {sec_name} (Stored as: {repr(sec_name)})")
        print(f"Locked: {s.sector_locked}")
    else:
        print(f"Symbol {sym} not found.")

print("\n--- Testing Filter Match ---")
# Manufacturing & Processing
m_sec = "Manufacturing & Processing"
exists = Sector.objects.filter(name__iexact=m_sec).exists()
print(f"Filter '{m_sec}' exists: {exists}")

# Development Banks
d_sec = "Development Banks"
exists = Sector.objects.filter(name__iexact=d_sec).exists()
print(f"Filter '{d_sec}' exists: {exists}")
