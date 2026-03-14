# myapp/management/commands/clean_corrupted_stocks.py

from django.core.management.base import BaseCommand
from myapp.models import Stock, NEPSEPrice, Portfolio, Watchlist
import re

class Command(BaseCommand):
    help = 'Deletes corrupted stocks where the symbol is a number'

    def handle(self, *args, **options):
        self.stdout.write("Scanning for corrupted numerical stocks...")
        
        # Find all stocks where the symbol is strictly digits
        corrupted_stocks = Stock.objects.filter(symbol__regex=r'^\d+$')
        count = corrupted_stocks.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS("✅ No corrupted stocks found! Your database is clean."))
            return
            
        symbols = list(corrupted_stocks.values_list('symbol', flat=True))
        self.stdout.write(self.style.WARNING(f"⚠️ Found {count} corrupted symbols: {symbols}"))
        
        # NEPSEPrice, Portfolio, and Watchlist do not always use ForeignKeys in your setup, 
        # so we must manually delete related text-based references first.
        prices_deleted, _ = NEPSEPrice.objects.filter(symbol__in=symbols).delete()
        portfolios_deleted, _ = Portfolio.objects.filter(symbol__in=symbols).delete()
        watchlists_deleted, _ = Watchlist.objects.filter(symbol__in=symbols).delete()
        
        self.stdout.write(f"Deleted {prices_deleted} corrupted price records.")
        self.stdout.write(f"Deleted {portfolios_deleted} corrupted portfolio entries.")
        self.stdout.write(f"Deleted {watchlists_deleted} corrupted watchlist entries.")
        
        # Finally delete the stocks themselves
        corrupted_stocks.delete()
        
        self.stdout.write(self.style.SUCCESS(f"✅ Successfully deleted {count} corrupted stocks and cleaned the database."))