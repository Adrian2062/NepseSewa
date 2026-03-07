from myapp.models import SubscriptionPlan
plans = SubscriptionPlan.objects.all()
print(f"Total plans: {len(plans)}")
for p in plans:
    print(f"Name: '{p.name}', Price: {p.price}, Active: {p.is_active}")
