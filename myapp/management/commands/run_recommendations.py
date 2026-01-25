from django.core.management.base import BaseCommand
from myapp.models import Watchlist, NEPSEPrice, StockRecommendation, Stock
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Institutional Quantitative Recommendation Engine for NEPSE'

    def add_arguments(self, parser):
        parser.add_argument('--watchlist-only', action='store_true', help='Only process symbols in user watchlists')
        parser.add_argument('--symbol', type=str, help='Process a single specific symbol')

    def handle(self, *args, **options):
        # Heavy imports inside handle to keep Django startup fast
        from myapp.ml_services import MLService, get_recommendation_data
        from django.db import connection
        
        self.stdout.write(self.style.SUCCESS('--- NEPSE QUANT ENGINE START ---'))
        
        # Self-healing schema: ensure all institutional columns exist in PostgreSQL
        with connection.cursor() as cursor:
            # Check existing columns
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'stock_recommendations'")
            cols = [row[0] for row in cursor.fetchall()]
            
            # Map required fields to types
            institutional_fields = {
                "rsi": "DOUBLE PRECISION",
                "expected_move": "DOUBLE PRECISION",
                "confidence": "DOUBLE PRECISION",
                "market_state": "VARCHAR(100)",
                "reason": "TEXT"
            }
            
            for field, ftype in institutional_fields.items():
                if field not in cols:
                    self.stdout.write(f'   Self-Healing: Adding institutional column {field}...')
                    cursor.execute(f'ALTER TABLE stock_recommendations ADD COLUMN "{field}" {ftype};')
        
        watchlist_only = options.get('watchlist_only', False)
        target_symbol = options.get('symbol')

        # 1. Scope Determination
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
        self.stdout.write(f'Processing {total} symbols using 60-day rolling window...')

        for i, symbol in enumerate(symbols):
            try:
                self.stdout.write(f"[{i+1}/{total}] Analyzing {symbol}...")
                
                # 2. Fetch History with Intraday Filter
                # We fetch a large block (3 months has ~65 trading days, but could have 1000s of intraday records)
                history_qs = NEPSEPrice.objects.filter(symbol=symbol).order_by('-timestamp')[:3000]
                raw_data = list(history_qs.values('timestamp', 'open', 'high', 'low', 'close', 'volume'))
                
                if not raw_data:
                    continue

                # Filter for distinct days (Latest record of each day)
                by_day = {}
                for record in raw_data:
                    day = record['timestamp'].date()
                    if day not in by_day: # Since it's ordered by -timestamp, the first one seen per day is the latest
                        by_day[day] = record
                
                # Sort back to chronological order
                history_data = [by_day[d] for d in sorted(by_day.keys())]
                
                # Cut to most recent 90 distinct days for analysis
                history_data = history_data[-90:]

                if len(history_data) < 60:
                    self.stdout.write(self.style.WARNING(f'   Skipping {symbol}: Insufficient historical days ({len(history_data)} days). Please run backfill_history command.'))
                    continue

                # 3. Quantitative Pipeline
                ml = MLService(history_data)
                ml_result = ml.train_and_predict(window_size=20)
                
                if not ml_result:
                    self.stdout.write(self.style.ERROR(f'   Model Pipeline Failed for {symbol}'))
                    continue

                # 4. Signal Scoring
                rec_data = get_recommendation_data(ml_result)
                if not rec_data:
                    continue

                # 5. Diagnostic Output
                m = ml_result['meta']
                self.stdout.write(f"   [Debug] RSI: {rec_data['rsi']:.1f} | State: {rec_data['market_condition']}")
                self.stdout.write(f"   [Debug] ExpMove: {rec_data['expected_move']:.2f}% | Reason: {rec_data['reason']}")

                # 6. Persist to Database
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
                        'market_state': rec_data['market_condition'],
                        'reason': rec_data['reason'],
                        'rmse': rec_data['rmse'],
                        'mae': rec_data['mae']
                    }
                )
                
                sig_label = "BUY" if rec_data['signal'] == 1 else ("SELL" if rec_data['signal'] == -1 else "HOLD")
                color_func = self.style.SUCCESS if sig_label != "HOLD" else self.style.NOTICE
                
                self.stdout.write(color_func(f'   Result: {sig_label} | {rec_data["market_condition"]} | {rec_data["confidence"]}%'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   Critical Error {symbol}: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('\n--- NEPSE QUANT ENGINE COMPLETE ---'))
