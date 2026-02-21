import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

from myapp.models import Stock, Sector

SECTOR_MAP = {
    "Commercial Banks": ["ADBL", "GBIME", "CZBIL", "NIMBPO", "SBL", "SANIMA", "NMB", "NICA", "MBL", "NBL", "EBL", "PCBL", "SCB", "LSL", "SBI", "KBL", "PRVU"],
    "Development Banks": ["MLBL", "KSBBL", "MDB", "MNBBL", "SINDU", "GRDBL", "JBBL", "EDBL", "GBBL", "NABBC", "SADBL", "CORBL", "SHINE", "LBBL", "SAPDBL", "SABBL"],
    "Microfinance": ["LLBS", "SMFBS", "MERO", "SKBBL", "CYCL", "FOWAD", "NUBL", "SWBBL", "DDBL", "GLBSL", "GMFBS", "MSLB", "FMDBL", "JBLB", "ULBSL", "DLBS", "NMFBS", "NMLBBL", "MLBSL", "ALBSL"],
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

print("=== Assigning Sectors ===")
updated = 0
skipped_locked = 0
not_found = 0

for sector_name, symbols in SECTOR_MAP.items():
    # Ensure sector exists
    sector_obj, _ = Sector.objects.get_or_create(name=sector_name)
    
    for symbol in symbols:
        stock = Stock.objects.filter(symbol__iexact=symbol.strip()).first()
        if stock:
            if getattr(stock, 'sector_locked', False):
                print(f"  LOCKED (skip): {symbol}")
                skipped_locked += 1
            else:
                stock.sector = sector_obj
                stock.save(update_fields=['sector'])
                updated += 1
        else:
            not_found += 1

print(f"\nDone!")
print(f"  Updated:        {updated}")
print(f"  Skipped(locked):{skipped_locked}")
print(f"  Not in DB:      {not_found}")

print("\n=== Verification ===")
for sym in ['SABBL', 'RSML', 'ADBL', 'NTC']:
    s = Stock.objects.filter(symbol__iexact=sym).select_related('sector').first()
    sec = s.sector.name if s and s.sector else 'None'
    locked = getattr(s, 'sector_locked', False) if s else False
    print(f"  {sym}: sector='{sec}' locked={locked}")
