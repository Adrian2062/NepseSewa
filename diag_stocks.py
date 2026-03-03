import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

from myapp.models import Stock, Sector
from django.db.models import Count

print(f'Total Stocks: {Stock.objects.count()}')
print(f'Total Sectors: {Sector.objects.count()}')
print(f'Stocks without sector: {Stock.objects.filter(sector__isnull=True).count()}')

print('\nSector counts:')
counts = Stock.objects.values('sector__name').annotate(count=Count('id')).order_by('-count')
for c in counts:
    sector_name = c['sector__name'] or 'None'
    print(f"{sector_name}: {c['count']}")

print('\nSample stocks with their sectors:')
sample_stocks = Stock.objects.select_related('sector').all()[:10]
for s in sample_stocks:
    print(f"Symbol: {s.symbol}, Sector: {s.sector.name if s.sector else 'None'}")
