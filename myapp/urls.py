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
]
