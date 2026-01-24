from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, NEPSEPrice, NEPSEIndex, MarketIndex, 
    MarketSummary, Trade, Order, Portfolio, TradeExecution, MarketSession,
    Stock, CandlestickLesson, LessonQuiz, UserLessonProgress,
    Course, CourseCategory, UserCourseProgress,
    SubscriptionPlan, UserSubscription, PaymentTransaction
)

# Register models
admin.site.register(CustomUser)
admin.site.register(NEPSEPrice)
admin.site.register(NEPSEIndex)
admin.site.register(MarketIndex)
admin.site.register(MarketSummary)
admin.site.register(Trade)
admin.site.register(CourseCategory)


# Trading Engine Models
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'symbol', 'side', 'qty', 'filled_qty', 'price', 'status', 'created_at']
    list_filter = ['status', 'side', 'symbol', 'created_at']
    search_fields = ['symbol', 'user__email']
    ordering = ['-created_at']

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'sector', 'is_active', 'updated_at')
    search_fields = ('symbol', 'name', 'sector')
    list_filter = ('sector', 'is_active')

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


# ============= CUSTOM ADMIN REORDERING =============

class LessonInline(admin.StackedInline):
    model = CandlestickLesson
    extra = 1

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'difficulty', 'is_featured', 'created_at')
    list_filter = ('category', 'difficulty', 'is_featured')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [LessonInline]

class QuizInline(admin.StackedInline):
    model = LessonQuiz
    extra = 1

@admin.register(CandlestickLesson)
class CandlestickLessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'created_at')
    list_filter = ('course',)
    search_fields = ('title', 'description', 'course__title')
    inlines = [QuizInline]
    ordering = ('course', 'order',)

@admin.register(UserLessonProgress)
class UserLessonProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'is_completed', 'completed_at')
    list_filter = ('is_completed',)
    search_fields = ('user__email', 'lesson__title')

@admin.register(UserCourseProgress)
class UserCourseProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'progress_percent', 'is_completed', 'last_accessed')
    list_filter = ('is_completed', 'course')
    search_fields = ('user__email', 'course__title')


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'tier', 'duration_days', 'is_active', 'created_at')
    list_editable = ('price', 'tier', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'plan', 'start_date', 'end_date')
    search_fields = ('user__email', 'plan__name')


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'plan', 'transaction_id', 'amount', 'status', 'view_receipt', 'created_at')
    list_filter = ('status', 'gateway', 'created_at')
    search_fields = ('user__email', 'transaction_id')
    readonly_fields = ('created_at', 'updated_at', 'thumbnail')
    
    fieldsets = (
        ('Transaction Info', {
            'fields': ('user', 'plan', 'transaction_id', 'amount', 'status', 'gateway')
        }),
        ('Verification Proof', {
            'fields': ('verification_image', 'thumbnail')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def view_receipt(self, obj):
        if obj.verification_image:
            from django.utils.html import format_html
            return format_html('<a href="{}" target="_blank">View Receipt</a>', obj.verification_image.url)
        return "No Receipt"
    
    def thumbnail(self, obj):
        if obj.verification_image:
            from django.utils.html import format_html
            return format_html('<img src="{}" style="max-height: 200px;"/>', obj.verification_image.url)
        return "No Proof Uploaded"
    
    view_receipt.short_description = 'Proof Link'
    thumbnail.short_description = 'Receipt Preview'
