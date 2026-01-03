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
from .models import NEPSEPrice, NEPSEIndex, MarketIndex, MarketSummary, Order, TradeExecution, Portfolio



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
            'top_losers': []
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
    return render(request, 'dashboard.html', context)


@login_required
def portfolio(request):
    return render(request, 'portfolio.html')


@login_required
def trade(request):
    return render(request, 'trade.html')


@login_required
def market(request):
    context = get_nepse_context()
    return render(request, 'market.html', context)


@login_required
def watchlist(request):
    return render(request, 'watchlist.html')


@login_required
def learn(request):
    return render(request, 'learn.html')


@login_required
def settings_view(request):
    return render(request, 'settings.html')


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
    """Get latest NEPSE Index value"""
    try:
        latest = NEPSEIndex.objects.latest('timestamp')
        return JsonResponse({
            'success': True,
            'data': {
                'value': float(latest.index_value),
                'change_pct': float(latest.percentage_change),
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
