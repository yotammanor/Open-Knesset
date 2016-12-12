# -*- coding: utf-8 -*-

from django.contrib import admin
from django.contrib.flatpages.admin import FlatPage, FlatPageAdmin as DjangoFlatPageAdmin

from .models import Tidbit


class TidibitAdmin(admin.ModelAdmin):
    model = Tidbit
    list_display = ('title', 'content', 'ordering', 'is_active')
    list_display_links = ('title', 'content')
    list_editable = ('ordering', 'is_active')


admin.site.register(Tidbit, TidibitAdmin)


class FlatPageAdmin(DjangoFlatPageAdmin):
    def save_model(self, request, obj, form, change):
        super(FlatPageAdmin, self).save_model(request, obj, form, change)
        from django.core.cache import cache
        from knesset.utils import get_cache_key
        cache.delete('flatpage_block_%s' % get_cache_key(obj.url))


admin.site.unregister(FlatPage)
admin.site.register(FlatPage, FlatPageAdmin)
