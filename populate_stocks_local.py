import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

from myapp.models import Stock, Sector
from myapp.management.commands.populate_sectors import SECTOR_MAP

log_file = r'populate_log.txt'
with open(log_file, 'w') as f:
    f.write('Starting population...\n')
    
    sectors_created = 0
    stocks_created = 0
    stocks_assigned = 0

    for sector_name, symbols in SECTOR_MAP.items():
        sector_obj, created = Sector.objects.get_or_create(name=sector_name)
        if created:
            f.write(f'  ✓ Sector created: {sector_name}\n')
            sectors_created += 1
        else:
            f.write(f'  - Sector exists: {sector_name}\n')

        for symbol in symbols:
            symbol = symbol.strip().upper()
            stock, stock_created = Stock.objects.get_or_create(
                symbol=symbol,
                defaults={'company_name': symbol, 'sector': sector_obj}
            )
            if stock_created:
                stocks_created += 1
            elif stock.sector != sector_obj and not getattr(stock, 'sector_locked', False):
                stock.sector = sector_obj
                stock.save(update_fields=['sector'])
                stocks_assigned += 1
                
    f.write(f'\nDone! {sectors_created} sectors created, {stocks_created} stocks created, {stocks_assigned} stocks re-assigned.\n')
    f.write(f'Final Stock Count: {Stock.objects.count()}\n')
    print('Population script finished')
