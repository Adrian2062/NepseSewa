from stocks.models import NEPSEPrice   # change app name if needed
from django.db.models import F, ExpressionWrapper, FloatField
from django.db.models.functions import Lag
from django.db.models import Window

# Get latest trading date
latest_date = NEPSEPrice.objects.order_by('-timestamp').first().timestamp.date()

# Get previous date
previous_date = NEPSEPrice.objects.filter(
    timestamp__date__lt=latest_date
).order_by('-timestamp').first().timestamp.date()

# Get today's data
today_data = NEPSEPrice.objects.filter(timestamp__date=latest_date)

# Get previous day's data
previous_data = {
    obj.symbol: obj.close
    for obj in NEPSEPrice.objects.filter(timestamp__date=previous_date)
}

results = []

for stock in today_data:
    if stock.symbol in previous_data and previous_data[stock.symbol] != 0:
        prev_close = previous_data[stock.symbol]
        percent_change = ((stock.close - prev_close) / prev_close) * 100
        
        results.append({
            "symbol": stock.symbol,
            "close": stock.close,
            "percent": round(percent_change, 2)
        })

# Sort for gainers
top_gainers = sorted(results, key=lambda x: x['percent'], reverse=True)[:5]

# Sort for losers
top_losers = sorted(results, key=lambda x: x['percent'])[:5]

print("\nTop Gainers:")
for stock in top_gainers:
    print(stock)

print("\nTop Losers:")
for stock in top_losers:
    print(stock)