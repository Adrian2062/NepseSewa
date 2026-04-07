import time
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from myapp.models import NEPSEPrice

def get_playback_state():
    """
    Bulletproof Playback Engine.
    Matches the current Nepal time (HH:MM) to the closest historical data point.
    """
    from myapp.services.market_session import get_current_session
    session = get_current_session()
    
    # Use real session state for production. Forced False for demo testing.
    is_open = False 
    
    if is_open:
        return {'is_playback': False, 'timestamp': None}
        
    # Find most recent date with full data
    best_dates = NEPSEPrice.objects.values('timestamp__date').annotate(
        count=Count('id')
    ).filter(count__gt=100).order_by('-timestamp__date')
    
    if not best_dates:
        return {'is_playback': False, 'timestamp': None}
        
    last_date = best_dates[0]['timestamp__date']
    
    # Get chronological timestamps for that day
    timestamps = list(NEPSEPrice.objects.filter(
        timestamp__date=last_date
    ).values_list('timestamp', flat=True).distinct().order_by('timestamp'))
    
    if not timestamps:
        return {'is_playback': False, 'timestamp': None}

    # --- BULLETPROOF CLOCK SYNC ---
    now = timezone.localtime() # Current real Nepal time
    
    # Create a "Target Time" using today's clock but yesterday's date
    target_datetime = now.replace(
        year=last_date.year, 
        month=last_date.month, 
        day=last_date.day,
        second=0, 
        microsecond=0
    )
    
    # Find the historical timestamp that is CLOSEST to our Target Time
    # This prevents the system from failing if a specific minute wasn't scraped
    closest_ts = timestamps[0]
    smallest_diff = abs((timezone.localtime(closest_ts) - target_datetime).total_seconds())

    for ts in timestamps:
        diff = abs((timezone.localtime(ts) - target_datetime).total_seconds())
        if diff < smallest_diff:
            smallest_diff = diff
            closest_ts = ts
    
    # If the closest time is more than 2 hours away (e.g., it's 8:00 AM right now, 
    # but data only starts at 11:00 AM), we fall back to the looping behavior
    # so the demo doesn't look completely frozen.
    if smallest_diff > 7200: 
        current_minute_abs = int(time.time() // 60)
        index = current_minute_abs % len(timestamps)
        closest_ts = timestamps[index]

    return {
        'is_playback': True,
        'timestamp': closest_ts
    }