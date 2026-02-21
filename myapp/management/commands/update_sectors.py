from django.core.management.base import BaseCommand
from myapp.models import Stock, Sector


class Command(BaseCommand):
    help = 'Assign correct sectors to all stocks using the authoritative NEPSE sector map'

    SECTOR_MAPPING = {
        "Commercial Banks": ["ADBL", "GBIME", "CZBIL", "NIMBPO", "SBL", "SANIMA", "NMB", "NICA", "MBL", "NBL", "EBL", "PCBL", "SCB", "LSL", "SBI", "KBL", "PRVU"],
        "Development Banks": ["MLBL", "KSBBL", "MDB", "MNBBL", "SINDU", "GRDBL", "JBBL", "EDBL", "GBBL", "NABBC", "SADBL", "CORBL", "SHINE", "LBBL", "SAPDBL", "SABBL"],
        "Microfinance": ["LLBS", "SMFBS", "MERO", "SKBBL", "CYCL", "FOWAD", "NUBL", "SWBBL", "DDBL", "GLBSL", "GMFBS", "MSLB", "FMDBL", "JBLB", "ULBSL", "DLBS", "NMFBS", "NMLBBL", "MLBSL", "ALBSL", "ANLB"],
        "Finance": ["PROFL", "MPFL", "CFCL", "MFIL", "JFL", "SFCL", "GFCL", "PFL", "NFS", "SIFC", "RLFL", "ICFC", "BFC"],
        "Investment": ["NRN", "HATHY", "NIFRA", "CIT", "HIDCL", "CHDC"],
        "Hotels & Tourism": ["BANDIPUR", "KDL", "TRH", "SHL", "OHL", "CITY", "CGH"],
        "Manufacturing & Processing": ["GCIL", "SHIVM", "OMPL", "SONA", "SYPNL", "SAIL", "BNT", "SAGAR", "SARBTM", "UNL", "HDL", "BNL", "RSML"],
        "Others": ["NTC", "NRM", "NWCL", "MKCL", "TTL", "JHAPA", "HRL", "NRIC", "PURE"],
        "Hydropower": ["SANVI", "KKHC", "BHCL", "AKJCL", "TPC", "DHEL", "SSHL", "HDHPC", "NHPC", "SPL", "SMHL", "IHL", "NHDL", "AHL", "BUNGAL", "TSHL", "RFPL", "MHCL", "GVL", "BNHC", "LEC", "UMRH", "SHEL", "SHPC", "RIDI", "NGPL", "MBJC", "DORDI", "SGHC", "MHL", "USHEC", "BHPL", "SMH", "MKHC", "MAKAR", "MKHL", "DOLTI", "MCHL", "MEL", "RAWA", "KBSH", "MEHL", "ULHC", "MANDU", "BGWT", "TVCL", "VLUCL", "CKHL", "BEDC", "UPPER", "GHL", "UPCL", "MHNL", "PPCL", "SJCL", "MEN", "GLH", "RURU", "SAHAS", "SPC", "NYADI", "BHDC", "HHL", "UHEWA", "PPL", "SPHL", "SIKLES", "EHPL", "SMJC", "MMKJL", "PHCL"],
        "Life Insurance": ["HLI", "CLI", "ILI", "PMLI", "RNLI", "SNLI", "SRLI", "CREST", "GMLI", "ALICL", "NLICL", "LICN", "NLIC"],
        "Non-Life Insurance": ["SGIC", "NMIC", "SICL", "IGI", "RBCL", "HEI", "NIL", "PRIN", "NICL", "SPIL", "UAIL", "NLG"],
        "Mutual Fund": ["NMBHF2", "GBIMESY2", "SIGS2", "SFEF", "NICBF", "NSIF2", "LVF2", "C30MF", "GIBF1", "NIBLSTF", "CMF2", "SIGS3", "NICGF2", "HLICF", "NICFC", "NBF2", "H8020", "MMF1", "SEF", "KDBY"],
        "Corporate Debentures": ["NBBD2085", "SBLD2091", "PBD85", "ADBLD83", "SBID83", "ICFCD88", "EBLD91", "NABILD2089", "EBLEB89", "MBLD2085", "SRBLD83", "SBID89", "PBD88", "GBBD85", "CIZBD86", "NICAD2091", "CIZBD90", "SAND2085", "RBBD2088"],
        "Trading": ["BBC", "STC"],
    }

    def handle(self, *args, **options):
        self.stdout.write("Starting sector assignment...")

        # Step 1: Pre-fetch/create all Sector objects
        sector_objects = {}
        for sector_name in self.SECTOR_MAPPING.keys():
            obj, created = Sector.objects.get_or_create(name=sector_name)
            sector_objects[sector_name] = obj
            if created:
                self.stdout.write(f"  Created sector: {sector_name}")

        # Step 2: Build symbol -> Sector object lookup
        symbol_to_sector_obj = {}
        for sector_name, symbols in self.SECTOR_MAPPING.items():
            for sym in symbols:
                symbol_to_sector_obj[sym.strip().upper()] = sector_objects[sector_name]

        # Step 3: Update stocks
        updated = 0
        skipped_locked = 0
        not_in_map = 0

        for stock in Stock.objects.select_related('sector').all():
            clean_sym = stock.symbol.strip().upper()

            if clean_sym not in symbol_to_sector_obj:
                not_in_map += 1
                continue

            target_sector = symbol_to_sector_obj[clean_sym]

            # Respect sector_locked flag
            if getattr(stock, 'sector_locked', False):
                skipped_locked += 1
                continue

            if stock.sector_id != target_sector.id:
                old = stock.sector.name if stock.sector else 'None'
                stock.sector = target_sector  # Correctly assigns FK instance
                stock.save(update_fields=['sector'])
                self.stdout.write(f"  {clean_sym}: {old} -> {target_sector.name}")
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"\nDone! Updated: {updated} | Locked (skipped): {skipped_locked} | Not in map: {not_in_map}"
        ))
