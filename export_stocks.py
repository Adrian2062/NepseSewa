import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

from myapp.models import Stock, NEPSEPrice

# 1. Get the latest price date across all stocks
latest_entry = NEPSEPrice.objects.order_by('-timestamp').first()
if not latest_entry:
    print("No price data found.")
    exit()

latest_date = latest_entry.timestamp

# 2. Get all prices for that specific date
all_latest_prices = NEPSEPrice.objects.filter(timestamp=latest_date).values('symbol', 'ltp')
price_map = {p['symbol'].strip().upper(): p['ltp'] for p in all_latest_prices}

# 3. Get all stocks
stocks = Stock.objects.all().order_by('symbol')

# 4. Generate report
output_path = os.path.join(os.getcwd(), 'exported_stock_data.md')
with open(output_path, 'w') as f:
    f.write("# Total Scraped Stocks Data\n\n")
    f.write(f"**Total Stocks in Registry:** {stocks.count()}\n")
    f.write(f"**Latest Data Date:** {latest_date.strftime('%Y-%m-%d %H:%M')}\n\n")
    f.write("| Symbol | Company Name | Sector | Last Traded Price (LTP) |\n")
    f.write("| :--- | :--- | :--- | :--- |\n")
    for s in stocks:
        clean_sym = s.symbol.strip().upper()
        ltp_val = price_map.get(clean_sym)
        ltp_str = f"Rs {ltp_val:.2f}" if ltp_val is not None else "Not Seeded"
        f.write(f"| {s.symbol} | {s.name} | {s.sector} | {ltp_str} |\n")

print(f"Exported successfully to {output_path}")
