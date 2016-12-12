from django.contrib import admin
from django.contrib.contenttypes import generic
from django.db.models import Q
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
import urllib

from import_export.admin import ImportExportModelAdmin

from models import Member, Membership, MemberAltname
from models import CoalitionMembership, Correlation, Party, \
    Award, AwardType, Knesset
from links.models import Link
from video.models import Video
from persons.models import Person


class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 1


class MemberLinksInline(generic.GenericTabularInline):
    model = Link
    ct_fk_field = 'object_pk'
    extra = 1


class MemberAltnameInline(admin.TabularInline):
    model = MemberAltname
    extra = 1


class MemberPersonInline(admin.StackedInline):
    model = Person
    ct_fk_field = "mk"
    extra = 0
    max_num = 0
    fields = ['calendar_url']
    can_delete = False


class MemberRelatedVideosInline(generic.GenericTabularInline):
    model = Video
    ct_fk_field = 'object_pk'
    can_delete = False
    fields = ['title', 'description', 'embed_link', 'group', 'sticky', 'hide']
    ordering = ['group', '-sticky', '-published']
    readonly_fields = ['title', 'description', 'embed_link', 'group']
    extra = 0

    def queryset(self, request):
        qs = super(MemberRelatedVideosInline, self).queryset(request)
        qs = qs.filter(Q(hide=False) | Q(hide=None))
        return qs


class CoalitionMembershipAdmin(ImportExportModelAdmin):
    list_display = ('party', 'start_date', 'end_date')


admin.site.register(CoalitionMembership, CoalitionMembershipAdmin)


class PartyAdmin(ImportExportModelAdmin):
    ordering = ('name',)
    list_display = ('name', 'knesset', 'start_date', 'end_date',
                    'is_coalition', 'number_of_members',
                    'number_of_seats')
    list_filter = ('knesset',)
    inlines = (MembershipInline,)


admin.site.register(Party, PartyAdmin)


class MemberAdmin(ImportExportModelAdmin):
    ordering = ('name',)
    #    fields = ('name','start_date','end_date')
    list_display = ('name', 'gender', 'PartiesString', 'current_party',
                    'is_current', 'current_position')
    list_editable = ('is_current', 'current_position')
    search_fields = ['name']
    inlines = (MembershipInline, MemberLinksInline, MemberAltnameInline, MemberPersonInline,
               MemberRelatedVideosInline)
    list_filter = ('current_party__knesset', 'gender', 'is_current', 'current_party',)

    # A template for a very customized change view:
    change_form_template = 'admin/simple/change_form_with_extra.html'

    def change_view(self, request, object_id, extra_context=None):
        m = Member.objects.get(id=object_id)
        my_context = {
            'extra': {
                'hi_corr': m.CorrelationListToString(m.HighestCorrelations()),
                'low_corr': m.CorrelationListToString(m.LowestCorrelations()),
            }
        }
        return super(MemberAdmin, self).change_view(request, object_id,
                                                    extra_context=my_context)

    def queryset(self, request):
        return super(MemberAdmin, self).queryset(
            request).select_related('current_party')

    def save_model(self, request, obj, form, change):
        super(MemberAdmin, self).save_model(request, obj, form, change)
        # Delete the cache of the current member after updating:
        cache.delete('mk_%d' % obj.id)
        # Delete the template key
        obj_url = urllib.unquote(obj.get_absolute_url())
        if not isinstance(obj_url, unicode):
            obj_url = obj_url.decode('utf-8')
        key = make_template_fragment_key('mks_detail', [obj.id, 1, obj_url])
        cache.delete(key)


admin.site.register(Member, MemberAdmin)


class CorrelationAdmin(admin.ModelAdmin):
    ordering = ('-normalized_score',)


admin.site.register(Correlation, CorrelationAdmin)


class MembershipAdmin(ImportExportModelAdmin):
    list_select_related = True
    ordering = ('member__name',)
    list_display = ('member', 'party', 'start_date', 'end_date')
    list_filter = ('party', )


admin.site.register(Membership, MembershipAdmin)


class AwardTypeAdmin(admin.ModelAdmin):
    pass


admin.site.register(AwardType, AwardTypeAdmin)


class AwardAdmin(ImportExportModelAdmin):
    list_display = ('member', 'award_type', 'date_given')
    raw_id_fields = ('member',)


admin.site.register(Award, AwardAdmin)


class KnessetAdmin(admin.ModelAdmin):
    list_display = ('number', 'start_date', 'end_date')


admin.site.register(Knesset, KnessetAdmin)
