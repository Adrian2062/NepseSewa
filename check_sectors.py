import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

from myapp.models import Stock
from django.db.models import Count

sectors = Stock.objects.values('sector').annotate(count=Count('symbol')).order_by('-count')
with open('sector_counts.txt', 'w') as f:
    f.write("Sector Counts:\n")
    for s in sectors:
        f.write(f"{s['sector']}: {s['count']}\n")
print("Done")
