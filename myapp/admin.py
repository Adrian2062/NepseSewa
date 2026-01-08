from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, NEPSEPrice, NEPSEIndex, MarketIndex, 
    MarketSummary, Trade, Order, Portfolio, TradeExecution, MarketSession,
    Stock, CandlestickLesson, LessonQuiz, UserLessonProgress,
    Course, CourseCategory, UserCourseProgress
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
