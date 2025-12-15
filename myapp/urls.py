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


    # path('api/nepse/summary/', views.get_market_summary, name='nepse_summary'),
    # path('api/nepse/top-gainers/', views.get_top_gainers, name='nepse_top_gainers'),
    # path('api/nepse/top-losers/', views.get_top_losers, name='nepse_top_losers'),
    # path('api/nepse/top-volume/', views.get_top_volume_stocks, name='nepse_top_volume'),
    # path('api/nepse/top-turnover/', views.get_top_turnover_stocks, name='nepse_top_turnover'),
    # path('api/nepse/market-overview/', views.get_market_overview, name='nepse_market_overview'),
    # path('api/nepse/security-info/', views.get_security_wise_info, name='nepse_security_info'),
    # path('api/nepse/sector-info/', views.get_sector_wise_info, name='nepse_sector_info'),
    # path('api/nepse/nepse-index/', views.get_nepse_index, name='nepse_index'),
    # path('api/nepse/dashboard/', views.get_dashboard_data, name='nepse_dashboard'),
    path('api/nepse/latest/', views.get_nepse_latest, name='nepse_latest'),
    path('api/nepse/history/', views.get_nepse_history, name='nepse_history'),
    path('api/nepse/top-gainers/', views.get_top_gainers_nepse, name='nepse_gainers'),
    path('api/nepse/top-losers/', views.get_top_losers_nepse, name='nepse_losers'),
]
# urls.py - Add these URLs to your myapp/urls.py or main urls.py

