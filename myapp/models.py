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
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        db_table = 'users'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


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

class Trade(models.Model):
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
