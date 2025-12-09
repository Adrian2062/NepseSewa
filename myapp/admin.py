from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

# @admin.register(CustomUser)
# class CustomUserAdmin(UserAdmin):
#     list_display = ['email', 'first_name', 'last_name', 'virtual_balance', 'portfolio_value', 'date_joined']
#     list_filter = ['date_joined', 'is_staff', 'is_active']
#     search_fields = ['email', 'first_name', 'last_name']
#     ordering = ['-date_joined']
    
#     fieldsets = UserAdmin.fieldsets + (
#         ('Additional Info', {'fields': ('virtual_balance', 'portfolio_value')}),
#     )