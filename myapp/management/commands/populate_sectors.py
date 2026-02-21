from django.core.management.base import BaseCommand
from myapp.models import Sector

class Command(BaseCommand):
    help = 'Safely populates the 14 required stock sectors'

    def handle(self, *args, **options):
        sectors = [
            "Commercial Banks",
            "Development Banks",
            "Microfinance",
            "Finance",
            "Investment",
            "Hotels & Tourism",
            "Manufacturing & Processing",
            "Others",
            "Hydropower",
            "Life Insurance",
            "Non-Life Insurance",
            "Mutual Fund",
            "Corporate Debentures",
            "Trading"
        ]

        self.stdout.write(self.style.SUCCESS('🚀 Starting sector population...'))
        
        created_count = 0
        for name in sectors:
            sector, created = Sector.objects.get_or_create(name=name)
            if created:
                self.stdout.write(f"✓ Created: {name}")
                created_count += 1
            else:
                self.stdout.write(f"- Already exists: {name}")

        self.stdout.write(self.style.SUCCESS(f'✅ Finished! {created_count} new sectors created.'))
