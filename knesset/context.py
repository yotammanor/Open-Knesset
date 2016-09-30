from django.conf import settings

d = {'debug': getattr(settings, 'LOCAL_DEV', False)}


def processor(request):
    from django.contrib.flatpages.models import FlatPage
    from django.core.cache import cache
    from knesset.utils import get_cache_key
    cache_key = get_cache_key(request.path)
    page = cache.get('flatpage_block_%s' % cache_key)
    if not page:
        qs = FlatPage.objects.filter(url=request.path)
        if qs.exists():
            page = qs.values('title', 'content', 'template_name')[0]
        else:
            page = 'NO PAGE'
        cache.set('flatpage_block_%s' % cache_key, page, 86400)
    d.update({
        'flatpage': page if page and page != 'NO PAGE' else None
    })
    return d
