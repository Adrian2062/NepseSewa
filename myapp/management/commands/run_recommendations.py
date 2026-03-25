from django.core.management.base import BaseCommand
from myapp.models import Watchlist, NEPSEPrice, StockRecommendation, Stock
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Institutional Quantitative Recommendation Engine for NEPSE (90-Day Swing Strategy)'

    def add_arguments(self, parser):
        parser.add_argument('--watchlist-only', action='store_true', help='Only process symbols in user watchlists')
        parser.add_argument('--symbol', type=str, help='Process a single specific symbol')

    def handle(self, *args, **options):
        # Heavy imports inside handle to keep Django startup fast
        from myapp.ml_services import MLService, get_recommendation_data
        from django.db import connection
        
        self.stdout.write(self.style.SUCCESS('--- NEPSE QUANT ENGINE START ---'))
        
        # --- SELF-HEALING SCHEMA ---
        # Ensures all required institutional columns exist in the PostgreSQL table
        with connection.cursor() as cursor:
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'stock_recommendations'")
            cols = [row[0] for row in cursor.fetchall()]
            
            institutional_fields = {
                "rsi": "DOUBLE PRECISION",
                "expected_move": "DOUBLE PRECISION",
                "confidence": "DOUBLE PRECISION",
                "market_condition": "VARCHAR(100)",
                "trend": "VARCHAR(100)",
                "market_state": "VARCHAR(50)",
                "reason": "TEXT",
                "extra_data": "JSONB",
                "valid_until": "TIMESTAMP WITH TIME ZONE",
                "rmse": "DOUBLE PRECISION",
                "mae": "DOUBLE PRECISION"
            }
            
            for field, ftype in institutional_fields.items():
                if field not in cols:
                    self.stdout.write(f'   Self-Healing: Adding column {field}...')
                    cursor.execute(f'ALTER TABLE stock_recommendations ADD COLUMN "{field}" {ftype};')
                else:
                    # Ensure columns are nullable if they already exist
                    cursor.execute(f'ALTER TABLE stock_recommendations ALTER COLUMN "{field}" DROP NOT NULL;')
        
        watchlist_only = options.get('watchlist_only', False)
        target_symbol = options.get('symbol')

        # 1. SCOPE DETERMINATION
        if target_symbol:
            symbols = [target_symbol.strip().upper()]
            self.stdout.write(f'Mode: Single Symbol ({target_symbol})')
        elif watchlist_only:
            symbols = list(Watchlist.objects.values_list('symbol', flat=True).distinct())
            self.stdout.write('Mode: Watchlist Only')
        else:
            # Full Market Logic
            symbols = list(Stock.objects.values_list('symbol', flat=True).distinct())
            if not symbols:
                symbols = list(NEPSEPrice.objects.values_list('symbol', flat=True).distinct())
            
            self.stdout.write('Mode: Total Market Sweep')
            self.stdout.write('Clearing old system-wide recommendations...')
            StockRecommendation.objects.all().delete()
        
        if not symbols:
            self.stdout.write('No stocks found to process.')
            return

        total = len(symbols)
        self.stdout.write(f'Processing {total} symbols using Dynamic 90-day window...')

        for i, symbol in enumerate(symbols):
            try:
                self.stdout.write(f"\n[{i+1}/{total}] Analyzing {symbol}...")
                
                # 2. DYNAMIC DATA FETCHING (Accounts for Intraday Scraper Data)
                # Fetch last 6 months to guarantee we find 90 distinct days
                six_months_ago = timezone.now() - timedelta(days=180)
                history_qs = NEPSEPrice.objects.filter(
                    symbol=symbol,
                    timestamp__gte=six_months_ago
                ).order_by('-timestamp')
                
                raw_data = list(history_qs.values('timestamp', 'open', 'high', 'low', 'close', 'volume'))
                
                if not raw_data:
                    self.stdout.write(self.style.WARNING(f'   Skipping {symbol}: No data found in database.'))
                    continue

                # Group by Day: Since the scraper saves every minute, we only keep the last record of each day
                by_day = {}
                for record in raw_data:
                    day = record['timestamp'].date()
                    if day not in by_day: 
                        # Since it's ordered by -timestamp, the first one seen per day is the latest (closing)
                        by_day[day] = record  
                
                # Sort back to chronological order (oldest to newest) for ML processing
                history_data = [by_day[d] for d in sorted(by_day.keys())]
                
                # --- DYNAMIC DATA CHECK FOR TEACHER'S REQUIREMENT ---
                total_available_days = len(history_data)
                
                if total_available_days > 90:
                    # Cut it to exactly 90 days as per your teacher's instruction
                    history_data = history_data[-90:]
                    self.stdout.write(f"   [Data] Found {total_available_days} trading days. Sliced to exact 90 days.")
                else:
                    self.stdout.write(f"   [Data] Only {total_available_days} days available. Using all available data.")

                # Minimum requirement for indicators (RSI requires 14 days, SMA/EMA requires 20)
                if len(history_data) < 30:
                    self.stdout.write(self.style.WARNING(f'   Skipping {symbol}: Insufficient data ({len(history_data)} days). Minimum 30 required.'))
                    continue

                # 3. QUANTITATIVE PIPELINE (ML Training)
                ml = MLService(history_data)
                
                # Dynamically adjust ML window size based on available data
                dynamic_window = 20 if len(history_data) >= 60 else 10
                ml_result = ml.train_and_predict(window_size=dynamic_window)
                
                if not ml_result:
                    self.stdout.write(self.style.ERROR(f'   Model Pipeline Failed for {symbol}'))
                    continue

                # 4. SIGNAL SCORING
                rec_data = get_recommendation_data(ml_result)
                if not rec_data:
                    continue

                # 5. DIAGNOSTIC OUTPUT
                self.stdout.write(f"   [Debug] RSI: {rec_data['rsi']:.1f} | State: {rec_data['market_condition']}")
                self.stdout.write(f"   [Debug] Expected Move: {rec_data['expected_move']:.2f}% | Reason: {rec_data['reason']}")

                # 6. PERSIST TO DATABASE
                StockRecommendation.objects.update_or_create(
                    symbol=symbol,
                    defaults={
                        'current_price': ml_result['meta']['current_close'],
                        'predicted_next_close': ml_result['predictions'][0],
                        'predicted_return': rec_data['expected_move'],
                        'trend': rec_data['trend'],
                        'recommendation': rec_data['signal'],
                        'entry_price': rec_data['levels']['entry'],
                        'target_price': rec_data['levels']['target'],
                        'stop_loss': rec_data['levels']['stop_loss'],
                        'exit_price': rec_data['levels']['exit'],
                        'rsi': rec_data['rsi'],
                        'expected_move': rec_data['expected_move'],
                        'confidence': rec_data['confidence'],
                        'market_condition': rec_data['market_condition'],
                        'reason': rec_data['reason'],
                        'rmse': rec_data.get('rmse', 0),
                        'mae': rec_data.get('mae', 0),
                        'extra_data': {
                            'rsi': rec_data['rsi'],
                            'confidence': rec_data['confidence'],
                            'expected_move': rec_data['expected_move'],
                            'institutional_validation': True,
                            'days_analyzed': len(history_data)
                        }
                    }
                )
                
                sig_label = "BUY" if rec_data['signal'] == 1 else ("SELL" if rec_data['signal'] == -1 else "HOLD")
                color_func = self.style.SUCCESS if sig_label != "HOLD" else self.style.NOTICE
                
                self.stdout.write(color_func(f'   Result: {sig_label} | {rec_data["market_condition"]} | {rec_data["confidence"]}% Confidence'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   Critical Error {symbol}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('\n--- NEPSE QUANT ENGINE COMPLETE ---'))