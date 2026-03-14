from django.core.management.base import BaseCommand
from myapp.models import NEPSEPrice, Stock
from django.utils import timezone
from django.db.models import Max

class Command(BaseCommand):
    help = 'Check how many stocks were scraped today'

    def handle(self, *args, **options):
        today = timezone.now().date()
        
        # 1. Total UNIQUE symbols scraped today
        unique_today = NEPSEPrice.objects.filter(timestamp__date=today).values('symbol').distinct().count()
        
        # 2. Latest batch count
        latest_time = NEPSEPrice.objects.filter(timestamp__date=today).aggregate(Max('timestamp'))['timestamp__max']
        
        self.stdout.write(f"\n--- STOCK DATA REPORT ({today}) ---")
        self.stdout.write(self.style.SUCCESS(f"Unique symbols found today: {unique_today}"))

        if latest_time:
            latest_batch_count = NEPSEPrice.objects.filter(timestamp=latest_time).count()
            self.stdout.write(f"Stocks found in the most recent scrape: {latest_batch_count}")
            self.stdout.write(f"Last update time: {latest_time}")
        else:
            self.stdout.write(self.style.WARNING("No data found for today yet."))

        self.stdout.write(f"Total rows in metadata table: {Stock.objects.count()}\n")