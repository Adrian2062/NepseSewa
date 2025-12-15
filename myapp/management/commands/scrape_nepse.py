from django.core.management.base import BaseCommand
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
from django.utils import timezone
import chromedriver_autoinstaller
from myapp.models import NEPSEPrice
from datetime import datetime

chromedriver_autoinstaller.install()

class Command(BaseCommand):
    help = 'Scrape NEPSE stock prices and save to PostgreSQL'

    def add_arguments(self, parser):
        parser.add_argument('--interval', type=int, default=60, help='Scraping interval in seconds')
        parser.add_argument('--once', action='store_true', help='Run once and exit')

    def handle(self, *args, **options):
        interval = options['interval']
        run_once = options['once']
        
        self.stdout.write(self.style.SUCCESS('Starting NEPSE scraper...'))
        
        if run_once:
            self.scrape_and_save()
        else:
            self.stdout.write(f'Scraping every {interval} seconds. Press Ctrl+C to stop.')
            iteration = 0
            while True:
                try:
                    iteration += 1
                    self.stdout.write(f'\n--- Iteration {iteration} ---')
                    self.scrape_and_save()
                    self.stdout.write(f'⏳ Waiting {interval} seconds...')
                    time.sleep(interval)
                except KeyboardInterrupt:
                    self.stdout.write(self.style.WARNING('\n✓ Scraper stopped.'))
                    break
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error in main loop: {e}'))
                    time.sleep(10)

    def scrape_and_save(self):
        """Scrape NEPSE data and save to PostgreSQL"""
        options = Options()
        options.headless = True
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        driver = webdriver.Chrome(options=options)
        
        try:
            timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.stdout.write(f'[{timestamp_str}] Loading NEPSE website...')
            
            driver.get("https://www.sharesansar.com/today-share-price")
            time.sleep(10)  # Wait for page to fully load
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Find table with the correct class selector
            table = soup.find("table", {
                "class": "table table-bordered table-striped table-hover dataTable compact no-footer"
            })
            
            if not table:
                self.stdout.write(self.style.ERROR('❌ Table not found'))
                return
            
            self.stdout.write('✓ Table found')
            
            # Extract all rows from table
            rows = []
            for tr in table.find_all("tr"):
                cols = [td.get_text(strip=True) for td in tr.find_all(["th", "td"])]
                if cols:
                    rows.append(cols)
            
            if len(rows) <= 1:
                self.stdout.write(self.style.WARNING('⚠️  No data rows found'))
                return
            
            # First row is header
            headers = rows[0]
            self.stdout.write(f'✓ Headers: {", ".join(headers[:6])}...')
            
            # Parse data rows
            data_rows = rows[1:]
            timestamp = timezone.now()
            saved_count = 0
            
            for idx, row in enumerate(data_rows):
                try:
                    if not row or len(row) < 2:
                        continue
                    
                    # Map headers to values
                    row_dict = {}
                    for i, header in enumerate(headers):
                        if i < len(row):
                            row_dict[header] = row[i]
                    
                    # Get symbol (usually first column)
                    symbol = row_dict.get('Symbol', row[0] if row else None)
                    
                    if not symbol or symbol == '' or symbol == 'Symbol':
                        continue
                    
                    # Helper to clean numeric values
                    def clean_number(val):
                        if val is None or val == '' or val == '--':
                            return None
                        try:
                            cleaned = str(val).replace(',', '').replace('%', '').strip()
                            return float(cleaned) if cleaned else None
                        except (ValueError, AttributeError, TypeError):
                            return None
                    
                    # Extract values from row dict
                    open_price = clean_number(row_dict.get('Open'))
                    high = clean_number(row_dict.get('High'))
                    low = clean_number(row_dict.get('Low'))
                    close = clean_number(row_dict.get('Close'))
                    ltp = clean_number(row_dict.get('LTP'))
                    change_pct = clean_number(row_dict.get('Diff %'))
                    volume = clean_number(row_dict.get('Vol'))
                    turnover = clean_number(row_dict.get('Turnover'))
                    
                    # Save to database
                    NEPSEPrice.objects.create(
                        symbol=symbol,
                        timestamp=timestamp,
                        open=open_price,
                        high=high,
                        low=low,
                        close=close,
                        ltp=ltp,
                        change_pct=change_pct,
                        volume=volume,
                        turnover=turnover,
                    )
                    saved_count += 1
                
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'⚠️  Skip row {idx}: {str(e)[:60]}'))
                    continue
            
            if saved_count > 0:
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Saved {saved_count} records at {timestamp.strftime("%H:%M:%S")}'
                ))
            else:
                self.stdout.write(self.style.WARNING('⚠️  No records saved'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Scraping error: {str(e)}'))
        
        finally:
            driver.quit()