from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse

def subscription_required(tier=1):
    """
    Decorator for views that checks if a user has an active subscription of at least the given tier.
    Tiers: 1=Basic, 2=Premium, 3=Gold
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                if request.path.startswith('/api/'):
                    return JsonResponse({'success': False, 'message': 'Authentication required.'}, status=401)
                return redirect('login')
            
            # Check for active subscription and tier
            try:
                subscription = request.user.subscription
                if subscription.has_access(tier):
                    return view_func(request, *args, **kwargs)
            except AttributeError:
                pass
                
            # Handle lack of subscription or tier
            msg = "This feature requires a premium subscription." if tier > 1 else "This feature requires an active subscription."
            if request.path.startswith('/api/'):
                return JsonResponse({
                    'success': False, 
                    'message': msg, 
                    'premium_required': True,
                    'required_tier': tier
                }, status=403)
            
            messages.warning(request, msg)
            return redirect('pricing')
            
        return _wrapped_view
    
    # Allows both @subscription_required and @subscription_required(tier=2)
    if callable(tier):
        func = tier
        tier = 1
        return decorator(func)
    return decorator

# Shortcuts
def premium_required(view_func):
    return subscription_required(tier=2)(view_func)

def gold_required(view_func):
    return subscription_required(tier=3)(view_func)
