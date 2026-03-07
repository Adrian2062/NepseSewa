import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

from myapp.models import SubscriptionPlan

# Clear all old plans
print("Deleting existing plans...")
deleted_count = SubscriptionPlan.objects.all().delete()
print(f"Deleted {deleted_count} plans.")

# Create Basic Plan (Free)
p1 = SubscriptionPlan.objects.create(
    name="Basic",
    price=0,
    tier=1,
    duration_days=365,
    description="- Daily Market Summary- Standard Stock Charts- Watchlist up to 5 stocks- Access to Beginner Courses",
    is_active=True
)
print(f"Created: {p1.name}")

# Create Premium Plan (Paid)
p2 = SubscriptionPlan.objects.create(
    name="Premium",
    price=499,
    tier=2,
    duration_days=30,
    description="- Real-time NEPSE Data- Advanced Portfolio Analytics- AI-Powered Recommendations- Unlimited Watchlist Stocks- Access to Intermediate Courses",
    is_active=True
)
print(f"Created: {p2.name}")

# Verify
all_plans = SubscriptionPlan.objects.all()
print(f"FINAL_PLAN_LIST: {[p.name for p in all_plans]}")
