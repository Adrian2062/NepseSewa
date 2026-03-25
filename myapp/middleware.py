from django.utils import timezone
from django.contrib import messages
from .models import SubscriptionPlan

class AutoDowngradeMiddleware:
    """
    Middleware to check if a user's premium subscription has expired.
    If expired, it automatically downgrades them to the Basic plan (Tier 1).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if hasattr(request.user, 'subscription') and request.user.subscription:
                sub = request.user.subscription
                
                # Check if subscription is expired AND it was a Premium plan (Tier > 1)
                if sub.is_expired and sub.plan and sub.plan.tier > 1:
                    
                    # Find the Basic Plan (Tier 1)
                    basic_plan = SubscriptionPlan.objects.filter(tier=1).first()
                    
                    if basic_plan:
                        # 1. Update the Subscription back to Basic
                        sub.plan = basic_plan
                        sub.start_date = timezone.now()
                        sub.end_date = timezone.now() + timezone.timedelta(days=basic_plan.duration_days)
                        sub.save()
                        
                        # 2. Update the User Profile to remove Premium status
                        request.user.is_premium = False
                        
                        # (Optional) If you also want to reset their balance back to default 100,000 
                        # after Premium expires, uncomment the next line:
                        # request.user.virtual_balance = 100000.00
                        
                        request.user.save(update_fields=['is_premium'])
                        
                        # 3. Notify the user on their screen
                        messages.warning(request, "Your Premium subscription has expired. You have been redirected to the Basic plan.")
        
        response = self.get_response(request)
        return response