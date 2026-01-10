from django.core.management.base import BaseCommand
from myapp.models import Stock, NEPSEPrice
from django.db import transaction

class Command(BaseCommand):
    help = 'Clean up symbol whitespace and casing in Stock and NEPSEPrice tables'

    def handle(self, *args, **options):
        self.stdout.write("Starting Symbol Cleanup...")
        
        with transaction.atomic():
            # 1. Clean Stock table
            stocks = Stock.objects.all()
            stock_count = 0
            for s in stocks:
                clean = s.symbol.strip().upper()
                if clean != s.symbol:
                    s.symbol = clean
                    s.save()
                    stock_count += 1
            
            self.stdout.write(self.style.SUCCESS(f"Cleaned {stock_count} entries in Stock table"))

            # 2. Clean NEPSEPrice table
            # Note: This might be large, so we use update() for bulk if possible,
            # but standardizing symbols in bulk is tricky with F expressions for stripping.
            # Let's do a more efficient approach for large tables if needed.
            
            # For NEPSEPrice, we check if any have spaces
            prices_with_spaces = NEPSEPrice.objects.filter(symbol__contains=' ')
            price_count = prices_with_spaces.count()
            
            if price_count > 0:
                self.stdout.write(f"Standardizing {price_count} symbols in NEPSEPrice table...")
                # We can't easily use .update(symbol=Trim('symbol')) in standard Django without extras
                # So we iterate in chunks if needed
                total_updated = 0
                for p in prices_with_spaces.iterator():
                    p.symbol = p.symbol.strip().upper()
                    p.save()
                    total_updated += 1
                self.stdout.write(self.style.SUCCESS(f"Updated {total_updated} symbols in NEPSEPrice"))
            else:
                self.stdout.write(self.style.SUCCESS("No symbols with whitespace found in NEPSEPrice"))

        self.stdout.write(self.style.SUCCESS("Cleanup complete!"))
