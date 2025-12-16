from django.core.management.base import BaseCommand
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, UnexpectedAlertPresentException
from bs4 import BeautifulSoup
import time
from django.utils import timezone
import chromedriver_autoinstaller
from myapp.models import NEPSEPrice, MarketIndex, MarketSummary, NEPSEIndex
import re

chromedriver_autoinstaller.install()

class Command(BaseCommand):
    help = 'Scrape NEPSE market data from Merolagani'

    def add_arguments(self, parser):
        parser.add_argument('--interval', type=int, default=60, help='Scrape interval in seconds')
        parser.add_argument('--once', action='store_true', help='Run once and exit')

    def handle(self, *args, **options):
        interval = options['interval']
        run_once = options['once']
        iteration = 0

        self.stdout.write("🚀 Starting Merolagani NEPSE scraper...")
        
        try:
            while True:
                iteration += 1
                self.stdout.write(f"\n{'='*60}")
                self.stdout.write(f"--- Iteration {iteration} at {timezone.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
                self.stdout.write(f"{'='*60}")
                
                try:
                    self.scrape_all_data()
                    
                    if run_once:
                        self.stdout.write(self.style.SUCCESS("\n✓ Scraper completed successfully!"))
                        break
                    
                    self.stdout.write(f"\n⏳ Waiting {interval} seconds before next scrape...")
                    time.sleep(interval)
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"\n✗ Error: {str(e)}"))
                    if run_once:
                        break
                    self.stdout.write(f"⏳ Retrying in {interval} seconds...")
                    time.sleep(interval)
                    
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\n\n✓ Scraper stopped by user.'))

    def create_driver(self):
        """Create a new Chrome driver with optimal settings"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Add preferences to handle alerts
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
        }
        options.add_experimental_option("prefs", prefs)
        
        return webdriver.Chrome(options=options)

    def dismiss_alerts(self, driver, max_attempts=3):
        """Dismiss any alert dialogs that appear (with retry logic)"""
        dismissed_count = 0
        for attempt in range(max_attempts):
            try:
                alert = driver.switch_to.alert
                alert_text = alert.text
                # Dismiss notification alerts, accept others
                if 'notification' in alert_text.lower():
                    alert.dismiss()  # Click "No"
                else:
                    alert.accept()  # Click "OK"
                
                if dismissed_count == 0:  # Only log first dismissal
                    self.stdout.write(f"  ℹ️  Alert dismissed: {alert_text[:50]}")
                dismissed_count += 1
                time.sleep(0.5)  # Brief pause between dismissals
            except:
                break
        
        return dismissed_count > 0

    def scrape_all_data(self):
        """Scrape all market data from Merolagani"""
        driver = self.create_driver()
        
        try:
            # Scrape market summary (NEPSE Index and overview)
            self.scrape_market_summary(driver)
            
            # Scrape stock prices
            self.scrape_stock_prices(driver)
            
        finally:
            driver.quit()

    def scrape_market_summary(self, driver):
        """Scrape NEPSE Index and market overview from MarketSummary.aspx"""
        try:
            self.stdout.write("\n[📈 Loading Market Summary page...]")
            driver.get('https://merolagani.com/MarketSummary.aspx')
            
            # Handle any alerts
            time.sleep(2)
            self.dismiss_alerts(driver)
            
            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)
            
            # Dismiss any remaining alerts
            self.dismiss_alerts(driver)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            timestamp = timezone.now()
            
            # Extract NEPSE Index
            self.extract_nepse_index(soup, timestamp, driver)
            
            # Extract market indices
            self.extract_market_indices(soup, timestamp)
            
            # Extract market summary statistics
            self.extract_market_stats(soup, timestamp)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Error scraping market summary: {str(e)}"))

    def extract_nepse_index(self, soup, timestamp, driver):
        """Extract main NEPSE Index value and change"""
        try:
            self.stdout.write("\n[📊 Extracting NEPSE Index...]")
            
            nepse_value = None
            change_pct = None
            
            # Strategy 1: Look for the main index display (usually in a card/box)
            # Merolagani typically shows NEPSE prominently at the top
            
            # Try finding by ID or class patterns common in Merolagani
            index_elements = soup.find_all(['div', 'span', 'td'], 
                                          class_=re.compile(r'index|market|nepse', re.IGNORECASE))
            
            for elem in index_elements:
                text = elem.get_text(strip=True)
                # Look for 4-digit numbers in the NEPSE range
                numbers = re.findall(r'\b(\d{4}(?:\.\d{1,2})?)\b', text)
                for num in numbers:
                    val = float(num)
                    if 2000 < val < 4000:
                        nepse_value = val
                        # Look for percentage in nearby text
                        parent_text = elem.parent.get_text() if elem.parent else text
                        pct_match = re.search(r'([+-]?\d+\.\d+)%', parent_text)
                        if pct_match:
                            change_pct = float(pct_match.group(1))
                        break
                if nepse_value:
                    break
            
            # Strategy 2: Look in tables with "NEPSE" in the row
            if not nepse_value:
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        row_text = row.get_text(strip=True)
                        if 'NEPSE' in row_text.upper() and 'INDEX' in row_text.upper():
                            cells = row.find_all(['td', 'th'])
                            for cell in cells:
                                cell_text = cell.get_text(strip=True)
                                # Look for the index value
                                val = self.parse_float(cell_text)
                                if val and 2000 < val < 4000:
                                    nepse_value = val
                                # Look for percentage
                                if '%' in cell_text:
                                    pct = self.parse_float(cell_text.replace('%', ''))
                                    if pct and abs(pct) < 15:
                                        change_pct = pct
                            if nepse_value:
                                break
                    if nepse_value:
                        break
            
            # Strategy 3: Use Selenium to find visible elements with specific IDs
            if not nepse_value:
                try:
                    # Common ID patterns in Merolagani
                    possible_ids = [
                        'lblNepseIndex', 'nepse-index', 'marketIndex', 
                        'ctl00_ContentPlaceHolder1_lblIndex'
                    ]
                    
                    for element_id in possible_ids:
                        try:
                            element = driver.find_element(By.ID, element_id)
                            text = element.text
                            val = self.parse_float(text)
                            if val and 2000 < val < 4000:
                                nepse_value = val
                                break
                        except:
                            continue
                except Exception as e:
                    pass
            
            # Strategy 4: Look for specific text patterns in page
            if not nepse_value:
                page_text = soup.get_text()
                # Match patterns like "NEPSE: 2,647.82" or "Index Value: 2647.82"
                patterns = [
                    r'NEPSE[:\s]*(\d{1}[,\s]*\d{3}\.\d{2})',
                    r'Index[:\s]*(\d{1}[,\s]*\d{3}\.\d{2})',
                    r'(?:Current|Today)[:\s]*(\d{1}[,\s]*\d{3}\.\d{2})',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        nepse_value = self.parse_float(match.group(1))
                        if nepse_value and 2000 < nepse_value < 4000:
                            break
                        nepse_value = None
            
            # Save if valid
            if nepse_value and 2000 < nepse_value < 4000:
                # Save to NEPSEIndex model
                NEPSEIndex.objects.update_or_create(
                    timestamp=timestamp,
                    defaults={
                        'index_value': nepse_value,
                        'percentage_change': change_pct or 0,
                    }
                )
                
                # Also save to MarketIndex model
                MarketIndex.objects.update_or_create(
                    index_name='NEPSE Index',
                    timestamp=timestamp,
                    defaults={
                        'value': nepse_value,
                        'change_pct': change_pct or 0,
                    }
                )
                
                change_str = f" ({change_pct:+.2f}%)" if change_pct else ""
                self.stdout.write(self.style.SUCCESS(
                    f"  ✓ NEPSE Index: {nepse_value:,.2f}{change_str}"
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f"  ⚠️  Could not extract valid NEPSE Index (found: {nepse_value})"
                ))
                # Save page source for debugging
                with open('debug_market_summary.html', 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                self.stdout.write("  ℹ️  Page source saved to debug_market_summary.html for inspection")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ✗ Error extracting NEPSE Index: {str(e)}"))

    def extract_market_indices(self, soup, timestamp):
        """Extract sector indices from the page"""
        try:
            self.stdout.write("\n[📊 Extracting sector indices...]")
            
            indices_saved = 0
            seen_indices = set()
            
            # Find all tables
            tables = soup.find_all('table')
            
            for table in tables:
                # Get table headers to identify index tables
                thead = table.find('thead')
                headers = []
                if thead:
                    headers = [th.get_text(strip=True).lower() for th in thead.find_all('th')]
                
                # Skip non-index tables
                if headers and not any(kw in ' '.join(headers) for kw in ['index', 'symbol', 'value', 'change']):
                    continue
                
                tbody = table.find('tbody') or table
                rows = tbody.find_all('tr')
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 2:
                        continue
                    
                    # Extract index name and value
                    index_name = cells[0].get_text(strip=True)
                    
                    # Skip invalid names
                    if not index_name or len(index_name) < 3 or len(index_name) > 100:
                        continue
                    if index_name.lower() in ['s.n.', 'sn', 'symbol', 'index', 'name', 'sector', 's.n', '']:
                        continue
                    if index_name in seen_indices:
                        continue
                    
                    # Extract value and change
                    index_value = None
                    change_pct = 0
                    
                    for cell in cells[1:]:
                        cell_text = cell.get_text(strip=True)
                        
                        if '%' in cell_text:
                            pct = self.parse_float(cell_text.replace('%', ''))
                            if pct is not None and abs(pct) < 50:
                                change_pct = pct
                        else:
                            val = self.parse_float(cell_text)
                            if val and 50 < val < 50000:  # Reasonable range
                                index_value = val
                    
                    # Save if valid
                    if index_value and index_name and index_value > 0:
                        MarketIndex.objects.update_or_create(
                            index_name=index_name,
                            timestamp=timestamp,
                            defaults={
                                'value': index_value,
                                'change_pct': change_pct,
                            }
                        )
                        seen_indices.add(index_name)
                        indices_saved += 1
            
            if indices_saved > 0:
                self.stdout.write(self.style.SUCCESS(f"  ✓ Saved {indices_saved} sector indices"))
            else:
                self.stdout.write(self.style.WARNING("  ⚠️  No sector indices found"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ✗ Error extracting indices: {str(e)}"))

    def extract_market_stats(self, soup, timestamp):
        """Extract market statistics (turnover, shares, etc.)"""
        try:
            self.stdout.write("\n[📊 Extracting market statistics...]")
            
            page_text = soup.get_text()
            data = {}
            
            # More comprehensive patterns
            patterns = {
                'total_turnover': [
                    r'Total\s+Turnover[:\s]*(?:Rs\.?\s*)?(\d[\d,\.]*)',
                    r'Turnover[:\s]*(?:Rs\.?\s*)?(\d[\d,\.]*)',
                ],
                'total_traded_shares': [
                    r'Total\s+(?:Traded\s+)?Shares?[:\s]*(\d[\d,]*)',
                    r'Shares?\s+Traded[:\s]*(\d[\d,]*)',
                ],
                'total_transactions': [
                    r'Total\s+Transactions?[:\s]*(\d[\d,]*)',
                    r'No\.?\s+of\s+Transactions?[:\s]*(\d[\d,]*)',
                ],
                'total_scrips': [
                    r'(?:Total\s+)?Scrips\s+Traded[:\s]*(\d[\d,]*)',
                    r'No\.?\s+of\s+Scrips[:\s]*(\d[\d,]*)',
                ],
            }
            
            for field, pattern_list in patterns.items():
                for pattern in pattern_list:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        value = self.parse_float(match.group(1))
                        if value and value > 0:
                            data[field] = value
                            # Store expected scrips for comparison later
                            if field == 'total_scrips':
                                self.expected_scrips = int(value)
                            break
            
            # Save if we have data
            if data:
                MarketSummary.objects.update_or_create(
                    timestamp=timestamp,
                    defaults=data
                )
                
                self.stdout.write(self.style.SUCCESS("  ✓ Market statistics saved:"))
                for key, val in data.items():
                    self.stdout.write(f"    • {key.replace('_', ' ').title()}: {val:,.0f}")
            else:
                self.stdout.write(self.style.WARNING("  ⚠️  No market statistics extracted"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ✗ Error extracting market stats: {str(e)}"))

    def scrape_stock_prices(self, driver):
        """Scrape individual stock prices from StockQuote.aspx"""
        try:
            self.stdout.write("\n[📈 Loading Stock Quote page...]")
            driver.get('https://merolagani.com/StockQuote.aspx')
            
            # Handle alerts immediately
            time.sleep(2)
            self.dismiss_alerts(driver)
            
            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)
            
            # Dismiss any late alerts
            self.dismiss_alerts(driver)
            
            # Try to show all records at once if there's a "show all" option
            try:
                # Look for entries dropdown (e.g., "Show 10/25/50/100/All entries")
                show_all_options = driver.find_elements(By.XPATH, 
                    "//select[contains(@name, 'length') or contains(@name, 'entries')] | " +
                    "//option[contains(text(), 'All') or @value='-1']/.."
                )
                
                if show_all_options:
                    select_element = show_all_options[0]
                    # Try to select "All" or highest number
                    try:
                        from selenium.webdriver.support.select import Select
                        select = Select(select_element)
                        
                        # Try to find "All" option
                        all_found = False
                        for option in select.options:
                            if 'all' in option.text.lower() or option.get_attribute('value') == '-1':
                                select.select_by_visible_text(option.text)
                                self.stdout.write("  ✓ Selected 'Show All' option")
                                all_found = True
                                time.sleep(3)
                                break
                        
                        # If no "All", select largest number
                        if not all_found:
                            max_val = 0
                            max_option = None
                            for option in select.options:
                                try:
                                    val = int(option.get_attribute('value'))
                                    if val > max_val:
                                        max_val = val
                                        max_option = option
                                except:
                                    pass
                            if max_option:
                                select.select_by_visible_text(max_option.text)
                                self.stdout.write(f"  ✓ Selected 'Show {max_option.text}' option")
                                time.sleep(3)
                    except:
                        pass
            except:
                pass
            
            # Check if page loaded correctly by looking for table
            try:
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
                self.stdout.write("  ✓ Stock table loaded")
            except TimeoutException:
                self.stdout.write(self.style.WARNING("  ⚠️  Table not found quickly"))
            
            timestamp = timezone.now()
            total_saved = 0
            total_skipped = 0
            page_num = 1
            max_pages = 10  # Safety limit to prevent infinite loops
            
            # Handle pagination - scrape all pages
            while page_num <= max_pages:
                try:
                    # Dismiss any alerts before scraping
                    self.dismiss_alerts(driver)
                    
                    # Get current page data
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    saved, skipped = self.extract_stocks_from_page(soup, timestamp)
                    total_saved += saved
                    total_skipped += skipped
                    
                    self.stdout.write(f"  ➡️ Page {page_num}: Saved {saved} records, skipped {skipped}")
                    
                    # If we got 0 records, something went wrong
                    if saved == 0 and page_num > 1:
                        self.stdout.write(f"  ⚠️  Page {page_num} returned 0 records, stopping pagination")
                        break
                    
                    # Try to find and click next page button
                    try:
                        # Multiple strategies to find next button
                        next_button = None
                        
                        # Strategy 1: Look for pagination links
                        try:
                            next_button = driver.find_element(By.XPATH, 
                                "//a[contains(text(), 'Next') or contains(text(), '›') or contains(text(), '>')]"
                            )
                        except:
                            pass
                        
                        # Strategy 2: Look for page numbers and click next number
                        if not next_button:
                            try:
                                # Find current page and click next
                                current_page = driver.find_element(By.XPATH, 
                                    "//span[@class='current'] | //a[@class='active'] | //li[@class='active']"
                                )
                                next_num = page_num + 1
                                next_button = driver.find_element(By.XPATH, 
                                    f"//a[text()='{next_num}']"
                                )
                            except:
                                pass
                        
                        # Strategy 3: Look for DataTables pagination
                        if not next_button:
                            try:
                                next_button = driver.find_element(By.CSS_SELECTOR, 
                                    ".paginate_button.next:not(.disabled), #DataTables_Table_0_next a"
                                )
                            except:
                                pass
                        
                        # Click if found and enabled
                        if next_button:
                            try:
                                # Check if disabled
                                classes = next_button.get_attribute('class') or ''
                                if 'disabled' in classes.lower():
                                    break
                                
                                # Method 1: JavaScript click (bypasses overlays)
                                try:
                                    driver.execute_script("arguments[0].click();", next_button)
                                    self.stdout.write(f"  ✓ Navigated to page {page_num + 1} (JS click)")
                                except Exception as e1:
                                    # Method 2: Scroll and regular click
                                    try:
                                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                                        time.sleep(1)
                                        next_button.click()
                                        self.stdout.write(f"  ✓ Navigated to page {page_num + 1} (regular click)")
                                    except Exception as e2:
                                        # Method 3: ActionChains
                                        try:
                                            from selenium.webdriver.common.action_chains import ActionChains
                                            actions = ActionChains(driver)
                                            actions.move_to_element(next_button).click().perform()
                                            self.stdout.write(f"  ✓ Navigated to page {page_num + 1} (action chains)")
                                        except Exception as e3:
                                            self.stdout.write(f"  ⚠️  All click methods failed: {str(e3)[:40]}")
                                            break
                                
                                time.sleep(4)  # Wait for page load
                                
                                # Aggressively dismiss alerts multiple times
                                for _ in range(3):
                                    self.dismiss_alerts(driver)
                                    time.sleep(1)
                                
                                # Wait for new content to load
                                try:
                                    WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located((By.TAG_NAME, "table"))
                                    )
                                except:
                                    pass
                                
                                page_num += 1
                                
                            except Exception as e:
                                self.stdout.write(f"  ℹ️  Pagination ended: {str(e)[:50]}")
                                break
                        else:
                            # No next button found
                            self.stdout.write(f"  ℹ️  No next button found after page {page_num}")
                            break
                    except Exception as e:
                        # No more pages
                        break
                        
                except Exception as e:
                    self.stdout.write(f"  ⚠️  Page {page_num} error: {str(e)[:50]}")
                    break
            
            if total_saved > 0:
                self.stdout.write(self.style.SUCCESS(
                    f"\n  ✓ Total {total_saved} stock records saved across {page_num} page(s)"
                ))
                if total_skipped > 0:
                    self.stdout.write(f"  ℹ️  Skipped {total_skipped} invalid records")
                
                # Compare with expected scrips count
                if hasattr(self, 'expected_scrips'):
                    if total_saved < self.expected_scrips * 0.8:  # Less than 80% of expected
                        self.stdout.write(self.style.WARNING(
                            f"  ⚠️  Only got {total_saved}/{self.expected_scrips} expected stocks. "
                            f"Some data may be missing."
                        ))
            else:
                self.stdout.write(self.style.WARNING("  ⚠️  No valid stock records saved"))
                # Save debug info
                with open('debug_stock_quote.html', 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                self.stdout.write("  ℹ️  Page source saved to debug_stock_quote.html")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ✗ Error scraping stock prices: {str(e)}"))

    def extract_stocks_from_page(self, soup, timestamp):
        """Extract stock data from current page"""
        saved_count = 0
        skipped_count = 0
        
        try:
            # Find the stock table
            table = None
            tables = soup.find_all('table')
            
            for t in tables:
                # Check if table has stock-related headers
                headers_row = t.find('tr')
                if headers_row:
                    headers_text = headers_row.get_text().lower()
                    if any(kw in headers_text for kw in ['symbol', 'ltp', 'open', 'high', 'low', 'close']):
                        table = t
                        break
            
            if not table:
                return saved_count, skipped_count
            
            # Get headers
            headers = []
            thead = table.find('thead')
            if thead:
                headers = [th.get_text(strip=True).lower() for th in thead.find_all('th')]
            else:
                first_row = table.find('tr')
                if first_row:
                    headers = [th.get_text(strip=True).lower() for th in first_row.find_all(['th', 'td'])]
            
            # Find data rows
            tbody = table.find('tbody') or table
            rows = tbody.find_all('tr')
            
            # Skip header row if no thead
            start_idx = 1 if not thead and headers else 0
            data_rows = rows[start_idx:]
            
            for row in data_rows:
                try:
                    cells = row.find_all('td')
                    if len(cells) < 3:
                        skipped_count += 1
                        continue
                    
                    # Map headers to values
                    row_data = {}
                    for i, cell in enumerate(cells):
                        if i < len(headers):
                            row_data[headers[i]] = cell.get_text(strip=True)
                    
                    # Extract symbol
                    symbol = (row_data.get('symbol') or row_data.get('scrip') or 
                             row_data.get('stock') or cells[0].get_text(strip=True))
                    
                    # Validate symbol
                    if not symbol or len(symbol) > 20:
                        skipped_count += 1
                        continue
                    if symbol.lower() in ['symbol', 's.n.', 'sn', 's.n', '', 'scrip']:
                        skipped_count += 1
                        continue
                    
                    # Extract price data
                    ltp = self.parse_float(row_data.get('ltp') or row_data.get('close') or row_data.get('last'))
                    open_price = self.parse_float(row_data.get('open'))
                    high = self.parse_float(row_data.get('high'))
                    low = self.parse_float(row_data.get('low'))
                    close = ltp or self.parse_float(row_data.get('close'))
                    volume = self.parse_float(row_data.get('volume') or row_data.get('qty') or row_data.get('quantity'))
                    turnover = self.parse_float(row_data.get('turnover') or row_data.get('value'))
                    
                    # Extract change percentage
                    change_pct = 0
                    change_str = (row_data.get('change') or row_data.get('% change') or 
                                row_data.get('diff %') or row_data.get('% diff'))
                    if change_str:
                        change_pct = self.parse_float(change_str.replace('%', '')) or 0
                    
                    # Validate minimum requirements
                    if not ltp or ltp <= 0:
                        skipped_count += 1
                        continue
                    
                    # Save to database
                    NEPSEPrice.objects.update_or_create(
                        symbol=symbol,
                        timestamp=timestamp,
                        defaults={
                            'open': open_price or 0,
                            'high': high or 0,
                            'low': low or 0,
                            'close': close or 0,
                            'ltp': ltp,
                            'change_pct': change_pct,
                            'volume': volume or 0,
                            'turnover': turnover or 0,
                        }
                    )
                    saved_count += 1
                    
                except Exception as e:
                    skipped_count += 1
                    continue
            
            return saved_count, skipped_count
            
        except Exception as e:
            # Log error but return what we have
            return saved_count, skipped_count

    def parse_float(self, value):
        """Parse float from string, handling commas and special characters"""
        try:
            if not value or value in ['-', '--', 'N/A', '', 'NA', 'n/a']:
                return None
            
            # Remove commas, spaces, currency symbols
            cleaned = re.sub(r'[,\s₹Rs]', '', str(value))
            
            # Remove non-numeric except decimal and signs
            cleaned = re.sub(r'[^\d.\-+]', '', cleaned)
            
            if cleaned and cleaned not in ['.', '-', '+', '', '.-', '+.']:
                return float(cleaned)
        except (ValueError, TypeError):
            pass
        return None