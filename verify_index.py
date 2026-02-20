import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

from myapp.views import get_latest_nepse_index_with_change
from myapp.models import NEPSEIndex

def verify():
    with open('verify_results.txt', 'w') as f:
        f.write("Fetching latest NEPSE data...\n")
        try:
            data = get_latest_nepse_index_with_change()
            if data:
                f.write(f"Value: {data['value']}\n")
                f.write(f"Change %: {data['change_pct']}\n")
                f.write(f"Timestamp: {data['timestamp']}\n")
            else:
                f.write("No data found.\n")
        except Exception as e:
            f.write(f"Error: {str(e)}\n")

if __name__ == "__main__":
    verify()
