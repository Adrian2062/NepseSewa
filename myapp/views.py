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

from .forms import RegistrationForm
from .models import NEPSEPrice

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
        
        return {
            'has_data': True,
            'market_stats': {
                'total_symbols': total,
                'gainers': gainers,
                'losers': losers,
            },
            'top_gainers': top_gainers,
            'top_losers': top_losers,
            'last_update': latest_time
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