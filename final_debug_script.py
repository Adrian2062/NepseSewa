import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

from myapp.models import Stock, Sector, NEPSEPrice

with open('final_debug.txt', 'w') as f:
    f.write("--- SECTORS ---\n")
    for s in Sector.objects.all():
        f.write(f"'{s.name}' | len: {len(s.name)}\n")
        
    f.write("\n--- STOCKS ---\n")
    for sym in ['RSML', 'SABBL']:
        s = Stock.objects.filter(symbol__iexact=sym).first()
        if s:
            sec_name = s.sector.name if s.sector else "None"
            f.write(f"SYM: {s.symbol} | SEC: {sec_name} | LOK: {s.sector_locked}\n")
        else:
            f.write(f"SYM: {sym} NOT FOUND\n")

    f.write("\n--- LATEST PRICES ---\n")
    latest = NEPSEPrice.objects.order_by('-timestamp').first()
    if latest:
        date = latest.timestamp.date()
        f.write(f"Latest Date: {date}\n")
        prices = NEPSEPrice.objects.filter(timestamp__date=date, symbol__in=['RSML', 'SABBL'])
        for p in prices:
            f.write(f"Found Price: {p.symbol} at {p.timestamp}\n")
    else:
        f.write("No prices found at all.\n")
