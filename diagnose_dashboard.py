
import os
import django
from django.utils import timezone
from datetime import datetime, time, timedelta
import pytz

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

from myapp.models import MarketSession, TradeExecution, Order, Trade
from myapp.services.market_session import get_nepal_time, NEPAL_TZ

def diagnose():
    now = timezone.now()
    nepal_now = get_nepal_time()
    today = nepal_now.date()
    today_start_nepal = nepal_now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_start_utc = today_start_nepal.astimezone(pytz.UTC)
    
    print(f"Current UTC: {now}")
    print(f"Current Nepal: {nepal_now}")
    print(f"Today Start Nepal: {today_start_nepal}")
    print(f"Today Start UTC: {today_start_utc}")
    
    session = MarketSession.objects.filter(session_date=today).first()
    print(f"Session Today: {session.status if session else 'NONE'} (Active: {session.is_active if session else 'N/A'})")
    
    # Check TradeExecution (New)
    trades_exec_today = TradeExecution.objects.filter(executed_at__gte=today_start_nepal)
    print(f"TradeExecutions today (>= Nepal Start): {trades_exec_today.count()}")
    
    trades_exec_today_utc = TradeExecution.objects.filter(executed_at__gte=today_start_utc)
    print(f"TradeExecutions today (>= UTC converted Start): {trades_exec_today_utc.count()}")
    
    # Check Legacy Trade
    trades_legacy_today = Trade.objects.filter(created_at__gte=today_start_nepal)
    print(f"Legacy Trades today: {trades_legacy_today.count()}")
    
    all_trades_exec = TradeExecution.objects.all().order_by('-executed_at')[:5]
    print("\nRecent 5 TradeExecutions:")
    for t in all_trades_exec:
        print(f"  - {t.symbol} {t.executed_qty} @ {t.executed_price} at {t.executed_at} (UTC)")
        
    all_trades_legacy = Trade.objects.all().order_by('-created_at')[:5]
    print("\nRecent 5 Legacy Trades:")
    for t in all_trades_legacy:
        print(f"  - {t.symbol} {t.qty} @ {t.price} at {t.created_at} (UTC)")

if __name__ == "__main__":
    diagnose()
