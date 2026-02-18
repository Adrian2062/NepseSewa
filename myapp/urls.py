
from django.urls import path
from . import views
from . import trading_api
from . import admin_views
from django.contrib.auth import views as auth_views
from .forms import CustomPasswordResetForm

urlpatterns = [
    # Page views
    path('', views.landing_page, name='landing'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('portfolio/', views.portfolio, name='portfolio'),
    path('trade/', views.trade, name='trade'),
    path('market/', views.market, name='market'),
    path('watchlist/', views.watchlist, name='watchlist'),
    path('learn/', views.learn, name='learn'),
    path('learn/course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('learn/lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('settings/', views.settings_view, name='settings'),
    path('logout/', views.logout_view, name='logout'),
    path('stocks/', views.stocks, name='stocks'),

    # Original NEPSE API Endpoints
    path('api/latest/', views.api_latest_nepse, name='api_latest'),
    path('api/gainers/', views.api_top_gainers, name='api_gainers'),
    path('api/losers/', views.api_top_losers, name='api_losers'),
    path('api/stats/', views.api_market_stats, name='api_stats'),
    path('api/history/', views.api_symbol_history, name='api_history'),
    path('api/search/', views.api_search_symbol, name='api_search'),
    path('api/nepse-index/', views.api_nepse_index, name='api_nepse_index'),
    path('api/market-summary/', views.api_market_summary, name='api_market_summary'),
    path('api/sector-indices/', views.api_sector_indices, name='api_sector_indices'),
    
    # Date-filtered API Endpoints
    path('api/market-data/', views.api_market_data_by_date, name='api_market_data_by_date'),
    path('api/sectors/', views.api_sectors, name='api_sectors'),
    path('api/available-dates/', views.api_available_dates, name='api_available_dates'),
    path('api/stock-history/<str:symbol>/', views.api_stock_history_range, name='api_stock_history_range'),
    path('api/date-range-summary/', views.api_date_range_summary, name='api_date_range_summary'),
    
    # Legacy trade endpoints
    path('api/trade/history/', views.api_trade_history, name='api_trade_history'),
    path('api/trade/place/', views.api_place_order, name='api_place_order_legacy'),
    
    # New Trading Engine API Endpoints
    path('api/orderbook/<str:symbol>/', trading_api.api_orderbook, name='api_orderbook'),
    path('api/market/session/', trading_api.api_market_session, name='api_market_session'),
    path('api/trade/orders/', trading_api.api_user_orders, name='api_user_orders'),
    path('api/trade/cancel/<int:order_id>/', trading_api.api_cancel_order, name='api_cancel_order'),
    path('api/trade/place-new/', trading_api.api_place_order_new, name='api_place_order_new'),
    path('api/trade/executions/', trading_api.api_trade_executions, name='api_trade_executions'),

    # Admin Dashboard & Operations
    path('admin/trading/dashboard/', admin_views.trading_dashboard, name='admin_trading_dashboard'),
    path('admin/trading/pause/', admin_views.pause_market_view, name='admin_pause_market'),
    path('admin/trading/resume/', admin_views.resume_market_view, name='admin_resume_market'),
    path('admin/scraper/run/', admin_views.run_scraper_view, name='admin_run_scraper'),
    path('admin/recommendations/run/', admin_views.run_recommendations_view, name='admin_run_recommendations'),
    path('admin/recommendations/watchlist/', admin_views.run_watchlist_recommendations_view, name='admin_run_watchlist_recommendations'),
    path('admin/trading/reset-control/', admin_views.reset_market_control_view, name='admin_reset_market_control'),
    path('admin/trading/close/', admin_views.close_market_view, name='admin_close_market'),

    # Watchlist & Recommendation APIs
    path('api/watchlist/', views.api_get_watchlist, name='api_get_watchlist'),
    path('api/watchlist/toggle/', views.api_toggle_watchlist, name='api_toggle_watchlist'),
    path('api/recommendations/', views.api_get_recommendations, name='api_get_recommendations'),
    path('api/recommendations/refresh/', views.api_refresh_recommendation, name='api_refresh_recommendation'),
    path('api/recommendations/refresh-all/', views.api_refresh_all_recommendations, name='api_refresh_all_recommendations'),
    
    # Manual Payment
    path('pricing/', views.pricing, name='pricing'),
    path('subscribe/<int:plan_id>/', views.join_plan, name='subscribe'),
    path('payment/manual-submit/', views.manual_payment_submit, name='manual_payment_submit'),
    path('api/payment-status/', views.api_check_payment_status, name='api_payment_status'),

    # Portfolio Analytics APIs
    path('api/portfolio/analytics/', views.api_portfolio_analytics, name='api_portfolio_analytics'),
    path('api/portfolio/holdings/', views.api_portfolio_holdings, name='api_portfolio_holdings'),
    path('api/portfolio/performance/', views.api_portfolio_performance, name='api_portfolio_performance'),
    path('api/portfolio/activity/', views.api_portfolio_activity, name='api_portfolio_activity'),
    path('api/dashboard/summary/', views.api_dashboard_summary, name='api_dashboard_summary'),
    path('api/nepse-index/performance/', views.api_nepse_index_performance, name='api_nepse_index_performance'),
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            form_class=CustomPasswordResetForm,
            template_name='registration/password_reset_form.html',
            email_template_name='registration/password_reset_email.html',
            subject_template_name='registration/password_reset_subject.txt',
            success_url='/password-reset/done/',
        ),
        name='password_reset'
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='registration/password_reset_done.html'
        ),
        name='password_reset_done'
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/password_reset_confirm.html',
            success_url='/reset/done/'
        ),
        name='password_reset_confirm'
    ),
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
]