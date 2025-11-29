from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('login/', views.login_view, name='login'),
    path('home/', views.home_view, name='home'),  # Add this
    path('dashboard/', views.home_view, name='dashboard'),  # Keep this too
    path('logout/', views.logout_view, name='logout'),
    path('portfolio/', views.home_view, name='portfolio'),
    path('trade/', views.home_view, name='trade'),
    path('market/', views.home_view, name='market'),
    path('watchlist/', views.home_view, name='watchlist'),
    path('learn/', views.home_view, name='learn'),
    path('settings/', views.home_view, name='settings'),
    path('password-reset/', views.home_view, name='password_reset'),
]