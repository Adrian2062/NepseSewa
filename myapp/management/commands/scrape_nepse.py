from django.core.management.base import BaseCommand
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime, timedelta
from django.utils import timezone
import chromedriver_autoinstaller
from myapp.models import NEPSEPrice

chromedriver_autoinstaller.install()

class Command(BaseCommand):
    help = 'Scrape NEPSE stock prices'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Scraping interval in seconds (default: 60)'
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help='Run once and exit'
        )

    def handle(self, *args, **options):
        interval = options['interval']
        run_once = options['once']
        
        self.stdout.write(self.style.SUCCESS('Starting NEPSE scraper...'))
        
        if run_once:
            self.scrape_data()
        else:
            self.stdout.write(f'Scraping every {interval} seconds. Press Ctrl+C to stop.')
            iteration = 0
            while True:
                try:
                    iteration += 1
                    self.stdout.write(f'\n--- Iteration {iteration} ---')
                    self.scrape_data()
                    self.stdout.write(f'Waiting {interval} seconds...')
                    time.sleep(interval)
                except KeyboardInterrupt:
                    self.stdout.write(self.style.WARNING('\nStopping scraper...'))
                    break
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error: {e}'))
                    time.sleep(10)

    def scrape_data(self):
        """Scrape NEPSE data and save to database"""
        try:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(60)
            
            self.stdout.write('Loading NEPSE website...')
            driver.get("https://www.sharesansar.com/today-share-price")
            
            time.sleep(3)
            
            # Wait for table
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "table"))
            )
            
            # Parse table
            soup = BeautifulSoup(driver.page_source, 'lxml')
            table = soup.find("table", {"class": "table"})
            
            if not table:
                self.stdout.write(self.style.ERROR('Table not found'))
                driver.quit()
                return
            
            # Extract data
            rows = []
            for row in table.find_all("tr")[1:]:  # Skip header
                cells = row.find_all("td")
                if len(cells) > 1:
                    try:
                        row_data = [cell.text.strip() for cell in cells]
                        if row_data[0]:  # Has symbol
                            rows.append(row_data)
                    except:
                        continue
            
            driver.quit()
            
            if not rows:
                self.stdout.write(self.style.WARNING('No data found'))
                return
            
            # Save to database
            current_time = timezone.now()
            saved_count = 0
            
            for row in rows:
                try:
                    symbol = row[0] if len(row) > 0 else None
                    if not symbol:
                        continue
                    
                    def clean_float(val):
                        if not val or val == '--':
                            return None
                        try:
                            return float(val.replace(',', ''))
                        except:
                            return None
                    
                    NEPSEPrice.objects.create(
                        symbol=symbol,
                        timestamp=current_time,
                        open=clean_float(row[2]) if len(row) > 2 else None,
                        high=clean_float(row[3]) if len(row) > 3 else None,
                        low=clean_float(row[4]) if len(row) > 4 else None,
                        close=clean_float(row[5]) if len(row) > 5 else None,
                        ltp=clean_float(row[6]) if len(row) > 6 else None,
                        change_pct=clean_float(row[8]) if len(row) > 8 else None,
                        volume=clean_float(row[10]) if len(row) > 10 else None,
                        turnover=clean_float(row[12]) if len(row) > 12 else None,
                    )
                    saved_count += 1
                except Exception as e:
                    continue
            
            self.stdout.write(self.style.SUCCESS(
                f'✓ Scraped {saved_count} records at {current_time.strftime("%H:%M:%S")}'
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Scraping error: {e}'))