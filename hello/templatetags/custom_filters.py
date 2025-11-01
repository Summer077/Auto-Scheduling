from django import template
import hashlib

register = template.Library()

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
    """Calculate the height in pixels for a schedule block.
    Each 30-minute slot = 50px height"""
    if not duration_minutes:
        return 50
    
    slot_height = 50
    slot_minutes = 30
    num_slots = duration_minutes / slot_minutes
    total_height = (num_slots * slot_height) + 40
    
    return int(total_height)
    
    return int(total_height)

@register.filter
def auto_color(value):
    """
    Generate a distinct color for a course based on its code.
    Returns a hex color code.
    """
    # Predefined palette of distinct, visually appealing colors
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
    
    # Generate a hash from the value (course code)
    if value:
        # Create a hash of the course code
        hash_object = hashlib.md5(str(value).encode())
        hash_int = int(hash_object.hexdigest(), 16)
        # Use modulo to select from palette
        return color_palette[hash_int % len(color_palette)]
    
    # Default fallback color
    return '#FFA726'