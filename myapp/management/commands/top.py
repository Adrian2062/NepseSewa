from myapp.models import NEPSEPrice
from django.db.models import F, ExpressionWrapper, FloatField
from django.db.models.functions import Lag
from django.db.models import Window

from django.core.management.base import BaseCommand
from myapp.models import NEPSEPrice
from django.db.models import Max

class Command(BaseCommand):
    help = "Show Top Gainers and Top Losers"

    def handle(self, *args, **kwargs):

        # Get latest date
        latest = NEPSEPrice.objects.order_by('-timestamp').first()
        if not latest:
            print("No data found")
            return

        latest_date = latest.timestamp.date()

        # Get previous date
        previous = NEPSEPrice.objects.filter(
            timestamp__date__lt=latest_date
        ).order_by('-timestamp').first()

        if not previous:
            print("No previous data found")
            return

        previous_date = previous.timestamp.date()

        # Get only latest record per symbol for today
        today_latest = (
            NEPSEPrice.objects
            .filter(timestamp__date=latest_date)
            .values('symbol')
            .annotate(latest_time=Max('timestamp'))
        )

        results = []

        for item in today_latest:
            symbol = item['symbol']

            today_stock = NEPSEPrice.objects.get(
                symbol=symbol,
                timestamp=item['latest_time']
            )

            prev_stock = NEPSEPrice.objects.filter(
                symbol=symbol,
                timestamp__date=previous_date
            ).order_by('-timestamp').first()

            if prev_stock and prev_stock.close != 0:
                percent = ((today_stock.close - prev_stock.close) / prev_stock.close) * 100

                results.append({
                    "symbol": symbol,
                    "close": today_stock.close,
                    "percent": round(percent, 2)
                })

        top_gainers = sorted(results, key=lambda x: x['percent'], reverse=True)[:5]
        top_losers = sorted(results, key=lambda x: x['percent'])[:5]

        print("\nTop Gainers:")
        for stock in top_gainers:
            print(stock)

        print("\nTop Losers:")
        for stock in top_losers:
            print(stock)