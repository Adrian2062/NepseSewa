from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Max
from datetime import timedelta
from django.utils import timezone
from django.views.decorators.http import require_GET
from .forms import RegistrationForm
from .models import NEPSEPrice, NEPSEIndex, MarketIndex, MarketSummary, Order, TradeExecution, Portfolio, Watchlist, StockRecommendation



User = get_user_model()

# --- Email authentication backend ---
class EmailBackend(ModelBackend):
    """
    Authenticate using email instead of username.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        email = kwargs.get('email', username)
        if email is None or password is None:
            return None
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None


# ========== HELPER FUNCTIONS ==========
def get_nepse_context():
    """Helper function to get NEPSE data for templates"""
    try:
        latest_time = NEPSEPrice.objects.aggregate(Max('timestamp'))['timestamp__max']
        
        if not latest_time:
            return {
                'has_data': False,
                'market_stats': {},
                'top_gainers': [],
                'top_losers': []
            }
        
        # Get latest prices
        latest_prices = NEPSEPrice.objects.filter(timestamp=latest_time)
        
        # Market stats
        gainers = latest_prices.filter(change_pct__gt=0).count()
        losers = latest_prices.filter(change_pct__lt=0).count()
        total = latest_prices.count()
        
        # Top gainers
        top_gainers = list(latest_prices.order_by('-change_pct')[:5].values(
            'symbol', 'ltp', 'change_pct'
        ))
        
        # Top losers
        top_losers = list(latest_prices.order_by('change_pct')[:5].values(
            'symbol', 'ltp', 'change_pct'
        ))

        # Top Turnover (Active Stocks)
        top_turnover = list(latest_prices.order_by('-turnover')[:5].values(
            'symbol', 'ltp', 'change_pct', 'turnover'
        ))

        # --- LIVE DATA FETCHING ---
        try:
            nepse_index = NEPSEIndex.objects.latest('timestamp')
        except NEPSEIndex.DoesNotExist:
            nepse_index = None

        try:
            sensitive_index = MarketIndex.objects.filter(index_name='Sensitive Index').latest('timestamp')
        except MarketIndex.DoesNotExist:
            sensitive_index = None
            
        try:
            float_index = MarketIndex.objects.filter(index_name='Float Index').latest('timestamp')
        except MarketIndex.DoesNotExist:
            float_index = None

        try:
            market_summary = MarketSummary.objects.latest('timestamp')
        except MarketSummary.DoesNotExist:
            market_summary = None
        
        return {
            'has_data': True,
            'market_stats': {
                'total_symbols': total,
                'gainers': gainers,
                'losers': losers,
            },
            'top_gainers': top_gainers,
            'top_losers': top_losers,
            'top_turnover': top_turnover,
            'last_update': latest_time,
            # Added live indices
            'nepse_index': nepse_index,
            'sensitive_index': sensitive_index,
            'float_index': float_index,
            'market_summary': market_summary
        }
    except Exception as e:
        print(f"Error getting NEPSE context: {e}")
        return {
            'has_data': False,
            'market_stats': {},
            'top_gainers': [],
            'top_losers': [],
            'top_turnover': []
        }


# ========== PAGE VIEWS ==========
def landing_page(request):
    """Landing page with NEPSE data"""
    context = get_nepse_context()
    return render(request, 'landing.html', context)


def login_view(request):
    """Login view with NEPSE data"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    context = get_nepse_context()
    
    if request.method == 'POST':
        form_type = request.POST.get('form-type')
        
        if form_type == 'register':
            form = RegistrationForm(request.POST)
            if form.is_valid():
                user = form.save()
                login(request, user, backend='myapp.views.EmailBackend')
                messages.success(request, "Registration successful!")
                return redirect('dashboard')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
        else:
            # Login logic
            email = request.POST.get('email')
            password = request.POST.get('password')
            
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid email or password')
    
    return render(request, 'login.html', context)


def password_reset(request):
    if request.method == "POST":
        messages.success(request, "Password reset link sent!")
        return redirect("login")
    return render(request, "password_reset.html")


@login_required
def dashboard(request):
    context = get_nepse_context()
    context['active_page'] = 'dashboard'
    return render(request, 'dashboard.html', context)


@login_required
def portfolio(request):
    return render(request, 'portfolio.html', {'active_page': 'portfolio'})


@login_required
def trade(request):
    context = {'active_page': 'trade'}
    return render(request, 'trade.html', context)


@login_required
def market(request):
    context = get_nepse_context()
    context['active_page'] = 'market'
    return render(request, 'market.html', context)


@login_required
def watchlist(request):
    return render(request, 'watchlist.html', {'active_page': 'watchlist'})


@login_required
def learn(request):
    return render(request, 'learn.html', {'active_page': 'learn'})


@login_required
def settings_view(request):
    return render(request, 'settings.html', {'active_page': 'settings'})


def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('landing')


# ========== NEPSE API ENDPOINTS ==========

@require_http_methods(["GET"])
def api_latest_nepse(request):
    """Get latest NEPSE prices for all symbols"""
    try:
        latest_time = NEPSEPrice.objects.aggregate(Max('timestamp'))['timestamp__max']
        
        if not latest_time:
            return JsonResponse({'data': [], 'message': 'No data available'})
        
        data = list(NEPSEPrice.objects.filter(
            timestamp=latest_time
        ).values(
            'symbol', 'open', 'high', 'low', 'close', 'ltp', 
            'change_pct', 'volume', 'turnover'
        ).order_by('symbol'))
        
        return JsonResponse({
            'data': data,
            'count': len(data),
            'timestamp': latest_time.isoformat()
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def api_top_gainers(request):
    """Get top 10 gainer stocks"""
    try:
        latest_time = NEPSEPrice.objects.aggregate(Max('timestamp'))['timestamp__max']
        
        if not latest_time:
            return JsonResponse({'data': []})
        
        data = list(NEPSEPrice.objects.filter(
            timestamp=latest_time
        ).values(
            'symbol', 'ltp', 'change_pct', 'volume'
        ).order_by('-change_pct')[:10])
        
        return JsonResponse({
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def api_top_losers(request):
    """Get top 10 loser stocks"""
    try:
        latest_time = NEPSEPrice.objects.aggregate(Max('timestamp'))['timestamp__max']
        
        if not latest_time:
            return JsonResponse({'data': []})
        
        data = list(NEPSEPrice.objects.filter(
            timestamp=latest_time
        ).values(
            'symbol', 'ltp', 'change_pct', 'volume'
        ).order_by('change_pct')[:10])
        
        return JsonResponse({
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def api_market_stats(request):
    """Get market statistics"""
    try:
        latest_time = NEPSEPrice.objects.aggregate(Max('timestamp'))['timestamp__max']
        
        if not latest_time:
            return JsonResponse({
                'gainers': 0,
                'losers': 0,
                'unchanged': 0,
                'total': 0
            })
        
        latest_prices = NEPSEPrice.objects.filter(timestamp=latest_time)
        
        gainers = latest_prices.filter(change_pct__gt=0).count()
        losers = latest_prices.filter(change_pct__lt=0).count()
        unchanged = latest_prices.filter(change_pct=0).count()
        total = latest_prices.count()
        
        return JsonResponse({
            'gainers': gainers,
            'losers': losers,
            'unchanged': unchanged,
            'total': total,
            'timestamp': latest_time.isoformat()
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def api_symbol_history(request):
    """Get price history for a symbol"""
    try:
        symbol = request.GET.get('symbol', 'ACLBSL').upper()
        hours = int(request.GET.get('hours', 24))
        
        since = timezone.now() - timedelta(hours=hours)
        data = list(NEPSEPrice.objects.filter(
            symbol=symbol,
            timestamp__gte=since
        ).values(
            'timestamp', 'open', 'high', 'low', 'close', 'ltp', 'change_pct', 'volume'
        ).order_by('timestamp'))
        
        return JsonResponse({
            'symbol': symbol,
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def api_search_symbol(request):
    """Search for a symbol"""
    try:
        query = request.GET.get('q', '').upper()
        
        if not query:
            return JsonResponse({'data': []})
        
        latest_time = NEPSEPrice.objects.aggregate(Max('timestamp'))['timestamp__max']
        
        if not latest_time:
            return JsonResponse({'data': []})
        
        symbols = list(NEPSEPrice.objects.filter(
            timestamp=latest_time,
            symbol__icontains=query
        ).values(
            'symbol', 'ltp', 'change_pct'
        )[:10])
        
        return JsonResponse({'data': symbols})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
# Add these to your myapp/views.py file (at the end with other API endpoints)

from .models import NEPSEIndex, MarketSummary, MarketIndex

@require_http_methods(["GET"])
def api_nepse_index(request):
    """Get latest NEPSE Index value with daily change"""
    try:
        latest = NEPSEIndex.objects.latest('timestamp')
        
        # Calculate daily change
        # Find the last record from a previous date (yesterday's close)
        previous_close = NEPSEIndex.objects.filter(
            timestamp__date__lt=latest.timestamp.date()
        ).order_by('-timestamp').first()

        if previous_close and previous_close.index_value:
            change = latest.index_value - previous_close.index_value
            change_pct = (change / previous_close.index_value) * 100
        else:
            # Fallback if no previous day data (e.g. first day of scraping)
            # Try to use the percentage_change field if it exists and is non-zero
            change_pct = float(latest.percentage_change or 0)

        return JsonResponse({
            'success': True,
            'data': {
                'value': float(latest.index_value),
                'change_pct': float(change_pct),
                'timestamp': latest.timestamp.isoformat(),
            }
        })
    except NEPSEIndex.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'No NEPSE Index data available'
        }, status=404)


@require_http_methods(["GET"])
def api_market_summary(request):
    """Get latest market summary"""
    try:
        latest = MarketSummary.objects.latest('timestamp')
        return JsonResponse({
            'success': True,
            'data': {
                'total_turnover': float(latest.total_turnover or 0),
                'total_traded_shares': float(latest.total_traded_shares or 0),
                'total_transactions': float(latest.total_transactions or 0),
                'total_scrips': float(latest.total_scrips or 0),
                'timestamp': latest.timestamp.isoformat(),
            }
        })
    except MarketSummary.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'No market summary data available'
        }, status=404)


@require_http_methods(["GET"])
def api_sector_indices(request):
    """Get latest sector indices"""
    try:
        latest_time = MarketIndex.objects.latest('timestamp').timestamp
        
        indices = MarketIndex.objects.filter(
            timestamp=latest_time
        ).exclude(
            index_name='NEPSE Index'
        ).order_by('index_name')
        
        data = [{
            'name': idx.index_name,
            'value': float(idx.value),
            'change_pct': float(idx.change_pct),
        } for idx in indices]
        
        return JsonResponse({
            'success': True,
            'data': data,
            'timestamp': latest_time.isoformat(),
        })
    except MarketIndex.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'No sector indices data available'
        }, status=404)
@login_required
def stocks(request):
    # just render page; it will load data using /api/latest/
    return render(request, "stocks.html")

@login_required
def trade(request):
    return render(request, 'trade.html')

from .models import Trade  # make sure this matches your model name

@require_GET
@login_required
def api_trade_history(request):
    """
    GET /api/trade/history/?symbol=NBL
    Returns ONLY the logged-in user's BUY/SELL history.
    """
    symbol = (request.GET.get('symbol') or '').strip().upper()
    side = (request.GET.get('side') or '').strip().upper()  # optional filter BUY/SELL

    qs = Trade.objects.filter(user=request.user)

    if symbol:
        qs = qs.filter(symbol__iexact=symbol)

    if side in ['BUY', 'SELL']:
        qs = qs.filter(side=side)

    qs = qs.order_by('-created_at')[:200]

    data = [{
        "created_at": t.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "symbol": t.symbol,
        "side": t.side,
        "qty": t.qty,
        "price": t.price,
        "status": t.status,
    } for t in qs]

    return JsonResponse({"success": True, "data": data})


@require_http_methods(["POST"])
@login_required
def api_place_order(request):
    """
    POST /api/trade/place/
    body: {symbol, side, qty, price}
    """
    import json
    try:
        data = json.loads(request.body)
        symbol = (data.get('symbol') or '').strip().upper()
        side = (data.get('side') or '').strip().upper()
        
        try:
            qty = int(data.get('qty', 0))
            price = float(data.get('price', 0.0))
        except ValueError:
            return JsonResponse({'success': False, 'message': 'Invalid quantity or price.'})

        if not symbol:
            return JsonResponse({'success': False, 'message': 'Symbol is required.'})
        
        if side not in ['BUY', 'SELL']:
            return JsonResponse({'success': False, 'message': 'Invalid side (BUY/SELL).'})
            
        if qty <= 0:
            return JsonResponse({'success': False, 'message': 'Quantity must be positive.'})
            
        if price <= 0:
            return JsonResponse({'success': False, 'message': 'Price must be positive.'})

        user = request.user
        total_cost = qty * price

        if side == 'BUY':
            # Convert to Decimal for precise calculation
            from decimal import Decimal
            cost_decimal = Decimal(str(total_cost))
            
            if user.virtual_balance < cost_decimal:
                 return JsonResponse({
                    'success': False, 
                    'message': f'Insufficient balance. Your limit is Rs {user.virtual_balance:,.2f} but order cost is Rs {total_cost:,.2f}.'
                })
            
            user.virtual_balance -= cost_decimal
            user.save()

        elif side == 'SELL':
            # For now, we don't check portfolio holdings (as per request simplicity/focus on BUY limit)
            # But we should credit the user
            from decimal import Decimal
            cost_decimal = Decimal(str(total_cost))
            user.virtual_balance += cost_decimal
            user.save()

        # Create Trade
        Trade.objects.create(
            user=user,
            symbol=symbol,
            side=side,
            qty=qty,
            price=price,
            status='COMPLETED'
        )

        return JsonResponse({
            'success': True, 
            'message': f'Order placed successfully! {side} {qty} {symbol} @ {price}'
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

# Add these new API endpoints to your existing views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_GET
from django.db.models import Max
from datetime import datetime, timedelta
from django.utils import timezone
from .forms import RegistrationForm
from .models import NEPSEPrice, NEPSEIndex, MarketIndex, MarketSummary, Order, TradeExecution, Portfolio, Trade, Stock, Watchlist, StockRecommendation

User = get_user_model()

# ... [Keep all your existing code: EmailBackend, get_nepse_context, landing_page, 
#      login_view, password_reset, dashboard, portfolio, trade, market, watchlist, 
#      learn, settings_view, logout_view, api_latest_nepse, api_top_gainers, 
#      api_top_losers, api_market_stats, api_symbol_history, api_search_symbol,
#      api_nepse_index, api_market_summary, api_sector_indices, stocks, 
#      api_trade_history, api_place_order] ...

# ========== NEW DATE-FILTERED API ENDPOINTS ==========

@require_http_methods(["GET"])
@login_required
def api_sectors(request):
    """Return list of distinct sectors for dropdown"""
    sectors = Stock.objects.values_list('sector', flat=True).distinct().order_by('sector')
    # Filter out empty or None
    clean_sectors = [s for s in sectors if s and s != 'Others'] + ['Others']
    # Unique/Sort
    final_sectors = sorted(list(set(clean_sectors)))
    if 'Others' in final_sectors:
        final_sectors.remove('Others')
        final_sectors.append('Others') # Put Others at end
        
    return JsonResponse({'success': True, 'sectors': final_sectors})

@require_http_methods(["GET"])
@login_required
def api_market_data_by_date(request):
    """
    API to get market data for a specific date, with optional sector/search filtering.
    """
    date_str = request.GET.get('date')
    sector_filter = request.GET.get('sector')
    search_query = request.GET.get('search', '').strip().upper()

    # 1. Determine Date
    if date_str:
        try:
            filter_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid date format'}, status=400)
    else:
        # Default to latest available date
        latest_entry = NEPSEPrice.objects.order_by('-timestamp').first()
        if not latest_entry:
             return JsonResponse({'success': True, 'stocks': [], 'date': str(timezone.now().date())})
        filter_date = latest_entry.timestamp.date()

    # 2. Optimization: Filter by Sector at DB level if possible
    relevant_symbols = None
    if sector_filter and sector_filter != 'All Sectors':
        relevant_symbols = list(Stock.objects.filter(sector__iexact=sector_filter).values_list('symbol', flat=True))
    
    # 3. Fetch Prices
    qs = NEPSEPrice.objects.filter(timestamp__date=filter_date)
    
    if relevant_symbols is not None:
        qs = qs.filter(symbol__in=relevant_symbols)
        
    if search_query:
        qs = qs.filter(symbol__icontains=search_query)

    all_prices_that_day = qs.values(
        'symbol', 'open', 'high', 'low', 'close', 'ltp',
        'change_pct', 'volume', 'turnover', 'timestamp'
    ).order_by('symbol', '-timestamp')

    # Deduplicate: Keep only latest timestamp for each symbol
    unique_prices = {}
    for p in all_prices_that_day:
        sym = p['symbol'].strip().upper()
        if sym not in unique_prices:
            unique_prices[sym] = p

    # Batch fetch sectors for the found symbols
    found_symbols = list(unique_prices.keys())
    stock_map = {s.symbol: s.sector for s in Stock.objects.filter(symbol__in=found_symbols)}

    stocks_data = []
    for sym, item in unique_prices.items():
        # Final Search Filter
        if search_query and search_query not in sym:
            continue
            
        # Get sector
        item_sector = stock_map.get(sym, 'Others')
        
        # Final Sector Filter
        if sector_filter and sector_filter != 'All Sectors' and sector_filter.lower() != item_sector.lower():
            continue
            
        item['sector'] = item_sector
        item['symbol'] = sym
        stocks_data.append(item)

    stocks_data.sort(key=lambda x: x['symbol'])

    return JsonResponse({
        'success': True, 
        'stocks': stocks_data,
        'date': str(filter_date),
        'count': len(stocks_data)
    })


@require_http_methods(["GET"])
def api_available_dates(request):
    """
    Get list of dates that have scraped data
    GET /api/available-dates/
    """
    try:
        # Get distinct dates from NEPSEPrice model
        dates = NEPSEPrice.objects.dates('timestamp', 'day', order='DESC')
        
        date_list = [date.strftime('%Y-%m-%d') for date in dates]
        
        return JsonResponse({
            'success': True,
            'dates': date_list,
            'total_days': len(date_list),
            'latest_date': date_list[0] if date_list else None,
            'oldest_date': date_list[-1] if date_list else None
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def api_stock_history_range(request, symbol):
    """
    Get historical data for a specific stock
    GET /api/stock-history/NABIL/?days=30
    GET /api/stock-history/NABIL/?start_date=2025-01-01&end_date=2025-01-31
    """
    try:
        symbol = symbol.upper()
        
        # Check for date range parameters
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        days = int(request.GET.get('days', 30))
        
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        else:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
        
        # Get history for date range
        history = NEPSEPrice.objects.filter(
            symbol=symbol,
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).order_by('timestamp')
        
        if not history.exists():
            return JsonResponse({
                'success': False,
                'error': f'No data found for symbol {symbol}'
            }, status=404)
        
        return JsonResponse({
            'success': True,
            'symbol': symbol,
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'data_points': history.count(),
            'history': [
                {
                    'date': h.timestamp.strftime('%Y-%m-%d'),
                    'time': h.timestamp.strftime('%H:%M:%S'),
                    'timestamp': h.timestamp.isoformat(),
                    'open': float(h.open or 0),
                    'high': float(h.high or 0),
                    'low': float(h.low or 0),
                    'close': float(h.close or 0),
                    'ltp': float(h.ltp or 0),
                    'volume': float(h.volume or 0),
                    'turnover': float(h.turnover or 0),
                    'change_pct': float(h.change_pct or 0)
                }
                for h in history
            ]
        })
    except ValueError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid date format. Use YYYY-MM-DD'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def api_date_range_summary(request):
    """
    Get summary statistics for a date range
    GET /api/date-range-summary/?start_date=2025-01-01&end_date=2025-01-31
    """
    try:
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        if not start_date_str or not end_date_str:
            return JsonResponse({
                'success': False,
                'error': 'Both start_date and end_date are required'
            }, status=400)
        
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        
        # Get all dates with data in range
        dates_with_data = NEPSEPrice.objects.filter(
            timestamp__date__gte=start_date.date(),
            timestamp__date__lte=end_date.date()
        ).dates('timestamp', 'day')
        
        # Get NEPSE index values for the range
        nepse_indices = NEPSEIndex.objects.filter(
            timestamp__date__gte=start_date.date(),
            timestamp__date__lte=end_date.date()
        ).order_by('timestamp')
        
        first_index = nepse_indices.first()
        last_index = nepse_indices.last()
        
        index_change = None
        index_change_pct = None
        if first_index and last_index:
            index_change = float(last_index.index_value - first_index.index_value)
            index_change_pct = (index_change / first_index.index_value) * 100
        
        return JsonResponse({
            'success': True,
            'start_date': start_date_str,
            'end_date': end_date_str,
            'trading_days': len(dates_with_data),
            'dates': [d.strftime('%Y-%m-%d') for d in dates_with_data],
            'nepse_index_summary': {
                'first_value': float(first_index.index_value) if first_index else None,
                'last_value': float(last_index.index_value) if last_index else None,
                'change': index_change,
                'change_pct': index_change_pct
            } if first_index and last_index else None
        })
        
    except ValueError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid date format. Use YYYY-MM-DD'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ========== WATCHLIST & RECOMMENDATION API ==========

@login_required
@require_http_methods(["GET"])
def api_get_watchlist(request):
    """Get the current user's watchlist symbols"""
    watchlist = Watchlist.objects.filter(user=request.user).values_list('symbol', flat=True)
    return JsonResponse({'success': True, 'watchlist': list(watchlist)})


@login_required
@require_http_methods(["POST"])
def api_toggle_watchlist(request):
    """Add or remove a symbol from the user's watchlist"""
    import json
    try:
        data = json.loads(request.body)
        symbol = data.get('symbol', '').strip().upper()
        if not symbol:
            return JsonResponse({'success': False, 'message': 'Symbol is required'})
        
        watchlist_item = Watchlist.objects.filter(user=request.user, symbol=symbol).first()
        if watchlist_item:
            watchlist_item.delete()
            action = 'removed'
        else:
            Watchlist.objects.create(user=request.user, symbol=symbol)
            action = 'added'
            
        return JsonResponse({'success': True, 'action': action, 'symbol': symbol})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@require_http_methods(["GET"])
def api_get_recommendations(request):
    """Fetch stored recommendations for symbols in user's watchlist"""
    user_symbols = Watchlist.objects.filter(user=request.user).values_list('symbol', flat=True)
    
    # Get latest price for context
    latest_time = NEPSEPrice.objects.aggregate(Max('timestamp'))['timestamp__max']
    
    recs = StockRecommendation.objects.filter(symbol__in=user_symbols)
    
    data = []
    for rec in recs:
        # Get actual current price if available
        curr = NEPSEPrice.objects.filter(symbol=rec.symbol, timestamp=latest_time).first()
        ltp = curr.ltp if curr else rec.current_price
        
        data.append({
            'symbol': rec.symbol,
            'current_price': ltp,
            'predicted_price': rec.predicted_next_close,
            'recommendation': rec.recommendation,
            'recommendation_str': rec.get_recommendation_display(),
            'rmse': rec.rmse,
            'mae': rec.mae,
            'last_updated': rec.last_updated.isoformat()
        })
        
    return JsonResponse({'success': True, 'data': data})


@login_required
@require_http_methods(["POST"])
def api_refresh_recommendation(request):
    """Trigger LSTM training and prediction for a stock"""
    import json
    from .ml_services import MLService, get_recommendation
    
    try:
        data = json.loads(request.body)
        symbol = data.get('symbol', '').strip().upper()
        if not symbol:
            return JsonResponse({'success': False, 'message': 'Symbol is required'})
            
        # 1. Fetch historical data (at least 60 days if possible)
        # We'll take last 100 entries to ensure we have enough for sliding window
        history_qs = NEPSEPrice.objects.filter(symbol=symbol).order_by('-timestamp')[:100]
        history_data = list(history_qs.values('timestamp', 'open', 'high', 'low', 'close', 'volume'))
        
        if len(history_data) < 40: # Minimum data check
            return JsonResponse({
                'success': False, 
                'message': f'Insufficient data for {symbol}. Need at least 40 trading days (have {len(history_data)}).'
            })

        # 2. Run ML Pipeline
        ml = MLService(history_data)
        predicted_price, rmse, mae, last_close = ml.train_and_predict(window_size=30)
        
        if predicted_price is None:
             return JsonResponse({'success': False, 'message': 'Model training failed.'})

        rec_val = get_recommendation(last_close, predicted_price)
        
        # 3. Save/Update Recommendation
        rec_obj, created = StockRecommendation.objects.update_or_create(
            symbol=symbol,
            defaults={
                'current_price': last_close,
                'predicted_next_close': predicted_price,
                'recommendation': rec_val,
                'rmse': rmse,
                'mae': mae
            }
        )
        
        return JsonResponse({
            'success': True,
            'data': {
                'symbol': symbol,
                'predicted_price': predicted_price,
                'recommendation': rec_obj.get_recommendation_display(),
                'rmse': rmse,
                'mae': mae
            }
        })
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'message': str(e)})
