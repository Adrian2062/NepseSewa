from django.urls import path, include
from myapp import views  # import views from your app

urlpatterns = [
    path('', views.index, name='landing'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('portfolio/', views.portfolio, name='portfolio'),
    path('trade/', views.trade, name='trade'),
    path('market/', views.market, name='market'),
    path('watchlist/', views.watchlist, name='watchlist'),
    path('learn/', views.learn, name='learn'),
    path('settings/', views.settings, name='settings'),
    path('password-reset/', views.password_reset, name='password_reset'),  # ✅ Add this
]

