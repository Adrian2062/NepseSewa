from django.core.management.base import BaseCommand
from myapp.models import (
    Stock, NEPSEPrice, Order, Portfolio, 
    TradeExecution, Watchlist, StockRecommendation
)
import re

class Command(BaseCommand):
    help = 'Clean up corrupted stock symbols (numeric) from the database'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Searching for corrupted stock symbols across all models...")
        
        models_to_clean = [
            Stock, NEPSEPrice, Order, Portfolio, 
            TradeExecution, Watchlist, StockRecommendation
        ]
        total_deleted = 0
        
        for model in models_to_clean:
            model_name = model.__name__
            # Use regex for ANY symbol containing a digit (e.g. "29.", "84 ")
            if model_name == 'Stock':
                # Special handling for Stock to log symbols
                bad_stocks = Stock.objects.filter(symbol__regex=r'[0-9]')
                for s in bad_stocks:
                    self.stdout.write(f"  ❌ Deleting Stock: {s.symbol}")
                    s.delete()
                    total_deleted += 1
            else:
                # Bulk delete for other models
                # Filter by symbol if the model has a symbol field
                if hasattr(model, 'symbol'):
                    deleted_count = model.objects.filter(symbol__regex=r'[0-9]').delete()[0]
                    if deleted_count > 0:
                        self.stdout.write(f"  ❌ Deleted {deleted_count} records from {model_name}")
                        total_deleted += deleted_count
        
        if total_deleted > 0:
            self.stdout.write(self.style.SUCCESS(f"✅ Cleanup completed! Total records deleted: {total_deleted}"))
        else:
            self.stdout.write(self.style.SUCCESS("✨ No corrupted numeric symbols found."))
