# from django.contrib.auth.models import AbstractUser
# from django.db import models

# class CustomUser(AbstractUser):
#     """Extended user model with additional fields"""
#     email = models.EmailField(unique=True)
#     first_name = models.CharField(max_length=100)
#     last_name = models.CharField(max_length=100)
#     virtual_balance = models.DecimalField(max_digits=12, decimal_places=2, default=100000.00)
#     portfolio_value = models.DecimalField(max_digits=12, decimal_places=2, default=100000.00)
#     date_joined = models.DateTimeField(auto_now_add=True)
    
#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
#     class Meta:
#         db_table = 'users'
    
#     def __str__(self):
#         return f"{self.first_name} {self.last_name}"
# Add this to your existing myapp/models.py

# ADD THESE AT THE END OF myapp/models.py

from django.db import models
from django.utils import timezone

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
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['symbol', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.symbol} - {self.timestamp}"


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
        return f"NEPSE Index - {self.timestamp}"