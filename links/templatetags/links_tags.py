from django import template
from django.conf import settings
from django.core.cache import cache
from links.models import Link

register = template.Library()


@register.inclusion_tag('links/_object_links.html')
def object_links(obj):
    if hasattr(obj, 'cached_links'):
        obj_links = obj.cached_links
    else:
        obj_links = Link.objects.for_model(obj)
    return {'links': obj_links, 'MEDIA_URL': settings.MEDIA_URL}


@register.inclusion_tag('links/_object_icon_links.html')
def object_icon_links(obj):
    "Display links as icons, to match the new design"
    key = "%s.%s.%s" % (obj._meta.app_label, obj._meta.module_name, obj.pk)
    obj_links = cache.get(key, None)  # look in the cache first
    if obj_links is None:  # if not found in cache
        if hasattr(obj, 'cached_links'):
            obj_links = obj.cached_links
        else:
            obj_links = Link.objects.for_model(obj)  # get it from db
        cache.set(key, obj_links, settings.LONG_CACHE_TIME)  # and save to cache
    return {'links': obj_links}
