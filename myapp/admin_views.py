"""
Custom Admin Views for Trading Engine
Handles market control and scraper management
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.core.management import call_command
import threading

from .models import Order, TradeExecution, MarketSession, MarketSummary, Trade, Stock, NEPSEPrice, Watchlist, StockRecommendation
from .services.market_session import get_current_session, pause_market, resume_market, get_nepal_time
from .ml_services import MLService, get_recommendation_data
from django.contrib.admin.sites import site

def dashboard_callback(request, context):
    """
    Unfold dashboard callback (REQUIRED)
    """
    context.update({
        "title": "NepseSewa Admin Dashboard",
        "user": request.user,
        "nepal_time": get_nepal_time(),
        "app_list": site.get_app_list(request),
    })
    return context


@staff_member_required
def trading_dashboard(request):
    """
    Admin dashboard for trading engine monitoring
    """
    # Get current session info
    session = get_current_session()
    nepal_time = get_nepal_time()
    today = nepal_time.date()
    
    # Get recent orders (filtered for today)
    recent_orders = Order.objects.filter(
        created_at__date=today
    ).select_related('user').order_by('-created_at')[:20]
    
    # Get recent trades (filtered for today)
    recent_trades = TradeExecution.objects.filter(
        executed_at__date=today
    ).select_related('buy_order', 'sell_order').order_by('-executed_at')[:20]
    
    # Get recent recommendations
    recent_recommendations = StockRecommendation.objects.order_by('-last_updated')[:10]
    
    # Debug: count records
    total_trades_count = TradeExecution.objects.count()
    total_legacy_trades_count = Trade.objects.count()
    total_recommendations = StockRecommendation.objects.count()
    
    context = {
        'session': session,
        'nepal_time': nepal_time,
        'recent_orders': recent_orders,
        'recent_trades': recent_trades,
        'recent_recommendations': recent_recommendations,
        'total_trades_count': total_trades_count,
        'total_legacy_trades_count': total_legacy_trades_count,
        'total_recommendations': total_recommendations,
        'title': 'Trading Engine Dashboard'
    }
    
    return render(request, 'admin/trading_dashboard.html', context)


def run_recommendations_logic(symbols=None):
    """
    Re-usable logic for running recommendations
    """
    try:
        if symbols is None:
            # Fallback to all active stocks
            symbols = Stock.objects.values_list('symbol', flat=True).distinct()
            if not symbols:
                symbols = NEPSEPrice.objects.values_list('symbol', flat=True).distinct()

        for symbol in symbols:
            try:
                history_qs = NEPSEPrice.objects.filter(symbol=symbol).order_by('timestamp')
                history_data = list(history_qs.values('timestamp', 'open', 'high', 'low', 'close', 'volume'))
                
                if len(history_data) > 200:
                    history_data = history_data[-200:]
                if len(history_data) < 40:
                    continue
                    
                ml = MLService(history_data)
                ml_result = ml.train_and_predict(window_size=20)
                if ml_result is None:
                    continue

                rec_data = get_recommendation_data(ml_result)
                if rec_data is None:
                    continue

                # Senior Practice: Model instance save handles truncation and validation automatically
                # We also ensure native Python types here to prevent NumPy ambiguity in Django validation
                rec_instance, _ = StockRecommendation.objects.update_or_create(
                    symbol=symbol,
                    defaults={
                        'current_price': float(ml_result['meta']['current_close']),
                        'predicted_next_close': float(ml_result['predictions'][0]),
                        'predicted_return': float(rec_data['expected_move']),
                        'trend': str(rec_data['trend']),
                        'recommendation': int(rec_data['signal']),
                        'entry_price': float(rec_data['levels']['entry']) if rec_data['levels']['entry'] is not None else None,
                        'target_price': float(rec_data['levels']['target']) if rec_data['levels']['target'] is not None else None,
                        'stop_loss': float(rec_data['levels']['stop_loss']) if rec_data['levels']['stop_loss'] is not None else None,
                        'exit_price': float(rec_data['levels']['exit']) if rec_data['levels']['exit'] is not None else None,
                        'rmse': float(rec_data['rmse']),
                        'mae': float(rec_data['mae']),
                        'extra_data': {
                            'rsi': float(rec_data['rsi']),
                            'confidence': float(rec_data['confidence']),
                            'expected_move': float(rec_data['expected_move'])
                        }
                    }
                )
            except Exception as e:
                import traceback
                print(f"Error recommending {symbol}: {str(e)}")
                traceback.print_exc()
                
    except Exception as e:
        print(f"ML Processing error: {e}")


@staff_member_required
@require_POST
def run_recommendations_view(request):
    """
    Trigger batch recommendations for ALL stocks in background
    """
    thread = threading.Thread(target=run_recommendations_logic)
    thread.daemon = True
    thread.start()
    
    messages.info(request, "AI Recommendation engine started for ALL stocks.")
    return redirect('admin_trading_dashboard')


@staff_member_required
@require_POST
def run_watchlist_recommendations_view(request):
    """
    Trigger AI recommendations ONLY for watchlist symbols
    """
    watchlist_symbols = Watchlist.objects.values_list('symbol', flat=True).distinct()
    
    if not watchlist_symbols:
        messages.warning(request, "No symbols found in any user's watchlist.")
        return redirect('admin_trading_dashboard')
    
    thread = threading.Thread(target=run_recommendations_logic, args=(list(watchlist_symbols),))
    thread.daemon = True
    thread.start()
    
    messages.info(request, f"AI Recommendations started for {len(watchlist_symbols)} watchlist symbols.")
    return redirect('admin_trading_dashboard')


@staff_member_required
@require_POST
def pause_market_view(request):
    """Pause the market simulation"""
    pause_market()
    messages.warning(request, "Market has been PAUSED.")
    return redirect('admin_trading_dashboard')


@staff_member_required
@require_POST
def resume_market_view(request):
    """Resume the market simulation"""
    force = request.POST.get('force') == 'true'
    resume_market(force=force)
    if force:
        messages.success(request, "Market has been FORCED to Resume.")
    else:
        messages.success(request, "Market has been RESUMED.")
    return redirect('admin_trading_dashboard')


@staff_member_required
@require_POST
def run_scraper_view(request):
    """
    Run scraper in a background thread
    """
    def run_command_thread():
        try:
            call_command('scrape_nepse')
        except Exception as e:
            print(f"Scraper error: {e}")

    thread = threading.Thread(target=run_command_thread)
    thread.daemon = True
    thread.start()
    
    messages.info(request, "Scraper started in background.")
    return redirect('admin_trading_dashboard')


@staff_member_required
@require_POST
def reset_market_control_view(request):
    """Reset to automatic market control"""
    from .services.market_session import get_current_session
    session = get_current_session()
    session.is_manual = False
    session.save()
    messages.info(request, "Market control reset to AUTOMATIC.")
    return redirect('admin_trading_dashboard')


@staff_member_required
@require_POST
def close_market_view(request):
    """Admin function to explicitly close the market"""
    from .services.market_session import get_current_session
    session = get_current_session()
    session.status = 'CLOSED'
    session.is_active = False
    session.is_manual = True
    session.save()
    messages.warning(request, "Market has been MANUALLY CLOSED.")
    return redirect('admin_trading_dashboard')
