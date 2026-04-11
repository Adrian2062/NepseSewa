import datetime
import time
import re
from django.core.management.base import BaseCommand
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from django.utils import timezone
from myapp.models import NEPSEPrice, MarketIndex

class Command(BaseCommand):
    help = 'Scrape REAL historical closing prices and Indices from Merolagani archives'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=90, help='Number of days to go back')

    def handle(self, *args, **options):
        days_to_pull = options['days']
        self.stdout.write(self.style.SUCCESS(f"🚀 Starting REAL History Scrape for {days_to_pull} days..."))

        # Setup Headless Chrome
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        driver = webdriver.Chrome(options=chrome_options)

        end_date = datetime.date.today()
        
        for i in range(1, days_to_pull + 1):
            target_date = end_date - datetime.timedelta(days=i)
            
            # THE FIX: Properly indented skip logic for Sat (5) and Sun (6)
            if target_date.weekday() in [5, 6]: 
                continue

            date_str = target_date.strftime("%m/%d/%Y") # Merolagani URL format
            
            # 1. SCRAPE INDICES (For your Navbar % fixes)
            self.scrape_indices(driver, target_date, date_str)
            
            # 2. SCRAPE STOCK PRICES (For your Buy/Sell AI Model)
            self.scrape_prices(driver, target_date, date_str)

        driver.quit()
        self.stdout.write(self.style.SUCCESS("\n✨ Done! Database is now populated with REAL history."))

    def scrape_indices(self, driver, target_date, date_str):
        """Pulls NEPSE, Sensitive, and Float values for a specific date"""
        url = f"https://merolagani.com/MarketSummary.aspx?date={date_str}"
        try:
            driver.get(url)
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            tables = soup.find_all('table')
            
            timestamp = timezone.make_aware(datetime.datetime.combine(target_date, datetime.time(15, 0)))
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 2: continue
                    name = cells[0].get_text(strip=True)
                    if name in ['NEPSE Index', 'Sensitive Index', 'Float Index']:
                        val = float(cells[1].get_text(strip=True).replace(',', ''))
                        MarketIndex.objects.update_or_create(
                            index_name=name, timestamp=timestamp,
                            defaults={'value': val, 'change_pct': 0.0}
                        )
            self.stdout.write(f"   📊 Saved Indices for {target_date}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Index Error on {target_date}: {e}"))

    def scrape_prices(self, driver, target_date, date_str):
        """Pulls all stock closing prices for a specific date"""
        url = f"https://merolagani.com/TodaysSharePrice.aspx?date={date_str}"
        try:
            driver.get(url)
            time.sleep(3)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            table = soup.find('table', {'class': 'table-hover'})
            
            if not table: return

            timestamp = timezone.make_aware(datetime.datetime.combine(target_date, datetime.time(15, 0)))
            rows = table.find_all('tr')[1:] # Skip header
            
            count = 0
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 8: continue
                
                symbol = cols[0].text.strip().upper()
                try:
                    ltp = float(cols[2].text.strip().replace(',', ''))
                    high = float(cols[3].text.strip().replace(',', ''))
                    low = float(cols[4].text.strip().replace(',', ''))
                    open_p = float(cols[5].text.strip().replace(',', ''))
                    vol = float(cols[7].text.strip().replace(',', ''))

                    NEPSEPrice.objects.update_or_create(
                        symbol=symbol, timestamp=timestamp,
                        defaults={
                            'ltp': ltp, 'close': ltp, 'open': open_p,
                            'high': high, 'low': low, 'volume': vol
                        }
                    )
                    count += 1
                except: continue
            
            self.stdout.write(f"   ✅ Saved {count} stocks for {target_date}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"   ❌ Price Error on {target_date}: {e}"))