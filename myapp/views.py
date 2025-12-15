from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from .forms import RegistrationForm

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

# --- Views ---
# def landing_page(request):
#     return render(request, 'landing.html')


# def login_view(request):
#     if request.method == 'POST':
#         form_type = request.POST.get('form-type')
#         if form_type == 'login':
#             email = request.POST.get('email')
#             password = request.POST.get('password')

#             user = authenticate(request, email=email, password=password)
#             if user:
#                 login(request, user)
#                 return redirect('dashboard')

#             messages.error(request, "Invalid email or password")
#             return redirect('login')

#         # REGISTER
#         elif form_type == 'register':
#             form = RegistrationForm(request.POST)
#             if form.is_valid():
#                 form.save()
#                 messages.success(request, "Account created successfully! Please login.")
#                 return redirect('login')
#             return render(request, 'login.html', {'form': form})

#     return render(request, 'login.html')

def landing_page(request):
    """Landing page with NEPSE data"""
    context = get_nepse_context()
    return render(request, 'landing.html', context)


# REPLACE your existing login_view function with this:
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
    return render(request, 'dashboard.html')

@login_required
def portfolio(request):
    return render(request, 'portfolio.html')

@login_required
def trade(request):
    return render(request, 'trade.html')

@login_required
def market(request):
    return render(request, 'market.html')

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

# views.py - Add this to your myapp/views.py



from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from datetime import datetime
from myapp.nepse_service import nepse_service


# ========== MARKET SUMMARY ==========
@require_http_methods(["GET"])
def get_market_summary(request):
    """Get market summary data"""
    try:
        summary = nepse_service.get_summary()
        if summary:
            result = {
                'data': summary,
                'timestamp': datetime.now().isoformat()
            }
            return JsonResponse(result)
        return JsonResponse({"error": "Could not fetch summary"}, status=503)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ========== TOP GAINERS ==========
@require_http_methods(["GET"])
def get_top_gainers(request):
    """Get top gainer stocks"""
    try:
        gainers = nepse_service.get_top_gainers()
        result = {
            'data': gainers,
            'count': len(gainers),
            'timestamp': datetime.now().isoformat()
        }
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ========== TOP LOSERS ==========
@require_http_methods(["GET"])
def get_top_losers(request):
    """Get top loser stocks"""
    try:
        losers = nepse_service.get_top_losers()
        result = {
            'data': losers,
            'count': len(losers),
            'timestamp': datetime.now().isoformat()
        }
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ========== TOP VOLUME STOCKS ==========
@require_http_methods(["GET"])
def get_top_volume_stocks(request):
    """Get top traded stocks by volume"""
    try:
        volume_stocks = nepse_service.get_top_by_volume()
        result = {
            'data': volume_stocks,
            'count': len(volume_stocks),
            'timestamp': datetime.now().isoformat()
        }
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ========== TOP TURNOVER STOCKS ==========
@require_http_methods(["GET"])
def get_top_turnover_stocks(request):
    """Get top stocks by turnover"""
    try:
        turnover_stocks = nepse_service.get_top_by_turnover()
        result = {
            'data': turnover_stocks,
            'count': len(turnover_stocks),
            'timestamp': datetime.now().isoformat()
        }
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ========== MARKET OVERVIEW ==========
@require_http_methods(["GET"])
def get_market_overview(request):
    """Get overview of market"""
    try:
        market_data = nepse_service.get_market_data()
        if market_data:
            result = {
                'data': market_data,
                'timestamp': datetime.now().isoformat()
            }
            return JsonResponse(result)
        return JsonResponse({"error": "Could not fetch market data"}, status=503)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ========== SECURITY WISE INFO ==========
@require_http_methods(["GET"])
def get_security_wise_info(request):
    """Get all security/stock information"""
    try:
        market_data = nepse_service.get_market_data()
        if market_data:
            stocks = market_data.get('data', [])
            result = {
                'data': stocks,
                'count': len(stocks),
                'timestamp': datetime.now().isoformat()
            }
            return JsonResponse(result)
        return JsonResponse({"error": "Could not fetch security info"}, status=503)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ========== SECTOR WISE INFO ==========
@require_http_methods(["GET"])
def get_sector_wise_info(request):
    """Get sector-wise information"""
    try:
        market_data = nepse_service.get_market_data()
        if market_data:
            stocks = market_data.get('data', [])
            
            # Group by sector
            sectors = {}
            for stock in stocks:
                sector = stock.get('businessType', 'Other')
                if sector not in sectors:
                    sectors[sector] = []
                sectors[sector].append(stock)
            
            result = {
                'data': sectors,
                'timestamp': datetime.now().isoformat()
            }
            return JsonResponse(result)
        return JsonResponse({"error": "Could not fetch sector info"}, status=503)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ========== NEPSE INDEX ==========
@require_http_methods(["GET"])
def get_nepse_index(request):
    """Get NEPSE Index data"""
    try:
        index_data = nepse_service.get_index_data()
        if index_data:
            result = {
                'data': index_data,
                'timestamp': datetime.now().isoformat()
            }
            return JsonResponse(result)
        return JsonResponse({"error": "Could not fetch index data"}, status=503)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ========== DASHBOARD DATA (Combined) ==========
@require_http_methods(["GET"])
def get_dashboard_data(request):
    """Get all dashboard data in one call"""
    try:
        all_data = nepse_service.get_all_data()
        return JsonResponse(all_data)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    

# new 
# ADD THESE AT THE END OF myapp/views.py

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Max, Count, Q
from myapp.models import NEPSEPrice
from datetime import timedelta
from django.utils import timezone

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


@require_http_methods(["GET"])
def get_nepse_latest(request):
    """API: Get latest NEPSE prices for all symbols"""
    try:
        latest_time = NEPSEPrice.objects.aggregate(Max('timestamp'))['timestamp__max']
        
        if not latest_time:
            return JsonResponse({'data': [], 'message': 'No data available'})
        
        data = list(NEPSEPrice.objects.filter(
            timestamp=latest_time
        ).values(
            'symbol', 'timestamp', 'open', 'high', 'low', 
            'close', 'ltp', 'change_pct', 'volume', 'turnover'
        ).order_by('symbol'))
        
        return JsonResponse({
            'data': data,
            'count': len(data),
            'timestamp': latest_time.isoformat()
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_nepse_history(request):
    """API: Get price history for a symbol"""
    try:
        symbol = request.GET.get('symbol', 'ACLBSL')
        hours = int(request.GET.get('hours', 24))
        
        since = timezone.now() - timedelta(hours=hours)
        data = list(NEPSEPrice.objects.filter(
            symbol=symbol,
            timestamp__gte=since
        ).values(
            'symbol', 'timestamp', 'open', 'high', 'low', 
            'close', 'ltp', 'change_pct', 'volume', 'turnover'
        ).order_by('timestamp'))
        
        return JsonResponse({
            'symbol': symbol,
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_top_gainers_nepse(request):
    """API: Get top gainer stocks"""
    try:
        latest_time = NEPSEPrice.objects.aggregate(Max('timestamp'))['timestamp__max']
        
        if not latest_time:
            return JsonResponse({'data': []})
        
        data = list(NEPSEPrice.objects.filter(
            timestamp=latest_time
        ).values(
            'symbol', 'close', 'ltp', 'change_pct', 'volume', 'turnover'
        ).order_by('-change_pct')[:10])
        
        return JsonResponse({
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_top_losers_nepse(request):
    """API: Get top loser stocks"""
    try:
        latest_time = NEPSEPrice.objects.aggregate(Max('timestamp'))['timestamp__max']
        
        if not latest_time:
            return JsonResponse({'data': []})
        
        data = list(NEPSEPrice.objects.filter(
            timestamp=latest_time
        ).values(
            'symbol', 'close', 'ltp', 'change_pct', 'volume', 'turnover'
        ).order_by('change_pct')[:10])
        
        return JsonResponse({
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)