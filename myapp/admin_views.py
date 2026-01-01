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

from .models import Order, TradeExecution, MarketSession, MarketSummary
from .services.market_session import get_current_session, pause_market, resume_market, get_nepal_time

@staff_member_required
def trading_dashboard(request):
    """
    Admin dashboard for trading engine monitoring
    """
    # Get current session info
    session = get_current_session()
    nepal_time = get_nepal_time()
    
    # Get recent orders
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:20]
    
    # Get recent trades
    recent_trades = TradeExecution.objects.select_related('buy_order', 'sell_order').order_by('-executed_at')[:20]
    
    # Market stats for today
    today_start = nepal_time.replace(hour=0, minute=0, second=0, microsecond=0)
    
    context = {
        'session': session,
        'nepal_time': nepal_time,
        'recent_orders': recent_orders,
        'recent_trades': recent_trades,
        'title': 'Trading Engine Dashboard'
    }
    
    return render(request, 'admin/trading_dashboard.html', context)


@staff_member_required
@require_POST
def pause_market_view(request):
    """Pause the market simulation"""
    pause_market()
    messages.warning(request, "Market has been PAUSED by admin.")
    return redirect('admin_trading_dashboard')


@staff_member_required
@require_POST
def resume_market_view(request):
    """Resume the market simulation"""
    resume_market()
    messages.success(request, "Market has been RESUMED.")
    return redirect('admin_trading_dashboard')


@staff_member_required
@require_POST
def run_scraper_view(request):
    """
    Run scraper in a background thread
    """
    def run_command():
        try:
            call_command('scrape_nepse')
        except Exception as e:
            print(f"Scraper error: {e}")

    thread = threading.Thread(target=run_command)
    thread.daemon = True
    thread.start()
    
    messages.info(request, "Scraper started in background. Check logs for progress.")
    return redirect('admin_trading_dashboard')
