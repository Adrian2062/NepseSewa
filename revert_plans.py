import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

from myapp.models import SubscriptionPlan

# Clear all old plans
SubscriptionPlan.objects.all().delete()

# 1. Basic (Free)
SubscriptionPlan.objects.create(
    name="Basic (Free)",
    price=0,
    tier=1,
    duration_days=365,
    description="- Daily Market Summary- Standard Stock Charts- Watchlist up to 5 stocks- Access to Beginner Courses",
    is_active=True
)

# 2. Premium Monthly
SubscriptionPlan.objects.create(
    name="Premium Monthly",
    price=499,
    tier=2,
    duration_days=30,
    description="- Real-time NEPSE Data- Advanced Portfolio Analytics- AI-Powered Recommendations- Unlimited Watchlist Stocks- Access to Intermediate Courses",
    is_active=True
)

# 3. Gold Trader
SubscriptionPlan.objects.create(
    name="Gold Trader",
    price=999,
    tier=3,
    duration_days=30,
    description="- Everything in Premium- Exclusive Advanced Courses- Deep LSTM Analytics- Direct CSV Data Export features",
    is_active=True
)

# 4. Premium Annual
SubscriptionPlan.objects.create(
    name="Premium Annual",
    price=4999,
    tier=2,
    duration_days=365,
    description="- All Premium Features- 15% Discount vs Monthly- Priority Support- Priority access to new features",
    is_active=True
)

print("SUCCESS: Reverted to original 4 plans.")
