from django.urls import path
from . import views

app_name = 'custom_admin'

urlpatterns = [
    # Dashboard & Custom Logic
    path('dashboard/', views.admin_dashboard_view, name='admin_trading_dashboard'),
    
    # Generic CRUD Engine
    path('<str:app_name>/<str:model_name>/', views.generic_list_view, name='generic_list'),
    path('<str:app_name>/<str:model_name>/add/', views.generic_create_view, name='generic_create'),
    path('<str:app_name>/<str:model_name>/<int:obj_id>/edit/', views.generic_edit_view, name='generic_edit'),
    path('<str:app_name>/<str:model_name>/<int:obj_id>/delete/', views.generic_delete_view, name='generic_delete'),
    
    # System Controls
    path('system/toggle/<str:process_name>/', views.toggle_system_process, name='toggle_process'),

    # Authentication
    path('search/', views.admin_search_view, name='admin_search'),
    path('login/', views.admin_login_view, name='admin_login'),
    path('logout/', views.admin_logout_view, name='admin_logout'),
]
