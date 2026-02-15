from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def query_transform(context, **kwargs):
    """
    Creates a URL query string with updated parameters.
    Usage: {% query_transform page=page_obj.next_page_number %}
    """
    query = context['request'].GET.copy()

    for key, value in kwargs.items():
        if value is not None:
            query[key] = value
        else:
            query.pop(key, None)

    return query.urlencode()