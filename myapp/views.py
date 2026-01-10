from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Max, Q, Avg, Count
from datetime import timedelta
from django.utils import timezone
from django.views.decorators.http import require_GET
from .forms import RegistrationForm
from .models import (
    NEPSEPrice, NEPSEIndex, MarketIndex, MarketSummary, Order, TradeExecution, 
    Portfolio, Watchlist, StockRecommendation, CandlestickLesson, UserLessonProgress,
    Course, CourseCategory, UserCourseProgress
)



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
    """
    Updated Learn View to display Courses instead of individual lessons.
    Supports Search, Category Filter, and Difficulty Filter.
    """
    
    # --- Filter Parameters ---
    search_query = request.GET.get('q', '')
    category_slug = request.GET.get('category', '')
    difficulty = request.GET.get('difficulty', '')

    # --- Base Query ---
    courses = Course.objects.all().order_by('-is_featured', '-created_at')

    # --- Apply Filters ---
    if search_query:
        courses = courses.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    if category_slug and category_slug != 'all':
        courses = courses.filter(category__slug=category_slug)

    if difficulty and difficulty != 'all':
        courses = courses.filter(difficulty=difficulty)

    # --- Prepare Course Data (Progress Calculation) ---
    course_data = []
    for course in courses:
        # Get total lessons in course
        total_lessons = course.lessons.count()
        
        progress_pct = 0
        is_completed = False
        first_incomplete_lesson = None

        if total_lessons > 0:
            # Get user's completed lessons for this course
            completed_lessons_count = UserLessonProgress.objects.filter(
                user=request.user, 
                lesson__course=course, 
                is_completed=True
            ).count()
            
            progress_pct = (completed_lessons_count / total_lessons) * 100
            is_completed = completed_lessons_count == total_lessons
            
            # Find first incomplete lesson to "Start/Continue"
            # Get IDs of completed lessons
            completed_lesson_ids = UserLessonProgress.objects.filter(
                user=request.user, 
                lesson__course=course, 
                is_completed=True
            ).values_list('lesson_id', flat=True)
            
            first_incomplete_lesson = course.lessons.exclude(id__in=completed_lesson_ids).order_by('order').first()

            # Update or Create UserCourseProgress record
            UserCourseProgress.objects.update_or_create(
                user=request.user,
                course=course,
                defaults={
                    'progress_percent': progress_pct,
                    'is_completed': is_completed
                }
            )

        course_data.append({
            'course': course,
            'progress': int(progress_pct), # passed as integer for cleaner UI
            'is_completed': is_completed,
            'total_lessons': total_lessons,
            'next_lesson': first_incomplete_lesson,
            'first_lesson': course.lessons.first() if total_lessons > 0 else None
        })

    # --- Categories for Filter Dropdown ---
    categories = CourseCategory.objects.all()

    # --- Featured Courses (Top 3) ---
    featured_courses = [c for c in course_data if c['course'].is_featured][:3]

    context = {
        'active_page': 'learn',
        'course_data': course_data,
        'categories': categories,
        'featured_courses': featured_courses,
        'search_query': search_query,
        'selected_category': category_slug,
        'selected_difficulty': difficulty,
    }
    return render(request, 'learn.html', context)


@login_required
def course_detail(request, course_id):
    """
    Detailed view for a specific course, listing all lessons.
    """
    course = get_object_or_404(Course, id=course_id)
    lessons = course.lessons.all().order_by('order')
    
    # Calculate progress
    lesson_data = []
    completed_count = 0
    
    for lesson in lessons:
        progress_obj = UserLessonProgress.objects.filter(user=request.user, lesson=lesson).first()
        is_completed = progress_obj.is_completed if progress_obj else False
        if is_completed:
            completed_count += 1
            
        lesson_data.append({
            'lesson': lesson,
            'is_completed': is_completed,
            'is_locked': False # Can implement locking logic later (e.g. must complete prev)
        })

    total_lessons = lessons.count()
    progress_pct = (completed_count / total_lessons * 100) if total_lessons > 0 else 0
    
    context = {
        'active_page': 'learn',
        'course': course,
        'lesson_data': lesson_data,
        'progress_pct': int(progress_pct),
        'total_lessons': total_lessons,
        'completed_count': completed_count
    }
    return render(request, 'learn/course_detail.html', context)


@login_required
def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(CandlestickLesson, id=lesson_id)
    
    # Mark as In Progress if accessed
    UserLessonProgress.objects.get_or_create(user=request.user, lesson=lesson)
    
    # Logic for next/prev lesson WITHIN THE COURSE
    if lesson.course:
        all_lessons = list(lesson.course.lessons.order_by('order'))
        try:
            current_index = all_lessons.index(lesson)
            previous_lesson = all_lessons[current_index - 1] if current_index > 0 else None
            next_lesson = all_lessons[current_index + 1] if current_index < len(all_lessons) - 1 else None
        except ValueError:
            previous_lesson = None
            next_lesson = None
    else:
        # Fallback for orphan lessons (shouldn't happen with new logic, but safety first)
        previous_lesson = None
        next_lesson = None

    is_completed = UserLessonProgress.objects.filter(user=request.user, lesson=lesson, is_completed=True).exists()

    # Handle completion (POST request)
    if request.method == 'POST' and 'mark_complete' in request.POST:
        UserLessonProgress.objects.update_or_create(
            user=request.user, 
            lesson=lesson,
            defaults={'is_completed': True}
        )
        is_completed = True
        messages.success(request, f"Lesson '{lesson.title}' completed! 🎉")
        
        # Determine redirect
        if next_lesson:
            return redirect('lesson_detail', lesson_id=next_lesson.id)
        else:
            # Finished course
            messages.success(request, f"Congratulations! You've finished the course '{lesson.course.title}'! 🎓")
            return redirect('course_detail', course_id=lesson.course.id)

    context = {
        'lesson': lesson,
        'is_completed': is_completed,
        'previous_lesson': previous_lesson,
        'next_lesson': next_lesson,
        'active_page': 'learn',
        'course': lesson.course 
    }
    return render(request, 'learn/lesson_detail.html', context)



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

# Helper to sanitize NaN/Inf for JSON
def sanitize_float(val):
    import math
    if val is None or (isinstance(val, float) and (math.isnan(val) or math.isinf(val))):
        return None
    return float(val)

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
    """
    Fetch stored recommendations.
    Params: filter='all' (returns ALL system stocks with optional recs) OR defaults to user's watchlist.
    """
    try:
        filter_type = request.GET.get('filter', 'watchlist')
        
        # Get latest price for context
        latest_time_agg = NEPSEPrice.objects.aggregate(Max('timestamp'))
        latest_time = latest_time_agg['timestamp__max']
        
        if not latest_time:
             return JsonResponse({'success': True, 'data': [], 'message': 'No market data available.'})

        # Fetch Pre-computed recommendations for lookup
        all_recs_qs = StockRecommendation.objects.all()
        rec_map = {r.symbol: r for r in all_recs_qs}

        data = []

        if filter_type == 'all':
            # Get ALL distinct symbols from Stock model (Total ~323)
            # If Stock model is empty, fallback to NEPSEPrice distinct symbols
            all_symbols = Stock.objects.values_list('symbol', flat=True).order_by('symbol')
            if not all_symbols:
                all_symbols = NEPSEPrice.objects.values_list('symbol', flat=True).distinct().order_by('symbol')
            
            target_symbols = all_symbols
        else:
            # Default: User Watchlist only
            target_symbols = Watchlist.objects.filter(user=request.user).values_list('symbol', flat=True)
            if not target_symbols:
                 return JsonResponse({'success': True, 'data': []})

        # Iterate through target symbols (either ALL or Watchlist)
        for symbol in target_symbols:
            rec = rec_map.get(symbol)
            
            # Get actual current price if available
            curr = NEPSEPrice.objects.filter(symbol=symbol, timestamp=latest_time).first()
            
            # If we show 'All Market', we want to show stocks even if they don't have predictions yet
            if not curr and not rec:
                # If truly no data, we might skip or show as 'No Data'
                # For 'All Market', better to show with empty values than hide it
                 data.append({
                    'symbol': symbol,
                    'current_price': 0,
                    'predicted_price': 0,
                    'recommendation': 0,
                    'recommendation_str': 'WAITING',
                    'rmse': None,
                    'mae': None,
                    'last_updated': None,
                    'status': 'No Data'
                })
                 continue
            
            ltp = curr.ltp if curr else (rec.current_price if rec else 0)
            
            # Determine prediction values (or defaults if missing)
            pred_price = rec.predicted_next_close if rec else 0
            rec_val = rec.recommendation if rec else 0
            rec_str = rec.get_recommendation_display() if rec else 'PENDING'
            rmse_val = rec.rmse if rec else None
            mae_val = rec.mae if rec else None
            last_upd = rec.last_updated.isoformat() if rec else None
            
            data.append({
                'symbol': symbol,
                'current_price': sanitize_float(ltp),
                'predicted_price': sanitize_float(pred_price),
                'recommendation': rec_val,
                'recommendation_str': rec_str,
                'rmse': sanitize_float(rmse_val),
                'mae': sanitize_float(mae_val),
                'last_updated': last_upd
            })
            
        return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        import traceback
        print(f"Error in api_get_recommendations: {e}")
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'message': 'Internal Server Error fetching recommendations.', 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def api_refresh_recommendation(request):
    """Trigger LSTM training and prediction for a stock"""
    import json
    # Import locally to avoid crashing if ML libs are missing at startup
    try:
        from .ml_services import MLService, get_recommendation
    except ImportError as e:
         return JsonResponse({'success': False, 'message': f'ML Service unavailable: {str(e)}'})

    try:
        data = json.loads(request.body)
        symbol = data.get('symbol', '').strip().upper()
        if not symbol:
            return JsonResponse({'success': False, 'message': 'Symbol is required'})
            
        # 1. Fetch historical data (at least 60 days if possible)
        # We'll take last 100 entries to ensure we have enough for sliding window
        history_qs = NEPSEPrice.objects.filter(symbol=symbol).order_by('timestamp') # Sort Ascending for ML
        
        # Check if we have enough data (naive check first)
        if not history_qs.exists():
            return JsonResponse({'success': False, 'message': f'No data found for {symbol}.'})

        # Get last 150 days to be safe
        history_data = list(history_qs.values('timestamp', 'open', 'high', 'low', 'close', 'volume'))
        
        # If dataset is too large, take the tail. But we need sorted by date ASC
        if len(history_data) > 200:
             history_data = history_data[-200:]

        if len(history_data) < 40: # Minimum data check
            return JsonResponse({
                'success': False, 
                'message': f'Insufficient data for {symbol}. Need at least 40 trading days (have {len(history_data)}).'
            })

        # 2. Run ML Pipeline
        ml = MLService(history_data)
        predicted_price, rmse, mae, last_close = ml.train_and_predict(window_size=30)
        
        if predicted_price is None:
             return JsonResponse({'success': False, 'message': 'Model training failed (insufficient data after processing?).'})

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
                'predicted_price': sanitize_float(predicted_price),
                'recommendation': rec_obj.recommendation, # Return Integer
                'recommendation_str': rec_obj.get_recommendation_display(), # Return String Display
                'rmse': sanitize_float(rmse),
                'mae': sanitize_float(mae),
                'current_price': sanitize_float(last_close),
                'last_updated': rec_obj.last_updated.isoformat()
            }
        })
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
@login_required
@require_http_methods(["POST"])
def api_refresh_all_recommendations(request):
    """
    Batch trigger LSTM training and prediction for ALL stocks.
    Supports filter='all' to process entire market, or default to user's watchlist.
    """
    try:
        from .ml_services import MLService, get_recommendation
        import json
        
        # Check for filter param in JSON body
        body_data = {}
        try:
            body_data = json.loads(request.body)
        except:
            pass
            
        filter_type = body_data.get('filter', 'watchlist')
        
        if filter_type == 'all':
             # Process ALL stocks
             target_symbols = Stock.objects.values_list('symbol', flat=True).order_by('symbol')
             if not target_symbols:
                 # Fallback
                 target_symbols = NEPSEPrice.objects.values_list('symbol', flat=True).distinct().order_by('symbol')
        else:
            # 1. Get User's Watchlist
            target_symbols = Watchlist.objects.filter(user=request.user).values_list('symbol', flat=True)
            
            if not target_symbols:
                return JsonResponse({'success': True, 'data': [], 'message': 'Watchlist is empty.'})
            
        results = []
        errors = []
        
        # 2. Loop through each stock (Dynamic & Scalable)
        for symbol in target_symbols:
             try:
                # Fetch Data
                history_qs = NEPSEPrice.objects.filter(symbol=symbol).order_by('timestamp')
                history_data = list(history_qs.values('timestamp', 'open', 'high', 'low', 'close', 'volume'))
                
                # Optimization: Limit data size for performance while keeping enough for LSTM
                if len(history_data) > 200:
                     history_data = history_data[-200:]

                # Check minimum data requirement
                if len(history_data) < 40:
                    errors.append(f"{symbol}: Insufficient data ({len(history_data)} days)")
                    continue

                # Run ML Pipeline
                ml = MLService(history_data)
                predicted_price, rmse, mae, last_close = ml.train_and_predict(window_size=30)
                
                if predicted_price is None:
                    errors.append(f"{symbol}: Model training failed")
                    continue

                # Generate Signal
                rec_val = get_recommendation(last_close, predicted_price)
                
                # Save Result
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
                
                # Append to results
                results.append({
                    'symbol': symbol,
                    'current_price': sanitize_float(last_close),
                    'predicted_price': sanitize_float(predicted_price),
                    'recommendation': rec_obj.recommendation,
                    'recommendation_str': rec_obj.get_recommendation_display(),
                    'rmse': sanitize_float(rmse),
                    'mae': sanitize_float(mae),
                    'last_updated': rec_obj.last_updated.isoformat()
                })
                
             except Exception as inner_e:
                 errors.append(f"{symbol}: {str(inner_e)}")
                 continue

        # 3. Return Aggregated Results
        return JsonResponse({
            'success': True,
            'data': results,
            'processed_count': len(results),
            'errors': errors
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
