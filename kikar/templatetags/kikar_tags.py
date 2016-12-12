from django import template
from django.conf import settings
from links.models import Link

register = template.Library()


@register.filter(name='objects_to_ids')
def objects_to_ids(list_of_objects):
    """

    Args:
        list_of_objects:

    Returns:
        a list of the ids of the objects in the list

    """
    return [x.id for x in list_of_objects]
