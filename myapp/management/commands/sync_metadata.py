from django.core.management.base import BaseCommand
from myapp.services.stock_service import StockService

class Command(BaseCommand):
    help = 'Sync company metadata (symbols, names, sectors) from Merolagani'

    def handle(self, *args, **options):
        self.stdout.write("🚀 Starting company metadata sync...")
        success = StockService.sync_company_metadata()
        if success:
            self.stdout.write(self.style.SUCCESS("✓ Company metadata sync completed successfully!"))
        else:
            self.stdout.write(self.style.ERROR("✗ Company metadata sync failed."))
