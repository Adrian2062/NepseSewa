from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from myapp.models import NEPSEPrice, NEPSEIndex, MarketIndex, MarketSummary

class Command(BaseCommand):
    help = 'Cleanup historical data older than 3 months'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=180, help='Days of history to keep (default: 180)')
        parser.add_argument('--force', action='store_true', help='Force deletion without confirmation')

    def handle(self, *args, **options):
        days = options['days']
        force = options['force']
        
        # Calculate cutoff date
        cutoff_date = timezone.now() - timedelta(days=days)
        self.stdout.write(f"🧹 Cleaning up data older than {cutoff_date.date()} ({days} days)...")
        
        # Count records to be deleted
        price_count = NEPSEPrice.objects.filter(timestamp__lt=cutoff_date).count()
        index_count = NEPSEIndex.objects.filter(timestamp__lt=cutoff_date).count()
        market_idx_count = MarketIndex.objects.filter(timestamp__lt=cutoff_date).count()
        summary_count = MarketSummary.objects.filter(timestamp__lt=cutoff_date).count()
        
        total_count = price_count + index_count + market_idx_count + summary_count
        
        if total_count == 0:
            self.stdout.write(self.style.SUCCESS("✓ No old data found to clean up."))
            return
            
        self.stdout.write(f"Found {total_count} records to delete:")
        self.stdout.write(f"  • NEPSE Stock Prices: {price_count}")
        self.stdout.write(f"  • NEPSE Index: {index_count}")
        self.stdout.write(f"  • Market Indices: {market_idx_count}")
        self.stdout.write(f"  • Market Summaries: {summary_count}")
        
        if not force:
            confirm = input("Are you sure you want to delete these records? [y/N] ")
            if confirm.lower() != 'y':
                self.stdout.write(self.style.WARNING("Aborted."))
                return
        
        # Delete data properly
        NEPSEPrice.objects.filter(timestamp__lt=cutoff_date).delete()
        NEPSEIndex.objects.filter(timestamp__lt=cutoff_date).delete()
        MarketIndex.objects.filter(timestamp__lt=cutoff_date).delete()
        MarketSummary.objects.filter(timestamp__lt=cutoff_date).delete()
        
        self.stdout.write(self.style.SUCCESS(f"✓ Successfully deleted {total_count} historical records."))
