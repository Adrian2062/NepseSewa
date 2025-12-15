from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('portfolio/', views.portfolio, name='portfolio'),
    path('trade/', views.trade, name='trade'),
    path('market/', views.market, name='market'),
    path('watchlist/', views.watchlist, name='watchlist'),
    path('learn/', views.learn, name='learn'),
    path('settings/', views.settings_view, name='settings'),
    path('logout/', views.logout_view, name='logout'),

    # NEPSE API Endpoints
    path('api/latest/', views.api_latest_nepse, name='api_latest'),
    path('api/gainers/', views.api_top_gainers, name='api_gainers'),
    path('api/losers/', views.api_top_losers, name='api_losers'),
    path('api/stats/', views.api_market_stats, name='api_stats'),
    path('api/history/', views.api_symbol_history, name='api_history'),
    path('api/search/', views.api_search_symbol, name='api_search'),
]