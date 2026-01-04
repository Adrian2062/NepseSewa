from django.core.management.base import BaseCommand
from myapp.models import Stock, NEPSEPrice

class Command(BaseCommand):
    help = 'Populate Stock table from existing NEPSEPrice data'

    def handle(self, *args, **options):
        self.stdout.write("Populating Stock table from NEPSEPrice...")
        
        # Get unique symbols
        symbols = NEPSEPrice.objects.values_list('symbol', flat=True).distinct()
        
        self.stdout.write(f"Found {len(symbols)} unique symbols")
        
        # Comprehensive sector map
        sector_map = {
            'ADBL': 'Commercial Banks', 'BOKL': 'Commercial Banks', 'CBL': 'Commercial Banks',
            'CCBL': 'Commercial Banks', 'CZBIL': 'Commercial Banks', 'EBL': 'Commercial Banks',
            'GBIME': 'Commercial Banks', 'HBL': 'Commercial Banks', 'KBL': 'Commercial Banks',
            'LBL': 'Commercial Banks', 'MBL': 'Commercial Banks', 'NABIL': 'Commercial Banks',
            'NBL': 'Commercial Banks', 'NICA': 'Commercial Banks', 'NMB': 'Commercial Banks',
            'NBB': 'Commercial Banks', 'PCBL': 'Commercial Banks', 'PRVU': 'Commercial Banks',
            'SANIMA': 'Commercial Banks', 'SBI': 'Commercial Banks', 'SBL': 'Commercial Banks',
            'SCB': 'Commercial Banks', 'SRBL': 'Commercial Banks',
            
            'AKPL': 'Hydropower', 'API': 'Hydropower', 'AHPC': 'Hydropower', 'UPPER': 'Hydropower',
            'CHCL': 'Hydropower', 'NHPC': 'Hydropower', 'SHPC': 'Hydropower', 'RHPC': 'Hydropower',
            
            'ACLBSL': 'Microfinance', 'AKBSL': 'Microfinance', 'CBBL': 'Microfinance',
            'DDBL': 'Microfinance', 'GILB': 'Microfinance', 'GLBSL': 'Microfinance',
            
            'NLIC': 'Life Insurance', 'NLICL': 'Life Insurance', 'ALICL': 'Life Insurance',
            
            'NICL': 'Non Life Insurance', 'NIL': 'Non Life Insurance', 'SICL': 'Non Life Insurance',
        }
        
        created = 0
        for symbol in symbols:
            clean_sym = symbol.strip().upper()
            
            # Determine sector
            sector = sector_map.get(clean_sym)
            if not sector:
                if 'LBSL' in clean_sym or 'BSL' in clean_sym:
                    sector = 'Microfinance'
                elif clean_sym.endswith('PC') or clean_sym.endswith('PL'):
                    sector = 'Hydropower'
                else:
                    sector = 'Others'
            
            Stock.objects.get_or_create(
                symbol=clean_sym,
                defaults={'name': clean_sym, 'sector': sector}
            )
            created += 1
            
        self.stdout.write(self.style.SUCCESS(f"Created/updated {created} stocks"))
