from django import template

register = template.Library()

@register.filter(name='getItem')
def getItem(dictionary, value):
    return dictionary.get(value)
