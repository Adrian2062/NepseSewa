import logging
import re
import time
from django.utils import timezone
from myapp.models import Stock, Sector, NEPSEPrice
from .nepse_scraper import NepseScraperService
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class StockService:
    SECTOR_MAP_DATA = {
        "Commercial Banks": [
            "ADBL", "GBIME", "CZBIL", "NIMBPO", "SBL", "SANIMA", "NMB", "NICA", "MBL", 
            "NBL", "EBL", "PCBL", "SCB", "LSL", "SBI", "KBL", "PRVU", "NABIL", "NIMB", "HBL"
        ],
        "Development Banks": [
            "MLBL", "KSBBL", "MDB", "MNBBL", "SINDU", "GRDBL", "JBBL", "EDBL", "GBBL", 
            "NABBC", "SADBL", "CORBL", "SHINE", "LBBL", "SAPDBL", "SABBL", "SHINED"
        ],
        "Microfinance": [
            "LLBS", "SMFBS", "MERO", "SKBBL", "CYCL", "FOWAD", "NUBL", "SWBBL", "DDBL", 
            "GLBSL", "GMFBS", "MSLB", "FMDBL", "JBLB", "ULBSL", "DLBS", "NMFBS", "NMLBBL", 
            "MLBSL", "ALBSL", "ANLB", "ACLBSL", "AVYAN", "CBBL", "GILB", "HLBSL", "ILBS", 
            "JSLBB", "KMCDB", "MATRI", "MLBBL", "MLBS", "NADEP", "NESDO", "NICLBSL", 
            "NMBMF", "NSLB", "SMB", "USLB", "VLBS", "WNLB", "RSDC", 
            "SHLB", "SLBBL", "SLBSL", "SMATA", "SWMF", "UNLB", "GBLBS", "SWASTIK", "SMPDA"
        ],
        "Finance": [
            "PROFL", "MPFL", "CFCL", "MFIL", "JFL", "SFCL", "GFCL", "PFL", "NFS", 
            "SIFC", "RLFL", "ICFC", "BFC", "GMFIL", "GUFL"
        ],
        "Investment": [
            "NRN", "HATHY", "NIFRA", "CIT", "HIDCL", "CHDC", "HIDCLP", "NIFRAGED", 
        ],
        "Hotels & Tourism": [
            "BANDIPUR", "KDL", "TRH", "SHL", "OHL", "CITY", "CGH", "HFIN"
        ],
        "Manufacturing & Processing": [
            "GCIL", "SHIVM", "OMPL", "SONA", "SYPNL", "SAIL", "BNT", "SAGAR", 
            "SARBTM", "UNL", "HDL", "BNL", "RSML"
        ],
        "Hydropower": [
            "SANVI", "KKHC", "SMH", "BHCL", "AKJCL", "TPC", "DHEL", "SSHL", "HDHPC", "NHPC", 
            "SPL", "SMHL", "IHL", "NHDL", "AHL", "BUNGAL", "TSHL", "RFPL", "MHCL", "SMHL",
            "GVL", "BNHC", "LEC", "UMRH", "SHEL", "SHPC", "RIDI", "NGPL", "MBJC", 
            "DORDI", "SGHC", "MHL", "USHEC", "BHPL", "SMH", "MKHC", "MAKAR", "MKHL", 
            "DOLTI", "MCHL", "MEL", "RAWA", "KBSH", "MEHL", "ULHC", "MANDU", "BGWT", 
            "TVCL", "VLUCL", "CKHL", "BEDC", "UPPER", "GHL", "UPCL", "MHNL", "PPCL", 
            "SJCL", "MEN", "GLH", "RURU", "SAHAS", "SPC", "NYADI", "BHDC", "HHL", 
            "UHEWA", "PPL", "SPHL", "SIKLES", "EHPL", "SMJC", "MMKJL", "PHCL", 
            "AHPC", "AKPL", "API", "BARUN", "BHL", "BPCL", "CHCL", "CHL", "DHPL", 
            "ENL", "HPPL", "HURJA", "JOSHI", "KPCL", "MKJC", "MSHL", "PMHPL", 
            "RADHI", "RHGCL", "RHPL", "SPDL", "TAMOR", "UMHL", "UNHPL", "USHL", "MABEL"
        ],
        "Life Insurance": [
            "HLI", "CLI", "ILI", "PMLI", "RNLI", "SNLI", "SRLI", "CREST", "GMLI", 
            "ALICL", "NLICL", "LICN", "NLIC", "SJLIC"
        ],
        "Non-Life Insurance": [
            "SGIC", "NMIC", "SICL", "IGI", "RBCL", "HEI", "NIL", "PRIN", "NICL", 
            "SPIL", "UAIL", "NLG", "HEIP", "SALICO"
        ],
        "Mutual Fund": [
            "NMBHF2", "GBIMESY2", "SIGS2", "SFEF", "NICBF", "NSIF2", "LVF2", "C30MF", 
            "GIBF1", "NIBLSTF", "CMF2", "SIGS3", "NICGF2", "HLICF", "NICFC", "NBF2", 
            "H8020", "MMF1", "SEF", "KDBY", "CSY", "GSY", "KEF", "KSY", "LUK", 
            "MBLEF", "MNMF1", "NIBLPF", "NICGF", "RMF1", "SAEF", "SBCF", "SFMF", 
            "NBF3", "NIBLGF", "NIBSF2", "NICSF", "NMB50", "PRSF", "PSF", "RBBF40", 
            "RMF2", "RSY", "SAGF", "SLCF"
        ],
        "Corporate Debentures": [
            "NBBD2085", "SBLD2091", "PBD85", "ADBLD83", "SBID83", "ICFCD88", "EBLD91", 
            "NABILD2089", "EBLEB89", "MBLD2085", "SRBLD83", "SBID89", "PBD88", "GBBD85", 
            "CIZBD86", "NICAD2091", "CIZBD90", "SAND2085", "RBBD2088", "EBLD85", 
            "MFLD85", "GBILD84/85", "GBILD86/87", "NBLD87", "NIBD2082", "NIBD84", 
            "NICD88", "PBLD87", "SBID2090"
        ],
        "Trading": [
            "BBC", "STC", "HIMSTAR"
        ],
        "Others": [
            "NTC", "NRM", "NWCL", "MKCL", "TTL", "JHAPA", "HRL", "NRIC", "PURE"
        ],
    }

    @staticmethod
    def get_correct_sector_instance(symbol):
        """Returns the actual database Sector object based on the exhaustive symbol map."""
        clean_sym = symbol.strip().upper()
        target_name = "Others" # Default fallback for newly listed scrips

        for sector_name, symbols in StockService.SECTOR_MAP_DATA.items():
            if clean_sym in symbols:
                target_name = sector_name
                break
        
        sector = Sector.objects.filter(name=target_name).first()
        if not sector:
            sector, _ = Sector.objects.get_or_create(name="Others")
        return sector

    @staticmethod
    def update_live_prices():
        """Scrape all 329 stocks and FORCE sync sectors from exhaustive mapping."""
        print("\n" + "="*60)
        print("🚀 STARTING GLOBAL SECTOR SYNC & LIVE PRICE SCRAPE")
        print("="*60)
        timestamp = timezone.now()
        
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        scraper = NepseScraperService()
        driver = scraper.create_driver()
        
        try:
            print("🌐 Connecting to Merolagani...")
            driver.get('https://merolagani.com/StockQuote.aspx')
            
            # Kill Alerts via JS Injection
            driver.execute_script("window.alert = function() {}; window.confirm = function() {};")

            wait = WebDriverWait(driver, 20)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            time.sleep(3)

            # Force 100 entries via JS
            driver.execute_script("""
                var sel = document.querySelector('select[name*="length"], .dataTables_length select');
                if(sel) { sel.value = '100'; sel.dispatchEvent(new Event('change', {bubbles: true})); }
            """)
            time.sleep(5)

            total_saved = 0
            page_num = 1
            max_pages = 5 

            while page_num <= max_pages:
                print(f"📄 Processing Page {page_num}...")
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                target_table = None
                for table in soup.find_all('table'):
                    if 'symbol' in table.get_text().lower() or 'ltp' in table.get_text().lower():
                        target_table = table
                        break
                
                if not target_table: break

                # Robust Column Mapping
                headers = [th.get_text(strip=True).upper() for th in target_table.find_all(['th', 'td'])[:15]]
                col_map = {'symbol': 0, 'ltp': 2, 'change': 3, 'high': 4, 'low': 5, 'open': 6, 'vol': 7, 'turnover': 8}
                for i, h in enumerate(headers):
                    if 'SYMBOL' in h or 'SCRIP' in h: col_map['symbol'] = i
                    elif 'LTP' in h: col_map['ltp'] = i
                    elif '%' in h or 'CHANGE' in h: col_map['change'] = i
                    elif 'HIGH' in h: col_map['high'] = i
                    elif 'LOW' in h: col_map['low'] = i
                    elif 'OPEN' in h: col_map['open'] = i
                    elif 'VOL' in h or 'QTY' in h or 'SHARES' in h: col_map['vol'] = i
                    elif 'TURN' in h or 'AMT' in h or 'AMOUNT' in h: col_map['turnover'] = i

                rows = target_table.find_all('tr')
                start_row = 1 if target_table.find('thead') else 0
                
                if len(rows) <= start_row: break
                first_sym_current = rows[start_row].find_all('td')[col_map['symbol']].get_text(strip=True)

                for row in rows[start_row:]:
                    cols = row.find_all('td')
                    if len(cols) <= col_map['symbol']: continue
                    
                    try:
                        symbol = cols[col_map['symbol']].get_text(strip=True).upper()
                        if not symbol or re.match(r'^\d+$', symbol) or symbol == "SYMBOL":
                            continue

                        ltp = scraper.parse_float(cols[col_map['ltp']].get_text(strip=True))
                        if ltp is None: continue

                        # --- FORCED SECTOR SYNC ---
                        correct_sector = StockService.get_correct_sector_instance(symbol)

                        # Update metadata and overwrite sector
                        stock, _ = Stock.objects.update_or_create(
                            symbol=symbol, 
                            defaults={
                                'company_name': symbol, 
                                'sector': correct_sector, 
                                'last_price': ltp,
                                'change': scraper.parse_float(cols[col_map['change']].get_text(strip=True)) if len(cols) > col_map['change'] else 0,
                            }
                        )
                        
                        # Save history
                        NEPSEPrice.objects.create(
                            symbol=symbol, timestamp=timestamp, ltp=ltp, change_pct=stock.change,
                            high=scraper.parse_float(cols[col_map['high']].get_text(strip=True)) if len(cols) > col_map['high'] else 0,
                            low=scraper.parse_float(cols[col_map['low']].get_text(strip=True)) if len(cols) > col_map['low'] else 0,
                            open=scraper.parse_float(cols[col_map['open']].get_text(strip=True)) if len(cols) > col_map['open'] else 0,
                            volume=scraper.parse_float(cols[col_map['vol']].get_text(strip=True)) if len(cols) > col_map['vol'] else 0,
                            turnover=scraper.parse_float(cols[col_map['turnover']].get_text(strip=True)) if len(cols) > col_map['turnover'] else 0
                        )
                        total_saved += 1
                    except: continue

                print(f"✅ Finished Page {page_num}. Total so far: {total_saved}")

                # JS PAGINATION
                js_clicked = driver.execute_script("""
                    var links = document.querySelectorAll('a');
                    for (var i = 0; i < links.length; i++) {
                        if (links[i].textContent.trim() === 'Next' || links[i].textContent.trim() === '›') {
                            if(!links[i].parentElement.classList.contains('disabled')) {
                                links[i].click(); return true;
                            }
                        }
                    }
                    return false;
                """)
                if not js_clicked: break
                
                refreshed = False
                for _ in range(10):
                    time.sleep(1.5)
                    check_soup = BeautifulSoup(driver.page_source, 'html.parser')
                    try:
                        new_sym = check_soup.find('table').find_all('tr')[start_row].find_all('td')[col_map['symbol']].get_text(strip=True)
                        if new_sym != first_sym_current:
                            refreshed = True
                            break
                    except: pass
                if not refreshed: break
                page_num += 1

            print(f"\n✨ FINISHED! Saved {total_saved} stocks with COMPREHENSIVE sector mapping.")
            return True
        finally:
            driver.quit()