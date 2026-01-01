from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, NEPSEPrice, NEPSEIndex, MarketIndex, 
    MarketSummary, Trade, Order, Portfolio, TradeExecution, MarketSession
)

# Register models
admin.site.register(CustomUser)
admin.site.register(NEPSEPrice)
admin.site.register(NEPSEIndex)
admin.site.register(MarketIndex)
admin.site.register(MarketSummary)
admin.site.register(Trade)


# Trading Engine Models
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'symbol', 'side', 'qty', 'filled_qty', 'price', 'status', 'created_at']
    list_filter = ['status', 'side', 'symbol', 'created_at']
    search_fields = ['symbol', 'user__email']
    ordering = ['-created_at']


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ['user', 'symbol', 'quantity', 'avg_price', 'updated_at']
    list_filter = ['symbol', 'updated_at']
    search_fields = ['user__email', 'symbol']


@admin.register(TradeExecution)
class TradeExecutionAdmin(admin.ModelAdmin):
    list_display = ['id', 'symbol', 'executed_qty', 'executed_price', 'executed_at']
    list_filter = ['symbol', 'executed_at']
    search_fields = ['symbol']
    ordering = ['-executed_at']


@admin.register(MarketSession)
class MarketSessionAdmin(admin.ModelAdmin):
    list_display = ['session_date', 'status', 'is_active', 'opened_at', 'closed_at']
    list_filter = ['status', 'is_active', 'session_date']
    ordering = ['-session_date']