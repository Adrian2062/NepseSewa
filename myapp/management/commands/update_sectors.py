from django.core.management.base import BaseCommand
from myapp.models import Stock
import requests
from bs4 import BeautifulSoup
import time
import random

class Command(BaseCommand):
    help = 'Update stock sectors by scraping company profile pages'

    def handle(self, *args, **options):
        self.stdout.write("Starting Sector Update Scraper...")
        
        stocks = Stock.objects.all().order_by('symbol')
        total = stocks.count()
        processed = 0
        updated = 0
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        for stock in stocks:
            try:
                # 1. Skip if already set (Optional, but let's force check "Others" or all)
                # If we want to fix specific "Others", we could filter query.
                # User wants "do for all", so we check all.
                
                url = f"https://merolagani.com/CompanyDetail.aspx?symbol={stock.symbol}"
                self.stdout.write(f"[{processed+1}/{total}] Checking {stock.symbol}...", ending='')
                
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Finding Sector in the table
                    # Usually in a table with ID "accordion" or just generic table
                    # Look for "Sector" text in th/td
                    
                    sector_found = None
                    
                    # Strategy: Find "Sector" label and get next sibling or cell
                    labels = soup.find_all(['th', 'td', 'strong', 'span'], text=lambda t: t and 'Sector' in t)
                    
                    for label in labels:
                        # Try to find value in next valid element
                        # Usually row: <th>Sector</th> <td>Commercial Banks</td>
                        parent = label.parent
                        if parent.name == 'tr':
                            cells = parent.find_all('td')
                            if cells:
                                sector_found = cells[0].get_text(strip=True) or cells[-1].get_text(strip=True)
                                if 'Sector' in sector_found: sector_found = None # Label itself
                                
                        if not sector_found:
                            # Try next sibling
                            nxt = label.find_next_sibling()
                            if nxt: 
                                sector_found = nxt.get_text(strip=True)
                                
                        if sector_found: break
                    
                    if sector_found and len(sector_found) > 2:
                        # Clean it
                        clean_sector = sector_found.strip()
                        if clean_sector != stock.sector:
                            stock.sector = clean_sector
                            stock.save()
                            self.stdout.write(self.style.SUCCESS(f" Updated to '{clean_sector}'"))
                            updated += 1
                        else:
                            self.stdout.write(f" OK ({clean_sector})")
                    else:
                        self.stdout.write(self.style.WARNING(" Sector not found"))
                else:
                    self.stdout.write(self.style.ERROR(f" Failed (Status {response.status_code})"))
                    
                processed += 1
                time.sleep(1.5) # Rate limit
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f" Error: {str(e)}"))
                
        self.stdout.write(self.style.SUCCESS(f"\nDone! Updated {updated} stocks."))
