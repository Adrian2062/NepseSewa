import time
from django.db.models import Count, Max
from django.utils import timezone
from myapp.models import NEPSEPrice
from custom_admin.models import SystemSetting

def get_playback_state():
    """
    Smart Playback Engine.
    Auto-detects if the scraper is running by checking data freshness.
    If data is old, falls back to historical playback.
    """
    from myapp.services.market_session import get_current_session
    session = get_current_session()
    
    # 1. --- AUTO DETECT LIVE SCRAPER ---
    # Find the absolute newest record in the database
    latest_record = NEPSEPrice.objects.aggregate(Max('timestamp'))['timestamp__max']
    
    is_live = False
    if latest_record:
        # Calculate how many seconds ago the data was saved
        time_difference = (timezone.now() - latest_record).total_seconds()
        
        # If data is less than 3 minutes old (180 seconds), the scraper is running!
        if time_difference < 180:
            is_live = True

    # 2. --- AUTO UPDATE UI STATUS ---
    if is_live:
        # Force the database session to CONTINUOUS so the frontend knows we are live
        if session.status != 'CONTINUOUS':
            session.status = 'CONTINUOUS'
            session.is_active = True
            session.save()
        
        # Return False for playback so the frontend asks for LIVE data
        return {'is_playback': False, 'timestamp': None}
        
    else:
        # Force the session to CLOSED if scraper is off
        if session.status != 'CLOSED':
            session.status = 'CLOSED'
            session.is_active = False
            session.save()
            
    # 3. --- START PLAYBACK MODE LOGIC (Only runs if scraper is off) ---
    
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

    # Clock Sync for Time Machine
    now = timezone.localtime()
    target_datetime = now.replace(
        year=last_date.year, month=last_date.month, day=last_date.day,
        second=0, microsecond=0
    )
    
    # Find closest historical point
    closest_ts = timestamps[0]
    smallest_diff = abs((timezone.localtime(closest_ts) - target_datetime).total_seconds())

    for ts in timestamps:
        diff = abs((timezone.localtime(ts) - target_datetime).total_seconds())
        if diff < smallest_diff:
            smallest_diff = diff
            closest_ts = ts
    
    # Loop fallback
    if smallest_diff > 7200: 
        current_minute_abs = int(time.time() // 60)
        index = current_minute_abs % len(timestamps)
        closest_ts = timestamps[index]

    return {
        'is_playback': True,
        'timestamp': closest_ts
    }