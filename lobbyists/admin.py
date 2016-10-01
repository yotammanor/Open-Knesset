from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from models import Lobbyist, LobbyistCorporation, LobbyistsChange, LobbyistCorporationAlias
from django.contrib.contenttypes import generic
from links.models import Link
from django.utils.text import mark_safe


class LinksInline(generic.GenericTabularInline):
    model = Link
    ct_fk_field = 'object_pk'
    extra = 1


class CorporationAliasInline(admin.TabularInline):
    model = LobbyistCorporationAlias
    fk_name = 'main_corporation'


class LobbyistAdmin(ImportExportModelAdmin):
    fields = ('person', 'description', 'image_url', 'large_image_url',)
    readonly_fields = ('person',)
    inlines = (LinksInline,)


class LobbyistCorporationAdmin(ImportExportModelAdmin):
    fields = ('name', 'description', 'lobbyists')
    readonly_fields = ('name', 'lobbyists')
    inlines = (LinksInline, CorporationAliasInline)
    list_display = ('name', 'alias_corporations')

    def lobbyists(self, obj):
        if obj.latest_data:
            return mark_safe(', '.join([
                u'<a href="/admin/lobbyists/lobbyist/'+unicode(lobbyist.pk)+'/">'+unicode(lobbyist)+u'</a>' for lobbyist in obj.latest_data.lobbyists.all()
            ]))


class LobbyistsChangeAdmin(admin.ModelAdmin):
    list_display = ('date', 'type', 'content_type', 'object_id', 'content_object')


admin.site.register(Lobbyist, LobbyistAdmin)
admin.site.register(LobbyistCorporation, LobbyistCorporationAdmin)
admin.site.register(LobbyistsChange, LobbyistsChangeAdmin)
