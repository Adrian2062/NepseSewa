import logging
import re
from django.utils import timezone
from django.db import transaction
from myapp.models import Stock, Sector, NEPSEPrice
from .nepse_scraper import NepseScraperService
from bs4 import BeautifulSoup
import requests
import time

logger = logging.getLogger(__name__)

class StockService:
    # Standard sector names as requested by user
    SECTOR_MAPPING = {
        "Commercial Bank": "Commercial Banks",
        "Commercial Banks Limited": "Commercial Banks",
        "Development Bank Limited": "Development Banks",
        "Development Bank": "Development Banks",
        "Development Banks": "Development Banks",
        "Hotels And Tourism": "Hotels & Tourism",
        "Hotel And Tourism": "Hotels & Tourism",
        "Manufacturing And Processing": "Manufacturing & Processing",
        "Hydro Power": "Hydropower",
        "Non Life Insurance": "Non-Life Insurance",
        "Mutual Funds": "Mutual Fund",
        "Corporate Debenture": "Corporate Debentures",
        "Tradings": "Trading",
        "Uncategorized": "Others",
    }

    @staticmethod
    def get_standard_sector(name):
        """Map scraped sector names to standardized names"""
        clean_name = name.strip()
        return StockService.SECTOR_MAPPING.get(clean_name, clean_name)

    @staticmethod
    def sync_company_metadata():
        """
        Scrape NEPSE company list from Merolagani and update Stock/Sector models.
        Handles both table-based and header-based structures.
        """
        logger.info("Starting company metadata sync...")
        url = "https://merolagani.com/CompanyList.aspx"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            sync_count = 0
            
            # --- Method 1: Table-based scraping (Legacy/Detailed) ---
            table = soup.find('table', {'id': 'ctl00_ContentPlaceHolder1_gvCompany'})
            if not table:
                table = soup.find('table', class_='table')
                
            if table:
                rows = table.find_all('tr')[1:]
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        symbol = cols[0].get_text(strip=True).upper()
                        name = cols[1].get_text(strip=True)
                        sector_name = cols[2].get_text(strip=True)
                        
                        if symbol and sector_name:
                            standard_name = StockService.get_standard_sector(sector_name)
                            sector_obj, _ = Sector.objects.get_or_create(name=standard_name)
                            
                            # Check if stock exists and has sector locked
                            stock_obj = Stock.objects.filter(symbol=symbol).first()
                            if stock_obj and stock_obj.sector_locked:
                                # Update fields EXCEPT sector
                                Stock.objects.filter(symbol=symbol).update(
                                    company_name=name,
                                    is_active=True
                                )
                            else:
                                # Standard update_or_create
                                Stock.objects.update_or_create(
                                    symbol=symbol,
                                    defaults={'company_name': name, 'sector': sector_obj, 'is_active': True}
                                )
                            sync_count += 1

            # --- Method 2: Header-based scraping (Modern Merolagani UI) ---
            # This handles cases where stocks are listed under H3/H4 headers
            # We iterate through all headers to find sectors
            headers = soup.find_all(['h3', 'h4'])
            numeric_pattern = re.compile(r'^[\d,]+$')
            
            for header in headers:
                sector_name = header.get_text(strip=True)
                
                # Validation: Ignore if empty, known nav items, or numeric strings (common mistakes)
                if not sector_name or sector_name.lower() in ['search', 'filter', 'navigation']:
                    continue
                if numeric_pattern.match(sector_name):
                    continue
                
                # The companies are usually in the next div or sibling
                # Merolagani uses a collapsible structure
                container = header.find_next_sibling('div')
                if container:
                    links = container.find_all('a', href=re.compile(r'CompanyDetail\.aspx\?symbol='))
                    if links:
                        standard_name = StockService.get_standard_sector(sector_name)
                        sector_obj, _ = Sector.objects.get_or_create(name=standard_name)
                        for link in links:
                            symbol = link.get_text(strip=True).upper()
                            if symbol:
                                # Check if sector is locked for this stock
                                stock_obj = Stock.objects.filter(symbol=symbol).first()
                                if stock_obj and stock_obj.sector_locked:
                                    # Just ensure it's active
                                    stock_obj.is_active = True
                                    stock_obj.save()
                                else:
                                    Stock.objects.update_or_create(
                                        symbol=symbol,
                                        defaults={'company_name': symbol, 'sector': sector_obj, 'is_active': True}
                                    )
                                sync_count += 1
            
            logger.info(f"Successfully synced metadata. Total processed entries: {sync_count}")
            return True
            
        except Exception as e:
            logger.error(f"Error during metadata sync: {str(e)}")
            return False

    @staticmethod
    def update_live_prices():
        """
        Scrape live prices from Merolagani and update Stock model and NEPSEPrice history.
        Runs every minute.
        """
        logger.info("Starting live price update...")
        timestamp = timezone.now()
        
        # We can reuse the driver-based logic from scrape_nepse or a more lightweight version if available
        # For simplicity and modularity, I'll implement a clean version here using Selenium as per existing patterns
        
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        scraper = NepseScraperService()
        driver = scraper.create_driver()
        
        try:
            driver.get('https://merolagani.com/StockQuote.aspx')
            time.sleep(2)
            scraper.dismiss_alerts(driver)
            
            # Wait for table
            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            
            # Scrape all pages if necessary, or just the first if it's "Show All"
            # For this service, let's assume we want all data
            
            total_updated = 0
            detected_new = 0
            
            # Reusing the existing extraction logic structure
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            table = soup.find('table') # Usually the first table on StockQuote
            if not table:
                return False

            rows = table.find_all('tr')[1:] # Skip header
            
            # Get sector "Uncategorized" as fallback
            uncategorized_sector, _ = Sector.objects.get_or_create(name="Uncategorized")

            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 3: continue
                
                # Merolagani Stock Quote Columns: Symbol, LTP, % Change, High, Low, Open, Qty, ...
                try:
                    symbol = cols[0].get_text(strip=True).upper()
                    ltp = scraper.parse_float(cols[1].get_text(strip=True))
                    change_pct = scraper.parse_float(cols[2].get_text(strip=True))
                    high = scraper.parse_float(cols[3].get_text(strip=True))
                    low = scraper.parse_float(cols[4].get_text(strip=True))
                    open_price = scraper.parse_float(cols[5].get_text(strip=True))
                    volume = scraper.parse_float(cols[6].get_text(strip=True))
                    turnover = scraper.parse_float(cols[7].get_text(strip=True))

                    if not symbol or ltp is None:
                        continue

                    # 1. Automatic Stock Detection
                    stock, created = Stock.objects.get_or_create(
                        symbol=symbol,
                        defaults={
                            'company_name': symbol, # Default to symbol if name unknown
                            'sector': uncategorized_sector,
                            'is_active': True
                        }
                    )
                    
                    if created:
                        logger.warning(f"New stock detected during price update: {symbol}")
                        detected_new += 1

                    # 2. Update Stock Model Current State
                    stock.last_price = ltp
                    stock.change = change_pct
                    stock.volume = volume or 0
                    stock.save()

                    # 3. Create NEPSEPrice record for history
                    NEPSEPrice.objects.create(
                        symbol=symbol,
                        timestamp=timestamp,
                        open=open_price,
                        high=high,
                        low=low,
                        close=ltp,
                        ltp=ltp,
                        change_pct=change_pct,
                        volume=volume or 0,
                        turnover=turnover or 0
                    )
                    
                    total_updated += 1
                except Exception as e:
                    logger.error(f"Error parsing row for {symbol if 'symbol' in locals() else 'unknown'}: {str(e)}")
                    continue

            logger.info(f"Live price update completed. Updated: {total_updated}, New Detected: {detected_new}")
            return True

        except Exception as e:
            logger.error(f"Error during live price update: {str(e)}")
            return False
        finally:
            driver.quit()
