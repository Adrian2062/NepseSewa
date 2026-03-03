from myapp.models import Stock
import re
import sys

try:
    deleted_count, _ = Stock.objects.filter(symbol__regex=r'^\d+$').delete()
    print(f"SUCCESS: Deleted {deleted_count} corrupted stock records.")
except Exception as e:
    print(f"ERROR: {str(e)}")
    sys.exit(1)
