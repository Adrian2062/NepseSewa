from django.core.management.base import BaseCommand
from myapp.models import Stock, NEPSEPrice, StockRecommendation
from myapp.ml_services import MLService, get_recommendation
import time

class Command(BaseCommand):
    help = 'Run LSTM predictions for all stocks'

    def handle(self, *args, **kwargs):
        self.stdout.write("Fetching stocks...")
        
        # Get all symbols
        symbols = list(Stock.objects.values_list('symbol', flat=True))
        if not symbols:
            symbols = list(NEPSEPrice.objects.values_list('symbol', flat=True).distinct())
            
        total = len(symbols)
        self.stdout.write(f"Found {total} stocks. Starting prediction loop...")
        
        count = 0
        errors = 0
        
        for symbol in symbols:
            try:
                # 1. Fetch Data
                history_qs = NEPSEPrice.objects.filter(symbol=symbol).order_by('timestamp')
                history_data = list(history_qs.values('timestamp', 'open', 'high', 'low', 'close', 'volume'))
                
                if len(history_data) < 40:
                    self.stdout.write(f"Skipping {symbol}: Insufficient data ({len(history_data)})")
                    continue
                    
                # Limit size
                if len(history_data) > 200:
                    history_data = history_data[-200:]
                    
                # 2. Train
                ml = MLService(history_data)
                predicted_price, rmse, mae, last_close = ml.train_and_predict(window_size=30)
                
                if predicted_price is None:
                     self.stdout.write(f"Skipping {symbol}: Model failed")
                     continue
                     
                rec_val = get_recommendation(last_close, predicted_price)
                
                # 3. Save
                StockRecommendation.objects.update_or_create(
                    symbol=symbol,
                    defaults={
                        'current_price': last_close,
                        'predicted_next_close': predicted_price,
                        'recommendation': rec_val,
                        'rmse': rmse,
                        'mae': mae
                    }
                )
                
                count += 1
                if count % 5 == 0:
                    self.stdout.write(f"Processed {count}/{total}...")
                    
            except Exception as e:
                errors += 1
                self.stdout.write(f"Error {symbol}: {e}")
                
        self.stdout.write(self.style.SUCCESS(f"Finished! Processed: {count}, Errors: {errors}"))
