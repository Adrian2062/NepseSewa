from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Fix missing sector column in stocks table'

    def handle(self, *args, **options):
        self.stdout.write("Attempting to add 'sector' column...")
        try:
            with connection.cursor() as cursor:
                cursor.execute("ALTER TABLE stocks ADD COLUMN IF NOT EXISTS sector VARCHAR(100) DEFAULT 'Others';")
                cursor.execute("CREATE INDEX IF NOT EXISTS stocks_sector_idx ON stocks (sector);")
            self.stdout.write(self.style.SUCCESS("Successfully added 'sector' column and index!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
