from django import template

register = template.Library()

@register.filter
def ordinal(value):
    """Converts 1 to 1st, 2 to 2nd, etc."""
    try:
        value = int(value)
    except (TypeError, ValueError):
        return value
    
    if 10 <= value % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(value % 10, 'th')
    
    return f'{value}{suffix}'