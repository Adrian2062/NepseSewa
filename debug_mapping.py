import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

from myapp.models import Stock, NEPSEPrice

# Check if AHL exists in Stock table
try:
    s = Stock.objects.get(symbol='AHL')
    print(f"Stock Table: Symbol='{s.symbol}', Sector='{s.sector}'")
except Stock.DoesNotExist:
    print("Stock Table: AHL DOES NOT EXIST")

# Check if AHL exists in NEPSEPrice table
p = NEPSEPrice.objects.filter(symbol__icontains='AHL').order_by('-timestamp').first()
if p:
    print(f"NEPSEPrice Table: Symbol='{p.symbol}', Price={p.ltp}")
else:
    print("NEPSEPrice Table: AHL NOT FOUND")

# Check unique sectors
sectors = list(Stock.objects.values_list('sector', flat=True).distinct())
print(f"Unique Sectors in Stock table: {sectors}")
