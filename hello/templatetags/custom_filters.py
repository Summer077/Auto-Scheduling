from django import template
import hashlib

register = template.Library()

@register.filter
def ordinal(value):
    """Convert integer to ordinal string (1 -> 1st, 2 -> 2nd, etc.)"""
    try:
        value = int(value)
    except (ValueError, TypeError):
        return value
    
    if 10 <= value % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(value % 10, 'th')
    
    return f"{value}{suffix}"


@register.filter
def schedule_height(duration_minutes):
    """Calculate height in pixels for a schedule block (30 min = 60px), always add +30 min."""
    try:
        duration_minutes = int(duration_minutes)
    except (ValueError, TypeError):
        duration_minutes = 0

    duration_minutes += 30  # always add one 30-min slot
    px_per_minute = 60 / 30  # 2 px per minute
    total_height = (duration_minutes * px_per_minute) - 2  # offset for borders
    return int(total_height)


@register.filter
def schedule_top(start_time):
    """
    Convert start time (e.g., '07:30') into vertical position in pixels.
    Each 30-minute slot = 60px height.
    The base time is 7:00 AM.
    """
    try:
        hours, minutes = map(int, str(start_time).split(':'))
        total_minutes = (hours * 60) + minutes
        base_minutes = 7 * 60  # starting point = 7:00 AM
        minutes_from_start = total_minutes - base_minutes
        px_per_minute = 60 / 30  # 2 px per minute
        return int(minutes_from_start * px_per_minute)
    except Exception:
        return 0


@register.filter
def auto_color(value):
    """
    Generate a distinct color for a course based on its code.
    Returns a hex color code.
    """
    color_palette = [
        '#FF6B6B',  # Red
        '#4ECDC4',  # Teal
        '#45B7D1',  # Blue
        '#FFA07A',  # Light Salmon
        '#98D8C8',  # Mint
        '#F7DC6F',  # Yellow
        '#BB8FCE',  # Purple
        '#85C1E2',  # Sky Blue
        '#F8B88B',  # Peach
        '#52B788',  # Green
        '#FF8FAB',  # Pink
        '#FFB84D',  # Orange
        '#A8DADC',  # Light Blue
        '#E76F51',  # Coral
        '#2A9D8F',  # Dark Teal
        '#E9C46A',  # Gold
        '#F4A261',  # Sandy Brown
        '#8E7CC3',  # Lavender
        '#6A4C93',  # Deep Purple
        '#00B4D8',  # Bright Blue
    ]
    
    if value:
        hash_object = hashlib.md5(str(value).encode())
        hash_int = int(hash_object.hexdigest(), 16)
        return color_palette[hash_int % len(color_palette)]
    
    return '#FFA726'


@register.filter
def rgba_25(hex_color):
    """
    Convert a hex color (#RRGGBB or RRGGBB) into an rgba string with 0.25 alpha.
    If input is invalid, return a sensible fallback rgba(255,167,38,0.25) (matches #FFA726 with 25% opacity).
    """
    if not hex_color:
        return 'rgba(255,167,38,0.25)'

    # Normalize the string
    c = str(hex_color).strip()
    if c.startswith('#'):
        c = c[1:]

    # Support short form like 'FAB' -> 'FFAABB'
    if len(c) == 3:
        try:
            r = int(c[0]*2, 16)
            g = int(c[1]*2, 16)
            b = int(c[2]*2, 16)
            return f'rgba({r},{g},{b},0.25)'
        except Exception:
            return 'rgba(255,167,38,0.25)'

    if len(c) != 6:
        return 'rgba(255,167,38,0.25)'

    try:
        r = int(c[0:2], 16)
        g = int(c[2:4], 16)
        b = int(c[4:6], 16)
        return f'rgba({r},{g},{b},0.25)'
    except Exception:
        return 'rgba(255,167,38,0.25)'
