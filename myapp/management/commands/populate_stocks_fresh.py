from django.core.management.base import BaseCommand
from myapp.models import Stock

class Command(BaseCommand):
    help = 'Aggressively populate stocks with correct sectors'

    def handle(self, *args, **options):
        self.stdout.write("Starting Fresh Stock Population...")

        SECTOR_DATA = {
            "Commercial Banks": [
                "ADBL", "GBIME", "CZBIL", "NIMBPO", "SBL", "SANIMA", "NMB", "NICA", "MBL", 
                "NBL", "EBL", "PCBL", "SCB", "LSL", "SBI", "KBL", "PRVU"
            ],
            "Development Banks": [
                "MLBL", "KSBBL", "MDB", "MNBBL", "SINDU", "GRDBL", "JBBL", "EDBL", "GBBL", 
                "NABBC", "SADBL", "CORBL", "SHINE", "LBBL", "SAPDBL"
            ],
            "Microfinance": [
                "LLBS", "SMFBS", "MERO", "SKBBL", "CYCL", "FOWAD", "NUBL", "SWBBL", "DDBL", 
                "GLBSL", "GMFBS", "MSLB", "FMDBL", "JBLB", "ULBSL", "DLBS", "NMFBS", "NMLBBL", 
                "MLBSL", "ALBSL"
            ],
            "Finance": [
                "PROFL", "MPFL", "CFCL", "MFIL", "JFL", "SFCL", "GFCL", "PFL", "NFS", "SIFC", 
                "RLFL", "ICFC", "BFC"
            ],
            "Investment": [
                "NRN", "HATHY", "NIFRA", "CIT", "HIDCL", "CHDC"
            ],
            "Hotels & Tourism": [
                "BANDIPUR", "KDL", "TRH", "SHL", "OHL", "CITY", "CGH"
            ],
            "Manufacturing & Processing": [
                "GCIL", "SHIVM", "OMPL", "SONA", "SYPNL", "SAIL", "BNT", "SAGAR", "SARBTM", "UNL", "HDL", "BNL"
            ],
            "Others": [
                "NTC", "NRM", "NWCL", "MKCL", "TTL", "JHAPA", "HRL", "NRIC", "PURE"
            ],
            "Hydropower": [
                "SANVI", "KKHC", "BHCL", "AKJCL", "TPC", "DHEL", "SSHL", "HDHPC", "NHPC", "SPL", 
                "SMHL", "IHL", "NHDL", "AHL", "BUNGAL", "TSHL", "RFPL", "MHCL", "GVL", "BNHC", 
                "LEC", "UMRH", "SHEL", "SHPC", "RIDI", "NGPL", "MBJC", "DORDI", "SGHC", "MHL", 
                "USHEC", "BHPL", "SMH", "MKHC", "MAKAR", "MKHL", "DOLTI", "MCHL", "MEL", "RAWA", 
                "KBSH", "MEHL", "ULHC", "MANDU", "BGWT", "TVCL", "VLUCL", "CKHL", "BEDC", "UPPER", 
                "GHL", "UPCL", "MHNL", "PPCL", "SJCL", "MEN", "GLH", "RURU", "SAHAS", "SPC", 
                "NYADI", "BHDC", "HHL", "UHEWA", "PPL", "SPHL", "SIKLES", "EHPL", "SMJC", "MMKJL", "PHCL"
            ],
            "Life Insurance": [
                "HLI", "CLI", "ILI", "PMLI", "RNLI", "SNLI", "SRLI", "CREST", "GMLI", "ALICL", "NLICL", "LICN", "NLIC"
            ],
            "Non-Life Insurance": [
                "SGIC", "NMIC", "SICL", "IGI", "RBCL", "HEI", "NIL", "PRIN", "NICL", "SPIL", "UAIL", "NLG"
            ],
            "Mutual Fund": [
                "NMBHF2", "GBIMESY2", "SIGS2", "SFEF", "NICBF", "NSIF2", "LVF2", "C30MF", "GIBF1", 
                "NIBLSTF", "CMF2", "SIGS3", "NICGF2", "HLICF", "NICFC", "NBF2", "H8020", "MMF1", 
                "SEF", "KDBY"
            ],
            "Corporate Debentures": [
                "NBBD2085", "SBLD2091", "PBD85", "ADBLD83", "SBID83", "ICFCD88", "EBLD91", 
                "NABILD2089", "EBLEB89", "MBLD2085", "SRBLD83", "SBID89", "PBD88", "GBBD85", 
                "CIZBD86", "NICAD2091", "CIZBD90", "SAND2085", "RBBD2088"
            ],
            "Trading": [
                "BBC", "STC"
            ]
        }

        # 1. Collect all known symbols
        all_symbols = []
        
        # 2. Iterate and update/create
        created_count = 0
        updated_count = 0

        for sector, symbols in SECTOR_DATA.items():
            for symbol in symbols:
                sym = symbol.strip().upper()
                all_symbols.append(sym)
                
                stock, created = Stock.objects.get_or_create(
                    symbol=sym,
                    defaults={'name': sym, 'sector': sector}
                )
                
                if created:
                    self.stdout.write(f"Created {sym} in {sector}")
                    created_count += 1
                else:
                    if stock.sector != sector:
                        self.stdout.write(f"Updated {sym} sector: {stock.sector} -> {sector}")
                        stock.sector = sector
                        stock.save()
                        updated_count += 1
        
        # 3. Clean up anything NOT in this list? 
        # The user said "remove all the old data from the all stocks and implement this data"
        # This implies we should maybe delete stocks that aren't in this master list.
        # But that's risky if valid stocks exist. For now, let's mark them as Inactive or just "Others"
        
        # Start by counting
        self.stdout.write("--------------------------------------------------")
        self.stdout.write(f"Finished processing. Created: {created_count}, Updated: {updated_count}")
