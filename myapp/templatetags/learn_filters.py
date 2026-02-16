from django import template
import re

register = template.Library()

@register.filter(name='youtube_embed_url')
def youtube_embed_url(value):
    """
    Converts a standard YouTube URL into an embed URL.
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    """
    if not value:
        return ""

    # Patterns to match YouTube IDs
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"(?:youtu\.be\/)([0-9A-Za-z_-]{11})"
    ]

    for pattern in patterns:
        match = re.search(pattern, value)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube.com/embed/{video_id}"

    return value
@register.filter(name='mul')
def mul(value, arg):
    """Multiplies the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
