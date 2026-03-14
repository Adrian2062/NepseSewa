from django import template
from django.db.models import Model
import datetime

register = template.Library()

@register.filter
def get_attribute(obj, attr_name):
    """
    Gets an attribute of an object dynamically from a string name.
    Useful for iterating through lists of fields in the generic list template.
    """
    if not hasattr(obj, attr_name):
        return None
    
    value = getattr(obj, attr_name)
    
    # Check if value is a callable (like a get_absolute_url method or related manager)
    if callable(value) and not isinstance(value, type):
        try:
            # We don't want to accidentally call things that mutate state
            # but usually for templates it's safe formatting functions
            value = value()
        except:
            return repr(value)
            
    # Format datetimes nicely
    if isinstance(value, datetime.datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, datetime.date):
        return value.strftime("%Y-%m-%d")
        
    return value
@register.filter
def get_item(dictionary, key):
    """Access dictionary items by key dynamically"""
    return dictionary.get(key)


@register.simple_tag
def url_replace(request, field, value):
    """Safely replace or add a GET parameter while preserving others"""
    dict_ = request.GET.copy()
    dict_[field] = value
    return dict_.urlencode()


@register.filter
def replace(value, arg):
    """
    Standard string replace filter.
    Usage: {{ value|replace:"search,replacement" }}
    """
    if isinstance(value, str):
        args = arg.split(',')
        if len(args) == 2:
            return value.replace(args[0], args[1])
    return value
