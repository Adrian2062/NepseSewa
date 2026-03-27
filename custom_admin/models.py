from django.db import models
from django.conf import settings

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('buy', 'Buy Order'),
        ('sell', 'Sell Order'),
        ('membership', 'Membership'),
        ('system', 'System'),
    )
    
    # Restored null=True, blank=True to prevent migration errors and allow global notifications
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True, help_text="Leave blank to send to all users")
    title = models.CharField(max_length=200)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='system')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering =['-created_at']

    def __str__(self):
        username = self.user.username if self.user else "GLOBAL"
        return f"{username} - {self.type} - {self.title}"

class ActivityLog(models.Model):
    """System activity logs for tracking user and admin actions"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.created_at.strftime('%Y-%m-%d %H:%M')}] {self.user} - {self.action}"

class SystemSetting(models.Model):
    """Global system configuration settings"""
    key = models.CharField(max_length=100, unique=True)
    value = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.key}: {self.value}"
