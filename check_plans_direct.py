import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NepseSewa.settings')
django.setup()

from myapp.models import SubscriptionPlan
plans = SubscriptionPlan.objects.all()
with open('plans_final.txt', 'w') as f:
    f.write(f"Count: {len(plans)}\n")
    for p in plans:
        f.write(f"'{p.name}' | Tier: {p.tier} | Price: {p.price}\n")
