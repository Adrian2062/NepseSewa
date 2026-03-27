import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum, F, ExpressionWrapper, DecimalField
from django.utils import timezone
from datetime import timedelta
from myapp.models import (
    MarketSession, Order, TradeExecution, Stock, Sector, 
    NEPSEPrice, NEPSEIndex, StockRecommendation, CustomUser, Portfolio, 
    UserSubscription, PaymentTransaction, SubscriptionPlan, 
    Course, CandlestickLesson, CourseCategory
)
from django.apps import apps
from django.forms import modelform_factory
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q
from .models import ActivityLog, SystemSetting, Notification
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy

logger = logging.getLogger(__name__)

# --- DASHBOARD & GENERIC CRUD ENGINE ---

@staff_member_required(login_url='custom_admin:admin_login')
def admin_dashboard_view(request):
    """The main Home dashboard featuring KPIs and charts"""
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    last_week_start = today - timedelta(days=7)
    previous_week_start = today - timedelta(days=14)

    # Revenue
    revenue = PaymentTransaction.objects.filter(status='COMPLETED').aggregate(total=Sum('amount'))['total'] or 0
    # Revenue Growth calculation
    this_week_revenue = PaymentTransaction.objects.filter(
        status='COMPLETED', 
        created_at__date__gte=last_week_start
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    last_week_revenue = PaymentTransaction.objects.filter(
        status='COMPLETED', 
        created_at__date__gte=previous_week_start,
        created_at__date__lt=last_week_start
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    if last_week_revenue > 0:
        revenue_growth = ((this_week_revenue - last_week_revenue) / last_week_revenue) * 100
    else:
        revenue_growth = 100 if this_week_revenue > 0 else 0

    # Users
    total_users = CustomUser.objects.count()
    new_users_today = CustomUser.objects.filter(date_joined__date=today).count()
    
    # Orders
    pending_orders = Order.objects.filter(status__in=['OPEN', 'PARTIAL']).count()
    
    # AI Signals
    ai_signals = StockRecommendation.objects.count()

    # Premium Users
    active_premium_users = UserSubscription.objects.filter(is_active=True).count()
    
    # Trades
    total_trades = TradeExecution.objects.count()
    trades_today = TradeExecution.objects.filter(executed_at__date=today).count()
    
    # Stocks
    total_stocks = Stock.objects.count()
    
    # Market Status Logic
    # 1. Try to find the session for today first
    today = timezone.now().date()
    latest_session = MarketSession.objects.filter(session_date=today).first()
    
    # 2. If not for today, find the one marked as active
    if not latest_session:
        latest_session = MarketSession.objects.filter(is_active=True).first()
        
    # 3. Fallback to the latest overall by date
    if not latest_session:
        latest_session = MarketSession.objects.order_by('-session_date').first()

    # Map status to 'OPEN' for any active phase, otherwise 'CLOSED'
    if latest_session and latest_session.status in ['CONTINUOUS', 'PRE_OPEN']:
        market_status = 'OPEN'
    else:
        market_status = 'CLOSED'
    
    # Chart data - Dynamic (Last 5 days)
    last_5_days = [timezone.now().date() - timedelta(days=i) for i in range(4, -1, -1)]
    
    # 1. Weekly Traded Volume
    volume_labels = [d.strftime('%a') for d in last_5_days]
    volume_data = []
    for day in last_5_days:
        day_volume = TradeExecution.objects.filter(
            executed_at__date=day
        ).aggregate(total=Sum('executed_qty'))['total'] or 0
        volume_data.append(int(day_volume))
    
    # 2. Market Trends (NEPSE Index)
    trend_labels = [d.strftime('%a') for d in last_5_days]
    trend_data = []
    for day in last_5_days:
        idx = NEPSEIndex.objects.filter(timestamp__date=day).order_by('-timestamp').first()
        trend_data.append(idx.index_value if idx else 0)

    # Recent lists for widgets
    recent_trades = TradeExecution.objects.select_related('buy_order__user').order_by('-executed_at')[:5]
    recent_users = CustomUser.objects.order_by('-date_joined')[:5]
    recent_payments = PaymentTransaction.objects.select_related('user', 'plan').order_by('-created_at')[:5]

    # System Controls Status (Check SystemSetting for 'scraper_running' and 'recommendation_running')
    scraper_status = SystemSetting.objects.filter(key='scraper_running').first()
    scraper_running = (scraper_status.value.lower() == 'true') if scraper_status else False
    
    rec_status = SystemSetting.objects.filter(key='recommendation_running').first()
    rec_running = (rec_status.value.lower() == 'true') if rec_status else False

    # Notifications (Example: count of failed payments or pending orders)
    unread_notifications_count = pending_orders

    context = {
        'page_title': 'Dashboard Overview',
        'revenue': revenue,
        'revenue_growth': revenue_growth,
        'total_users': total_users,
        'new_users_today': new_users_today,
        'pending_orders': pending_orders,
        'ai_signals': ai_signals,
        'active_premium_users': active_premium_users,
        'total_trades': total_trades,
        'trades_today': trades_today,
        'total_stocks': total_stocks,
        'market_status': market_status,
        'recent_trades': recent_trades,
        'recent_users': recent_users,
        'recent_payments': recent_payments,
        'volume_labels': volume_labels,
        'volume_data': volume_data,
        'trend_labels': trend_labels,
        'trend_data': trend_data,
        'unread_notifications_count': unread_notifications_count,
        'scraper_running': scraper_running,
        'recommendation_running': rec_running,
    }
    return render(request, 'custom_admin/panel_dashboard.html', context)


@staff_member_required(login_url='custom_admin:admin_login')
def toggle_system_process(request, process_name):
    """Toggle system processes like scraper or recommendation engine"""
    if process_name not in ['scraper', 'recommendation']:
        messages.error(request, "Invalid process name.")
        return redirect('custom_admin:admin_trading_dashboard')
    
    key = f"{process_name}_running"
    setting, created = SystemSetting.objects.get_or_create(
        key=key,
        defaults={'value': 'false', 'description': f"Is the {process_name} process currently enabled?"}
    )
    
    # Toggle logic
    new_status = 'true' if setting.value.lower() == 'false' else 'false'
    setting.value = new_status
    setting.save()
    
    logger.info(f"Toggling process: {process_name} to {new_status}")

    # Trigger Task immediately if started
    if new_status == 'true':
        try:
            if process_name == 'scraper':
                from myapp.tasks import scrape_market_data
                scrape_market_data.delay()
            elif process_name == 'recommendation':
                from myapp.tasks import generate_watchlist_recommendations
                generate_watchlist_recommendations.delay()
        except Exception as e:
            logger.error(f"Failed to trigger {process_name} task: {str(e)}")
            messages.warning(request, f"Status updated to '{new_status}', but {process_name} task failed to start (Broker error). Check Redis/Celery.")

    action_verb = "Started" if new_status == 'true' else "Stopped"
    messages.success(request, f"{process_name.capitalize()} process has been {action_verb.lower()}.")

    # Log the action
    ActivityLog.objects.create(
        user=request.user,
        action=f"{action_verb} {process_name} process",
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    return redirect('custom_admin:admin_trading_dashboard')


@staff_member_required(login_url='custom_admin:admin_login')
def admin_search_view(request):
    """Global search across Users, Stocks, and Orders"""
    query = request.GET.get('q', '').strip()
    if not query:
        return redirect('custom_admin:admin_trading_dashboard')
    
    user_results = CustomUser.objects.filter(
        Q(username__icontains=query) | Q(email__icontains=query)
    )[:10]
    
    stock_results = Stock.objects.filter(
        Q(symbol__icontains=query) | Q(company_name__icontains=query)
    )[:10]
    
    order_results = Order.objects.filter(
        Q(symbol__icontains=query) | Q(user__username__icontains=query)
    ).order_by('-created_at')[:10]
    
    context = {
        'page_title': f"Search Results for '{query}'",
        'query': query,
        'user_results': user_results,
        'stock_results': stock_results,
        'order_results': order_results,
        'total_results': user_results.count() + stock_results.count() + order_results.count()
    }
    return render(request, 'custom_admin/search_results.html', context)


def get_model_or_404(app_name, model_name):
    try:
        return apps.get_model(app_label=app_name, model_name=model_name)
    except LookupError:
        from django.http import Http404
        raise Http404(f"Model {model_name} not found in app {app_name}")


@staff_member_required(login_url='custom_admin:admin_login')
def generic_list_view(request, app_name, model_name):
    from .filters import get_filter_config
    model = get_model_or_404(app_name, model_name)
    query = request.GET.get('q', '')
    sort_by = request.GET.get('sort', '-id') # Default sort by ID descending
    
    queryset = model.objects.all()
    
    # 1. Global Search
    if query:
        q_objects = Q()
        for field in model._meta.fields:
            if field.get_internal_type() in ['CharField', 'TextField']:
                kwarg = {f"{field.name}__icontains": query}
                q_objects |= Q(**kwarg)
        queryset = queryset.filter(q_objects)
    
    # 2. Advanced Filters
    filters_config = get_filter_config(model_name)
    for cfg in filters_config:
        val = request.GET.get(cfg['name'])
        if val:
            queryset = cfg['query'](queryset, val)
            
    # 3. Sorting
    if sort_by:
        field_name = sort_by[1:] if sort_by.startswith('-') else sort_by
        # Validate field exists
        if any(f.name == field_name for f in model._meta.fields):
            queryset = queryset.order_by(sort_by)
        
    paginator = Paginator(queryset, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Exclude complex fields like password for list display
    display_fields = [f.name for f in model._meta.fields if f.name not in ['password']]
    
    context = {
        'page_title': f"Manage {model._meta.verbose_name_plural.title()}",
        'app_name': app_name,
        'model_name': model_name,
        'objects': page_obj,
        'fields': display_fields,
        'headers': display_fields,
        'filters_config': filters_config,
        'active_filters': request.GET,
        'current_sort': sort_by,
    }
    return render(request, 'custom_admin/generic_list.html', context)


@staff_member_required(login_url='custom_admin:admin_login')
def generic_create_view(request, app_name, model_name):
    model = get_model_or_404(app_name, model_name)
    ModelFormClass = modelform_factory(model, exclude=['created_at', 'updated_at', 'date_joined'])
    
    if request.method == 'POST':
        form = ModelFormClass(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, f"{model._meta.verbose_name.title()} created successfully.")
            return redirect('custom_admin:generic_list', app_name=app_name, model_name=model_name)
    else:
        form = ModelFormClass()
        
    context = {
        'page_title': f"Create {model._meta.verbose_name.title()}",
        'form': form,
        'app_name': app_name,
        'model_name': model_name,
    }
    return render(request, 'custom_admin/generic_form.html', context)


@staff_member_required(login_url='custom_admin:admin_login')
def generic_edit_view(request, app_name, model_name, obj_id):
    model = get_model_or_404(app_name, model_name)
    obj = get_object_or_404(model, pk=obj_id)
    ModelFormClass = modelform_factory(model, exclude=['created_at', 'updated_at', 'date_joined'])
    
    if request.method == 'POST':
        form = ModelFormClass(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, f"{model._meta.verbose_name.title()} updated successfully.")
            return redirect('custom_admin:generic_list', app_name=app_name, model_name=model_name)
    else:
        form = ModelFormClass(instance=obj)
        
    context = {
        'page_title': f"Edit {model._meta.verbose_name.title()}",
        'form': form,
        'app_name': app_name,
        'model_name': model_name,
    }
    return render(request, 'custom_admin/generic_form.html', context)


@staff_member_required(login_url='custom_admin:admin_login')
def generic_delete_view(request, app_name, model_name, obj_id):
    model = get_model_or_404(app_name, model_name)
    obj = get_object_or_404(model, pk=obj_id)
    
    obj.delete()
    messages.success(request, f"{model._meta.verbose_name.title()} deleted successfully.")
    return redirect('custom_admin:generic_list', app_name=app_name, model_name=model_name)

# --- AUTHENTICATION ---

def admin_login_view(request):
    """Dedicated login for Custom Admin ERP"""
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('custom_admin:admin_trading_dashboard')
        
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('custom_admin:admin_trading_dashboard')
        else:
            messages.error(request, "Invalid admin credentials or unauthorized access.")
            
    return render(request, 'custom_admin/login.html', {'page_title': 'Admin Login'})

def admin_logout_view(request):
    """Logout and redirect to admin login"""
    logout(request)
    messages.info(request, "Successfully logged out of the admin panel.")
    return redirect('custom_admin:admin_login')
# --- API ENDPOINTS FOR AJAX (NOTIFICATIONS & SEARCH) ---

def api_get_notifications(request):
    """Fetch latest notifications for polling"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
        
    # Fetch notifications specifically for the user OR global notifications (user is NULL)
    notifications = Notification.objects.filter(
        Q(user=request.user) | Q(user__isnull=True)
    ).order_by('-created_at')[:10]
    
    unread_count = Notification.objects.filter(
        Q(user=request.user) | Q(user__isnull=True), 
        is_read=False
    ).count()
    
    data =[{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'type': n.type, # Make sure 'type' was added to your Notification model!
        'is_read': n.is_read,
        'time': n.created_at.strftime('%b %d, %H:%M')
    } for n in notifications]
    
    return JsonResponse({'notifications': data, 'unread_count': unread_count})


@require_POST
def api_mark_notification_read(request, notif_id):
    """Mark a specific notification as read (Handles User and Global)"""
    if request.user.is_authenticated:
        # Filter by ID AND (User is current user OR notification is global)
        Notification.objects.filter(
            id=notif_id
        ).filter(
            Q(user=request.user) | Q(user__isnull=True)
        ).update(is_read=True)
        
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Unauthorized'}, status=401)


def api_live_search(request):
    """AJAX endpoint for searching stocks AND users dynamically"""
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})
        
    results =[]
    
    # 1. Search Stocks
    stocks = Stock.objects.filter(
        Q(symbol__icontains=query) | Q(company_name__icontains=query)
    ).order_by('symbol')[:4]
    
    for s in stocks:
        results.append({
            'title': s.symbol,
            'subtitle': s.company_name,
            'icon': 'bx-buildings' # Building icon for stocks
        })
    
    # 2. Search Users
    users = CustomUser.objects.filter(
        Q(username__icontains=query) | Q(email__icontains=query)
    ).order_by('username')[:4]
    
    for u in users:
        results.append({
            'title': u.username,
            'subtitle': u.email,
            'icon': 'bx-user' # User icon for accounts
        })
        
    return JsonResponse({'results': results})
@staff_member_required(login_url='custom_admin:admin_login')
def admin_profile_view(request):
    context = {
        'page_title': 'Admin Profile',
        'user': request.user,
    }
    return render(request, 'custom_admin/admin_profile.html', context)
class AdminPasswordChangeView(PasswordChangeView):
    template_name = 'custom_admin/password_change.html'
    success_url = reverse_lazy('custom_admin:admin_profile')

    def form_valid(self, form):
        messages.success(self.request, "Your password has been updated successfully!")
        return super().form_valid(form)