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
    description="- Daily Market Summary\n- Standard Stock Charts\n- Watchlist up to 5 stocks\n- Access to Beginner Courses",
    is_active=True
)

# Create Premium Plan (Paid)
SubscriptionPlan.objects.create(
    name="Premium",
    price=500,
    tier=2,
    duration_days=30,
    description="- Real-time NEPSE Data\n- Advanced Portfolio Analytics\n- AI-Powered Recommendations\n- Unlimited Watchlist Stocks\n- Access to Intermediate Courses",
    is_active=True
)

print("SUCCESS: Database updated with 'Basic' and 'Premium' plans and original features.")
