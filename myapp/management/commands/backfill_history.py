from django.core.management.base import BaseCommand
from myapp.models import Stock, NEPSEPrice
from django.utils import timezone
import datetime
import random
from decimal import Decimal

class Command(BaseCommand):
    help = 'Backfill 3 months of stock history with realistic mock data for DEMO'

    def handle(self, *args, **options):
        self.stdout.write("Starting 3-Month History Backfill...")
        
        # Get unique symbols from existing price data
        symbols = NEPSEPrice.objects.values_list('symbol', flat=True).distinct()
        
        if not symbols:
            self.stdout.write(self.style.WARNING("No symbols found in NEPSEPrice table. Please run the scraper first."))
            return
            
        end_date = timezone.now().date()
        start_date = end_date - datetime.timedelta(days=90)
        
        self.stdout.write(f"Generating data from {start_date} to {end_date}...")
        self.stdout.write(f"Found {len(symbols)} symbols to process...")
        
        created_count = 0
        
        for symbol in symbols:
            # Get latest price to start walking backwards from, or default
            latest = NEPSEPrice.objects.filter(symbol=symbol).order_by('-timestamp').first()
            if latest:
                current_price = float(latest.ltp)
            else:
                current_price = random.uniform(100, 1000) # Default start
                
            # Walk backwards
            for i in range(90):
                date = end_date - datetime.timedelta(days=i)
                
                # Skip if already exists (optional, or just overwrite)
                # For speed, we just create bulk? No, loop is safer.
                
                # Verify weekday (NEPSE closed Fri/Sat usually, but let's just do Mon-Thu+Sun for strictness? 
                # Or just simple Mon-Fri for demo logic. Let's do Mon-Fri + Sun? 
                # Actually, simplest is just exclude Saturday.)
                if date.weekday() == 5: # Saturday
                    continue
                    
                # Calculate previous day's price (reverse logic)
                # If current is X, previous was X / (1 + change)
                change_pct = random.uniform(-2.5, 2.5)
                # So prev_price * (1 + change/100) = current_price
                # prev_price = current_price / (1 + change/100)
                
                # Wait, we are generating FORWARD from past or BACKWARD from now?
                # BACKWARD is easier to match current LTPS.
                # Today is 100. Yesterday was... 
                # If yesterday was 98, and change +2%, then today 100.
                # So Yesterday = Today / (1 + change/100)
                
                prev_price = current_price / (1 + (change_pct / 100))
                
                # Create the record for 'date' (which is the loop date)
                # Wait, if I iterate backwards (i=0 is today), I am creating record for today? 
                # No, today already exists. I should skip today.
                if i == 0 and latest and latest.timestamp.date() == end_date:
                    current_price = prev_price
                    continue

                # Generate OHLC
                daily_volatility = random.uniform(0.5, 3.0)
                open_p = prev_price * (1 + random.uniform(-0.5, 0.5)/100)
                high_p = max(prev_price, open_p) * (1 + (daily_volatility/100))
                low_p = min(prev_price, open_p) * (1 - (daily_volatility/100))
                close_p = prev_price
                
                # Volume
                volume = random.randint(100, 50000)
                turnover = volume * close_p
                
                NEPSEPrice.objects.update_or_create(
                    symbol=symbol,
                    timestamp=datetime.datetime.combine(date, datetime.time(15, 0), tzinfo=timezone.get_current_timezone()),
                    defaults={
                        'open': round(open_p, 2),
                        'high': round(high_p, 2),
                        'low': round(low_p, 2),
                        'close': round(close_p, 2),
                        'ltp': round(close_p, 2),
                        'change_pct': round(change_pct, 2),
                        'volume': volume,
                        'turnover': round(turnover, 2)
                    }
                )
                created_count += 1
                
                # Update current_price for next iteration (which is previous day)
                current_price = prev_price
                
        self.stdout.write(self.style.SUCCESS(f"Successfully created {created_count} historical records."))
