"""
Market Session Management Service
Handles Nepal timezone (UTC+5:45) and market hours validation
"""
from django.utils import timezone
from datetime import datetime, time, timedelta
import pytz
from myapp.models import MarketSession


# Nepal timezone is UTC+5:45
NEPAL_TZ = pytz.timezone('Asia/Kathmandu')

# Market hours (Nepal time)
CONTINUOUS_START = time(11, 0)  # 11:00 AM
CONTINUOUS_END = time(15, 0)    # 3:00 PM


def get_nepal_time():
    """Get current time in Nepal timezone"""
    return timezone.now().astimezone(NEPAL_TZ)


def get_current_session():
    """Get or create today's market session"""
    nepal_now = get_nepal_time()
    today = nepal_now.date()
    
    session, created = MarketSession.objects.get_or_create(
        session_date=today,
        defaults={
            'status': 'CLOSED',
            'is_active': False,
            'is_manual': False
        }
    )
    
    # Auto-update session status based on time
    if not created and not session.is_manual:
        update_session_status(session, nepal_now)
    
    return session


def update_session_status(session, nepal_now=None):
    """Update session status based on current time"""
    if nepal_now is None:
        nepal_now = get_nepal_time()
    
    current_time = nepal_now.time()
    
    # Don't auto-update if admin has manually set status
    if session.is_manual:
        return session
    
    # Check if within continuous session hours
    if CONTINUOUS_START <= current_time < CONTINUOUS_END:
        if session.status != 'CONTINUOUS':
            session.status = 'CONTINUOUS'
            session.is_active = True
            if not session.opened_at:
                session.opened_at = nepal_now
            session.save()
    else:
        if session.status != 'CLOSED':
            session.status = 'CLOSED'
            session.is_active = False
            if session.opened_at and not session.closed_at:
                session.closed_at = nepal_now
            session.save()
    
    return session


def is_market_open():
    """Check if market is currently open for trading"""
    session = get_current_session()
    return session.is_active and session.status == 'CONTINUOUS'


def get_market_status():
    """Get current market status with details"""
    nepal_now = get_nepal_time()
    session = get_current_session()
    
    return {
        'status': session.status,
        'is_active': session.is_active,
        'nepal_time': nepal_now.isoformat(),
        'session_date': session.session_date.isoformat(),
        'opened_at': session.opened_at.isoformat() if session.opened_at else None,
        'closed_at': session.closed_at.isoformat() if session.closed_at else None,
    }


def is_continuous_session():
    """Check if current time is within continuous session hours"""
    nepal_now = get_nepal_time()
    current_time = nepal_now.time()
    return CONTINUOUS_START <= current_time < CONTINUOUS_END


def pause_market():
    """Admin function to pause market"""
    session = get_current_session()
    session.status = 'PAUSED'
    session.is_active = False
    session.is_manual = True
    session.save()
    return session


def resume_market(force=False):
    """Admin function to resume market"""
    session = get_current_session()
    nepal_now = get_nepal_time()
    
    # If force=True, we set is_manual to prevent auto-closing
    if force:
        session.status = 'CONTINUOUS'
        session.is_active = True
        session.is_manual = True
    elif is_continuous_session():
        session.status = 'CONTINUOUS'
        session.is_active = True
        session.is_manual = False
    else:
        session.status = 'CLOSED'
        session.is_active = False
        session.is_manual = False
    
    session.save()
    return session
