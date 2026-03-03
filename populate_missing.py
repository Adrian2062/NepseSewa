import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

from myapp.models import Stock, Sector

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
    "Corporate Debentures": ["NBBD2085", "SBLD2091", "PBD85", "ADBLD83", "SBID83", "ICFCD88", "EBLD91", "NABILD2089", "EBLEB89", "MBLD2085", "SRBLD83", "SBID83", "SBID89", "PBD88", "GBBD85", "CIZBD86", "NICAD2091", "CIZBD90", "SAND2085", "RBBD2088"],
    "Trading": ["BBC", "STC"],
}

print("Starting population...")
# Step 1: Pre-fetch/create all Sector objects
sector_objects = {}
for sector_name in SECTOR_MAPPING.keys():
    obj, created = Sector.objects.get_or_create(name=sector_name)
    sector_objects[sector_name] = obj

# Step 2: Build symbol -> Sector object lookup
symbol_to_sector_obj = {}
for sector_name, symbols in SECTOR_MAPPING.items():
    for sym in symbols:
        symbol_to_sector_obj[sym.strip().upper()] = sector_objects[sector_name]

# Step 3: Update existing stocks or create missing ones
handled_symbols = set()
for stock in Stock.objects.all():
    handled_symbols.add(stock.symbol.strip().upper())

created_count = 0
for sym, sector_obj in symbol_to_sector_obj.items():
    if sym not in handled_symbols:
        Stock.objects.create(
            symbol=sym,
            sector=sector_obj,
            company_name=sym
        )
        created_count += 1

print(f"DONE. Created: {created_count}")
print(f"TOTAL STOCKS: {Stock.objects.count()}")
