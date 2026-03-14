from django.db.models import Q
from myapp.models import Sector, SubscriptionPlan

def get_filter_config(model_name):
    """
    Returns a list of filter configurations for a given model.
    Each config is a dict with: 'name', 'label', 'type', 'options' (for select), and 'query' (function).
    """
    configs = []

    if model_name == 'CustomUser':
        configs = [
            {
                'name': 'plan',
                'label': 'Plan',
                'type': 'select',
                'options': [('', 'All Plans'), ('basic', 'Basic'), ('premium', 'Premium')],
                'query': lambda qs, val: qs.filter(is_premium=(val == 'premium')) if val else qs
            },
            {
                'name': 'status',
                'label': 'Status',
                'type': 'select',
                'options': [('', 'All Status'), ('active', 'Active'), ('inactive', 'Inactive')],
                'query': lambda qs, val: qs.filter(is_active=(val == 'active')) if val else qs
            },
            {
                'name': 'date',
                'label': 'Joined Date',
                'type': 'date',
                'query': lambda qs, val: qs.filter(date_joined__date=val) if val else qs
            }
        ]

    elif model_name == 'Order':
        configs = [
            {
                'name': 'side',
                'label': 'Side',
                'type': 'select',
                'options': [('', 'All Types'), ('BUY', 'Buy'), ('SELL', 'Sell')],
                'query': lambda qs, val: qs.filter(side=val) if val else qs
            },
            {
                'name': 'status',
                'label': 'Status',
                'type': 'select',
                'options': [('', 'All Status'), ('OPEN', 'Open'), ('PARTIAL', 'Partial'), ('FILLED', 'Filled'), ('CANCELLED', 'Cancelled')],
                'query': lambda qs, val: qs.filter(status=val) if val else qs
            },
            {
                'name': 'date',
                'label': 'Order Date',
                'type': 'date',
                'query': lambda qs, val: qs.filter(created_at__date=val) if val else qs
            }
        ]

    elif model_name == 'TradeExecution':
        configs = [
            {
                'name': 'symbol',
                'label': 'Symbol',
                'type': 'text',
                'query': lambda qs, val: qs.filter(symbol__icontains=val) if val else qs
            },
            {
                'name': 'date',
                'label': 'Execution Date',
                'type': 'date',
                'query': lambda qs, val: qs.filter(executed_at__date=val) if val else qs
            }
        ]

    elif model_name == 'Stock':
        sectors = [('', 'All Sectors')] + [(s.id, s.name) for s in Sector.objects.all()]
        configs = [
            {
                'name': 'sector',
                'label': 'Sector',
                'type': 'select',
                'options': sectors,
                'query': lambda qs, val: qs.filter(sector_id=val) if val else qs
            },
            {
                'name': 'status',
                'label': 'Status',
                'type': 'select',
                'options': [('', 'All Status'), ('active', 'Active'), ('inactive', 'Inactive')],
                'query': lambda qs, val: qs.filter(is_active=(val == 'active')) if val else qs
            }
        ]

    elif model_name == 'NEPSEPrice':
        configs = [
            {
                'name': 'symbol',
                'label': 'Symbol',
                'type': 'text',
                'query': lambda qs, val: qs.filter(symbol__icontains=val) if val else qs
            },
            {
                'name': 'performance',
                'label': 'Performance',
                'type': 'select',
                'options': [('', 'All'), ('gainers', 'Gainers'), ('losers', 'Losers')],
                'query': lambda qs, val: qs.filter(change_pct__gt=0) if val == 'gainers' else (qs.filter(change_pct__lt=0) if val == 'losers' else qs)
            }
        ]

    elif model_name == 'StockRecommendation':
        configs = [
            {
                'name': 'recommendation',
                'label': 'Rec',
                'type': 'select',
                'options': [('', 'All'), ('1', 'BUY'), ('0', 'HOLD'), ('-1', 'SELL')],
                'query': lambda qs, val: qs.filter(recommendation=val) if val else qs
            },
            {
                'name': 'confidence',
                'label': 'Confidence >',
                'type': 'number',
                'query': lambda qs, val: qs.filter(confidence__gte=float(val)/100) if val else qs
            }
        ]

    elif model_name == 'UserSubscription':
        plans = [('', 'All Plans')] + [(p.id, p.name) for p in SubscriptionPlan.objects.all()]
        configs = [
            {
                'name': 'plan',
                'label': 'Plan',
                'type': 'select',
                'options': plans,
                'query': lambda qs, val: qs.filter(plan_id=val) if val else qs
            },
            {
                'name': 'status',
                'label': 'Status',
                'type': 'select',
                'options': [('', 'All Status'), ('active', 'Active'), ('expired', 'Expired')],
                'query': lambda qs, val: qs.filter(is_active=(val == 'active')) if val else qs
            }
        ]

    elif model_name == 'PaymentTransaction':
        plans = [('', 'All Plans')] + [(p.id, p.name) for p in SubscriptionPlan.objects.all()]
        configs = [
            {
                'name': 'status',
                'label': 'Status',
                'type': 'select',
                'options': [('', 'All Status'), ('PENDING', 'Pending'), ('COMPLETED', 'Completed'), ('FAILED', 'Failed')],
                'query': lambda qs, val: qs.filter(status=val) if val else qs
            },
            {
                'name': 'plan',
                'label': 'Plan',
                'type': 'select',
                'options': plans,
                'query': lambda qs, val: qs.filter(plan_id=val) if val else qs
            },
            {
                'name': 'date',
                'label': 'Date',
                'type': 'date',
                'query': lambda qs, val: qs.filter(created_at__date=val) if val else qs
            }
        ]

    elif model_name == 'Course':
        from myapp.models import CourseCategory
        categories = [('', 'All Categories')] + [(c.id, c.name) for c in CourseCategory.objects.all()]
        configs = [
            {
                'name': 'category',
                'label': 'Category',
                'type': 'select',
                'options': categories,
                'query': lambda qs, val: qs.filter(category_id=val) if val else qs
            }
        ]

    elif model_name == 'CandlestickLesson':
        from myapp.models import Course
        courses = [('', 'All Courses')] + [(c.id, c.title) for c in Course.objects.all()]
        configs = [
            {
                'name': 'course',
                'label': 'Course',
                'type': 'select',
                'options': courses,
                'query': lambda qs, val: qs.filter(course_id=val) if val else qs
            }
        ]

    return configs
