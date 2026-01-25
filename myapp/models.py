from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.conf import settings

# ============= CUSTOM USER MODEL =============
class CustomUser(AbstractUser):
    """Extended user model with additional fields"""
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    virtual_balance = models.DecimalField(max_digits=12, decimal_places=2, default=100000.00)
    portfolio_value = models.DecimalField(max_digits=12, decimal_places=2, default=100000.00)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    # Settings fields
    phone = models.CharField(max_length=15, blank=True, null=True)
    buy_sell_notifications = models.BooleanField(default=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        db_table = 'users'
    

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# ============= STOCK METADATA (NEW) =============
class Stock(models.Model):
    """Store static stock details (Symbol, Name, Sector)"""
    symbol = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    sector = models.CharField(max_length=100, db_index=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'stocks'
        ordering = ['symbol']
        indexes = [
            models.Index(fields=['sector', 'symbol']),
        ]

    def __str__(self):
        return f"{self.symbol} ({self.sector})"


# ============= NEPSE STOCK PRICES =============
class NEPSEPrice(models.Model):
    """Store NEPSE stock prices"""
    symbol = models.CharField(max_length=50, db_index=True)
    timestamp = models.DateTimeField(db_index=True)
    open = models.FloatField(null=True, blank=True)
    high = models.FloatField(null=True, blank=True)
    low = models.FloatField(null=True, blank=True)
    close = models.FloatField(null=True, blank=True)
    ltp = models.FloatField(null=True, blank=True)
    change_pct = models.FloatField(null=True, blank=True)
    volume = models.FloatField(null=True, blank=True)
    turnover = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'nepse_prices'
        ordering = ['-timestamp', 'symbol']
        indexes = [
            models.Index(fields=['symbol', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.symbol} - {self.ltp} ({self.change_pct}%)"


# ============= NEPSE INDEX (MAIN INDEX) =============
class NEPSEIndex(models.Model):
    """Store NEPSE Index data"""
    timestamp = models.DateTimeField(db_index=True, unique=True)
    index_value = models.FloatField()
    percentage_change = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'nepse_index'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"NEPSE Index - {self.index_value} ({self.percentage_change}%)"


# ============= MARKET INDICES (ALL INDICES) =============
class MarketIndex(models.Model):
    """Store all market indices (NEPSE, Sensitive, Float, Sector Indices, etc.)"""
    INDEX_CHOICES = [
        ('NEPSE Index', 'NEPSE Index'),
        ('Sensitive Index', 'Sensitive Index'),
        ('Float Index', 'Float Index'),
        ('Sensitive Float Index', 'Sensitive Float Index'),
        ('Banking SubIndex', 'Banking SubIndex'),
        ('Development Bank', 'Development Bank'),
        ('Finance Index', 'Finance Index'),
        ('Hotels And Tourism', 'Hotels And Tourism'),
        ('Hydropower Index', 'Hydropower Index'),
        ('Insurance Index', 'Insurance Index'),
        ('Life Insurance', 'Life Insurance'),
        ('Non Life Insurance', 'Non Life Insurance'),
        ('Investment', 'Investment'),
        ('Manufacturing And Processing', 'Manufacturing And Processing'),
    ]
    
    index_name = models.CharField(max_length=100, choices=INDEX_CHOICES, db_index=True)
    value = models.FloatField()
    change_pct = models.FloatField(default=0)
    timestamp = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'market_indices'
        ordering = ['-timestamp', 'index_name']
        indexes = [
            models.Index(fields=['index_name', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]
        unique_together = [['index_name', 'timestamp']]
    
    def __str__(self):
        return f"{self.index_name}: {self.value} ({self.change_pct:+.2f}%)"


# ============= MARKET SUMMARY =============
class MarketSummary(models.Model):
    """Store overall market summary data"""
    total_turnover = models.FloatField(null=True, blank=True)
    total_traded_shares = models.FloatField(null=True, blank=True)
    total_transactions = models.FloatField(null=True, blank=True)
    total_scrips = models.FloatField(null=True, blank=True)
    market_cap = models.FloatField(null=True, blank=True)
    float_market_cap = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField(db_index=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'market_summary'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Market Summary - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    
    def format_turnover(self):
        """Format turnover with comma separators"""
        if self.total_turnover:
            return f"Rs {self.total_turnover:,.2f}"
        return "N/A"
    
    def format_shares(self):
        """Format traded shares with comma separators"""
        if self.total_traded_shares:
            return f"{self.total_traded_shares:,.0f}"
        return "N/A"

# ============= ORDER MODEL (PENDING/OPEN ORDERS) =============
class Order(models.Model):
    """Represents a pending or partially filled order"""
    SIDE_CHOICES = [
        ('BUY', 'BUY'),
        ('SELL', 'SELL'),
    ]

    STATUS_CHOICES = [
        ('OPEN', 'OPEN'),           # Not filled at all
        ('PARTIAL', 'PARTIAL'),     # Partially filled
        ('FILLED', 'FILLED'),       # Completely filled
        ('CANCELLED', 'CANCELLED'), # Cancelled by user
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    symbol = models.CharField(max_length=50, db_index=True)
    side = models.CharField(max_length=4, choices=SIDE_CHOICES, db_index=True)
    qty = models.PositiveIntegerField()
    filled_qty = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=12, decimal_places=2)  # Limit price
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='OPEN', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'orders'
        ordering = ['created_at']  # Time priority (oldest first)
        indexes = [
            models.Index(fields=['symbol', 'side', 'status', 'created_at']),
            models.Index(fields=['user', 'status', '-created_at']),
            models.Index(fields=['symbol', 'status']),
        ]

    def __str__(self):
        return f"{self.user.email} {self.side} {self.symbol} {self.filled_qty}/{self.qty} @ {self.price}"

    @property
    def remaining_qty(self):
        """Calculate remaining quantity to be filled"""
        return self.qty - self.filled_qty

    @property
    def is_fully_filled(self):
        """Check if order is completely filled"""
        return self.filled_qty >= self.qty


# ============= PORTFOLIO MODEL (USER HOLDINGS) =============
class Portfolio(models.Model):
    """Track user's stock holdings"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='portfolio'
    )
    symbol = models.CharField(max_length=50, db_index=True)
    quantity = models.PositiveIntegerField(default=0)
    avg_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'portfolio'
        unique_together = [['user', 'symbol']]
        indexes = [
            models.Index(fields=['user', 'symbol']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.symbol}: {self.quantity} @ {self.avg_price}"


# ============= TRADE EXECUTION MODEL (COMPLETED TRADES) =============
class TradeExecution(models.Model):
    """Log of executed trades (matches between buy and sell orders)"""
    buy_order = models.ForeignKey(
        'Order',
        on_delete=models.CASCADE,
        related_name='buy_executions'
    )
    sell_order = models.ForeignKey(
        'Order',
        on_delete=models.CASCADE,
        related_name='sell_executions'
    )
    symbol = models.CharField(max_length=50, db_index=True)
    executed_qty = models.PositiveIntegerField()
    executed_price = models.DecimalField(max_digits=12, decimal_places=2)
    executed_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'trade_executions'
        ordering = ['-executed_at']
        indexes = [
            models.Index(fields=['symbol', '-executed_at']),
            models.Index(fields=['-executed_at']),
        ]

    def __str__(self):
        return f"{self.symbol} {self.executed_qty} @ {self.executed_price} on {self.executed_at}"


# ============= MARKET SESSION MODEL =============
class MarketSession(models.Model):
    """Manage market trading sessions and hours"""
    SESSION_STATUS_CHOICES = [
        ('PRE_OPEN', 'PRE_OPEN'),       # Future: 9:00-11:00
        ('CONTINUOUS', 'CONTINUOUS'),   # 11:00-15:00
        ('CLOSED', 'CLOSED'),           # Outside trading hours
        ('PAUSED', 'PAUSED'),           # Admin paused
    ]

    session_date = models.DateField(unique=True, db_index=True)
    status = models.CharField(max_length=15, choices=SESSION_STATUS_CHOICES, default='CLOSED')
    opened_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'market_sessions'
        ordering = ['-session_date']

    def __str__(self):
        return f"{self.session_date} - {self.status}"


# ============= LEGACY TRADE MODEL (KEPT FOR BACKWARD COMPATIBILITY) =============
class Trade(models.Model):
    """Legacy model - kept for backward compatibility with existing data"""
    SIDE_CHOICES = [
        ('BUY', 'BUY'),
        ('SELL', 'SELL'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'PENDING'),
        ('COMPLETED', 'COMPLETED'),
        ('CANCELLED', 'CANCELLED'),
        ('REJECTED', 'REJECTED'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='trades'
    )

    symbol = models.CharField(max_length=50, db_index=True)
    side = models.CharField(max_length=4, choices=SIDE_CHOICES, db_index=True)

    qty = models.PositiveIntegerField()
    price = models.FloatField(null=True, blank=True)  # executed price or limit price

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='COMPLETED', db_index=True)

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'trades'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'symbol', '-created_at']),
            models.Index(fields=['symbol', '-created_at']),
        ]


    def __str__(self):
        return f"{self.user_id} {self.side} {self.symbol} x{self.qty} @ {self.price}"


# ============= WATCHLIST MODEL =============
class Watchlist(models.Model):
    """User's watchlist for stocks they want to track and get recommendations for"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='watchlist'
    )
    symbol = models.CharField(max_length=50, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'watchlist'
        unique_together = [['user', 'symbol']]
        indexes = [
            models.Index(fields=['user', 'symbol']),
        ]

    def __str__(self):
        return f"{self.user.email} watching {self.symbol}"


# ============= STOCK RECOMMENDATION MODEL =============
class StockRecommendation(models.Model):
    """Store LSTM-based recommendations for stocks"""
    symbol = models.CharField(max_length=50, db_index=True)
    current_price = models.FloatField()
    predicted_next_close = models.FloatField()
    predicted_return = models.FloatField(null=True, blank=True)
    trend = models.CharField(max_length=20, choices=[('Bullish', 'Bullish'), ('Bearish', 'Bearish'), ('Neutral', 'Neutral')], default='Neutral')
    recommendation = models.IntegerField(choices=[(1, 'BUY'), (0, 'HOLD'), (-1, 'SELL')])
    
    # Trading Levels
    entry_price = models.FloatField(null=True, blank=True)
    target_price = models.FloatField(null=True, blank=True)
    stop_loss = models.FloatField(null=True, blank=True)
    exit_price = models.FloatField(null=True, blank=True)
    
    # Quant Metrics
    rsi = models.FloatField(null=True, blank=True)
    expected_move = models.FloatField(null=True, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    market_condition = models.CharField(max_length=100, null=True, blank=True)
    reason = models.TextField(null=True, blank=True)
    
    rmse = models.FloatField(null=True, blank=True)
    mae = models.FloatField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    # academic disclaimer is part of the logic/display, not the model
    
    class Meta:
        db_table = 'stock_recommendations'
        ordering = ['symbol']

    def __str__(self):
        return f"Rec for {self.symbol}: {self.get_recommendation_display()}"



# ============= LEARNING MODULE =============

class CourseCategory(models.Model):
    """Category for courses (e.g., Trading Basics, Technical Analysis)"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Course Categories"

    def __str__(self):
        return self.name


class Course(models.Model):
    """Structured Course containing multiple lessons"""
    DIFFICULTY_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    category = models.ForeignKey(CourseCategory, on_delete=models.SET_NULL, null=True, related_name='courses')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='Beginner')
    image = models.ImageField(upload_to='courses/', null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class CandlestickLesson(models.Model):
    """Stores individual lessons about candlestick patterns"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons', null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='lessons/', null=True, blank=True)
    video_url = models.URLField(max_length=500, null=True, blank=True, help_text="YouTube video URL (e.g., https://www.youtube.com/watch?v=...)")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['course', 'order']
        verbose_name = "Lesson"
        verbose_name_plural = "Lessons"

    def __str__(self):
        return f"{self.course.title} - {self.title}" if self.course else self.title


class LessonQuiz(models.Model):
    """Stores quiz questions for a specific lesson"""
    lesson = models.ForeignKey(CandlestickLesson, on_delete=models.CASCADE, related_name='quizzes')
    question = models.CharField(max_length=300)
    option1 = models.CharField(max_length=200)
    option2 = models.CharField(max_length=200)
    option3 = models.CharField(max_length=200)
    option4 = models.CharField(max_length=200)
    correct_answer = models.CharField(max_length=200, help_text="Exact text of the correct option")
    
    class Meta:
        verbose_name = "Lesson Quiz"
        verbose_name_plural = "Lesson Quizzes"

    def __str__(self):
        return f"Quiz for {self.lesson.title}"


class UserLessonProgress(models.Model):
    """Tracks user progress for each lesson"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(CandlestickLesson, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'lesson']
    
    def __str__(self):
        return f"{self.user.email} - {self.lesson.title}: {'Completed' if self.is_completed else 'In Progress'}"


class UserCourseProgress(models.Model):
    """Tracks overall progress for a course"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='course_progress')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    progress_percent = models.FloatField(default=0.0)
    is_completed = models.BooleanField(default=False)
    last_accessed = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'course']

    def __str__(self):
        return f"{self.user.email} - {self.course.title}: {self.progress_percent}%"


# ============= SUBSCRIPTION MODELS =============

class SubscriptionPlan(models.Model):
    """Store available subscription plans and pricing"""
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    tier = models.IntegerField(default=1, help_text="1=Basic, 2=Premium, 3=Gold")
    duration_days = models.PositiveIntegerField(help_text="Duration of the plan in days")
    description = models.TextField(help_text="Description of features included")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - Rs {self.price} [Tier {self.tier}]"


class UserSubscription(models.Model):
    """Link users to their subscription plans"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, related_name='subscribers')
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.plan.name if self.plan else 'No Plan'}"

    @property
    def is_expired(self):
        """Check if subscription has expired"""
        return timezone.now() > self.end_date

    def has_access(self, required_tier):
        """Check if user has at least the required tier level"""
        if not self.is_active or self.is_expired:
            return False
        return self.plan.tier >= required_tier

    def save(self, *args, **kwargs):
        """Auto-calculate end_date if not set"""
        if not self.end_date and self.plan:
            self.end_date = self.start_date + timezone.timedelta(days=self.plan.duration_days)
        super().save(*args, **kwargs)


class PaymentTransaction(models.Model):
    """Track payment attempts and their status"""
    STATUS_CHOICES = [
        ('PENDING', 'PENDING'),
        ('COMPLETED', 'COMPLETED'),
        ('FAILED', 'FAILED'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    gateway = models.CharField(max_length=50, default='esewa')
    verification_image = models.ImageField(upload_to='payment_proofs/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.id} - {self.user.email} - {self.status}"


# --- SIGNALS ---
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=PaymentTransaction)
def activate_subscription_on_payment(sender, instance, created, **kwargs):
    """Automatically activate subscription when PaymentTransaction is marked COMPLETED by admin"""
    if instance.status == 'COMPLETED':
        from django.utils import timezone
        
        UserSubscription.objects.update_or_create(
            user=instance.user,
            defaults={
                'plan': instance.plan,
                'start_date': timezone.now(),
                # end_date calculation is handled by UserSubscription.save() logic if not set,
                # but we'll set it here explicitly for clarity
                'end_date': timezone.now() + timezone.timedelta(days=instance.plan.duration_days),
                'is_active': True
            }
        )

