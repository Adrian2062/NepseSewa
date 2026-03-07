import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

from myapp.models import SubscriptionPlan

# Clear all old plans
SubscriptionPlan.objects.all().delete()

# Create Basic Plan (Free)
SubscriptionPlan.objects.create(
    name="Basic",
    price=0,
    tier=1,
    duration_days=365,
    description="Standard Market Data\nBasic Portfolio Tracking\nStandard Watchlist\nAccess to Beginner Lessons",
    is_active=True
)

# Create Premium Plan (Paid)
SubscriptionPlan.objects.create(
    name="Premium",
    price=500,
    tier=2,
    duration_days=30,
    description="Priority Market Access\nAdvanced Portfolio Tools\nEnhanced Watchlist Capacity\nAccess to All Learning Content",
    is_active=True
)

print("SUCCESS: Database updated with 'Basic' and 'Premium' plans.")
