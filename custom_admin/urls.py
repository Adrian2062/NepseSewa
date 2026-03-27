from django.urls import path
from . import views

app_name = 'custom_admin'

urlpatterns =[
    # Dashboard & Custom Logic
    path('dashboard/', views.admin_dashboard_view, name='admin_trading_dashboard'),
    
    # Authentication & Old Search Page
    path('search/', views.admin_search_view, name='admin_search'),
    path('login/', views.admin_login_view, name='admin_login'),
    path('logout/', views.admin_logout_view, name='admin_logout'),
    path('profile/', views.admin_profile_view, name='admin_profile'),
    path('profile/password/', views.AdminPasswordChangeView.as_view(), name='password_change'),

    # System Controls
    path('system/toggle/<str:process_name>/', views.toggle_system_process, name='toggle_process'),

    # --- API ENDPOINTS FOR AJAX (Must be ABOVE the Generic CRUD Engine) ---
    path('api/notifications/', views.api_get_notifications, name='api_notifications'),
    path('api/notifications/read/<int:notif_id>/', views.api_mark_notification_read, name='api_mark_read'),
    path('api/search/', views.api_live_search, name='api_live_search'),

    # --- GENERIC CRUD ENGINE ---
    # (These act as wildcards, so they must be at the very bottom)
    path('<str:app_name>/<str:model_name>/', views.generic_list_view, name='generic_list'),
    path('<str:app_name>/<str:model_name>/add/', views.generic_create_view, name='generic_create'),
    path('<str:app_name>/<str:model_name>/<int:obj_id>/edit/', views.generic_edit_view, name='generic_edit'),
    path('<str:app_name>/<str:model_name>/<int:obj_id>/delete/', views.generic_delete_view, name='generic_delete'),
]