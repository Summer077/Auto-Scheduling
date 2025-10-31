from django import template

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