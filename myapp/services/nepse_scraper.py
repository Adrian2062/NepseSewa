import re
import time
from django.utils import timezone
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_autoinstaller

class NepseScraperService:
    @staticmethod
    def create_driver():
        """Create a new Chrome driver with optimal settings"""
        # Install driver only when actually needed
        chromedriver_autoinstaller.install()
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--ignore-certificate-errors') # For NEPSE site
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Add preferences to handle alerts
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
        }
        options.add_experimental_option("prefs", prefs)
        
        return webdriver.Chrome(options=options)

    @staticmethod
    def dismiss_alerts(driver, max_attempts=3):
        """Dismiss any alert dialogs that appear (with retry logic)"""
        dismissed_count = 0
        for attempt in range(max_attempts):
            try:
                alert = driver.switch_to.alert
                alert_text = alert.text
                if 'notification' in alert_text.lower():
                    alert.dismiss()
                else:
                    alert.accept()
                dismissed_count += 1
                time.sleep(0.5)
            except:
                break
        return dismissed_count > 0

    @staticmethod
    def parse_float(value):
        """Parse float from string, handling commas and special characters"""
        try:
            if not value or value in ['-', '--', 'N/A', '', 'NA', 'n/a']:
                return None
            cleaned = re.sub(r'[,\s₹Rs]', '', str(value))
            cleaned = re.sub(r'[^\d.\-+]', '', cleaned)
            if cleaned and cleaned not in ['.', '-', '+', '', '.-', '+.']:
                return float(cleaned)
        except (ValueError, TypeError):
            pass
        return None

    @classmethod
    def get_live_depth(cls, symbol):
        """
        Scrape live market depth from nepalstock.com for a given symbol.
        Returns detailed DOM-scraped structure of Buy/Sell orders.
        """
        driver = cls.create_driver()
        data = {'bids': [], 'asks': []}
        
        try:
            # Go to NEPSE Market Depth
            url = f"https://nepalstock.com/marketdepth"
            driver.get(url)
            
            # 1. Handle SSL Bypass (Agonizingly explicit)
            time.sleep(1)
            try:
                if "Privacy error" in driver.title or "Your connection is not private" in driver.page_source:
                   # Try clicking "Advanced"
                   try:
                       driver.find_element(By.ID, "details-button").click()
                       time.sleep(0.5)
                   except: 
                       pass
                   
                   # Try clicking "Proceed"
                   try:
                       driver.find_element(By.ID, "proceed-link").click()
                   except:
                       # Maybe it's a different link ID or text
                       try:
                           driver.find_element(By.partial_link_text("Proceed")).click()
                       except:
                           pass
                   time.sleep(3)
            except:
                pass

            wait = WebDriverWait(driver, 10)
            
            # 2. Search for Symbol
            try:
                search_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='search'], input[formcontrolname='search']")))
            except:
                # If explicit input not found, try generic input
                search_input = driver.find_element(By.TAG_NAME, "input")
                
            search_input.clear()
            search_input.send_keys(symbol)
            time.sleep(2) # Debounce
            
            # 3. Click Suggestion
            # The browser tool showed class='search_suggestion'.
            try:
                # Try specific suggestion first
                suggestion = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".search_suggestion .item, .search-result-item, .ng-option")))
                driver.execute_script("arguments[0].click();", suggestion)
            except:
                # Fallback: Send ENTER key
                from selenium.webdriver.common.keys import Keys
                search_input.send_keys(Keys.ENTER)
            
            # 4. Wait for Table
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.table-striped, table.table-bordered")))
            except:
                print("Table not found after search.")
                return data
            
            time.sleep(2) # Render delay
            
            # 5. Parse Data
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            tables = soup.find_all('table')
            target_table = None
            
            # Logic: Look for table with headers "Orders", "Qty", "Price" or similar logic
            for t in tables:
                header_text = t.get_text().lower()
                # Check for key columns in one table (Buy and Sell side)
                if "orders" in header_text and "qty" in header_text and "price" in header_text:
                    # Check if it has enough columns (at least 6-7)
                    rows = t.find_all('tr')
                    if len(rows) > 1:
                         # Verify first row headers
                         cols = rows[0].find_all(['th', 'td'])
                         if len(cols) >= 6:
                             target_table = t
                             break
            
            if target_table:
                rows = target_table.find_all('tr')
                # Skip header (row 0 is header)
                for row in rows[1:]:
                    cells = row.find_all('td')
                    
                    # Structure: [Ord, Qty, Price, Spacer, Price, Qty, Ord]
                    if len(cells) >= 7:
                        # BUY SIDE (Left)
                        try:
                            ord_b = cls.parse_float(cells[0].get_text()) or 1
                            qty_b = cls.parse_float(cells[1].get_text())
                            prc_b = cls.parse_float(cells[2].get_text())
                            
                            if qty_b and prc_b:
                                data['bids'].append({
                                    'price': prc_b,
                                    'qty': int(qty_b),
                                    'orders': int(ord_b)
                                })
                        except: pass
                        
                        # SELL SIDE (Right)
                        try:
                            # Index might vary if spacer is actually a td or just CSS. 
                            # Usually cols are: 0, 1, 2, [3?], 4, 5, 6
                            # Let's assume index 4, 5, 6 for Sell
                            
                            prc_s = cls.parse_float(cells[4].get_text())
                            qty_s = cls.parse_float(cells[5].get_text())
                            ord_s = cls.parse_float(cells[6].get_text()) or 1
                            
                            if qty_s and prc_s:
                                data['asks'].append({
                                    'price': prc_s,
                                    'qty': int(qty_s),
                                    'orders': int(ord_s)
                                })
                        except: pass

        except Exception as e:
            print(f"Scraping error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            try:
                driver.quit()
            except:
                pass
            
        return data
