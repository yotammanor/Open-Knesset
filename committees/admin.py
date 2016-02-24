from django.contrib.contenttypes import generic
from django.contrib.contenttypes.generic import GenericTabularInline
from django.db.models import Q
from django.contrib import admin
from video.models import Video
from models import Committee, CommitteeMeeting, Topic
from links.models import Link
from django.utils.translation import ugettext_lazy as _


class CommitteeRelatedVideosInline(generic.GenericTabularInline):
    model = Video
    ct_fk_field = 'object_pk'
    can_delete = False
    fields = ['title', 'description', 'embed_link', 'group', 'hide']
    ordering = ['group', '-published']
    readonly_fields = ['title', 'description', 'embed_link', 'group']
    extra = 0

    def queryset(self, request):
        qs = super(CommitteeRelatedVideosInline, self).queryset(request)
        qs = qs.filter(Q(hide=False) | Q(hide=None))
        return qs


class CommitteeAdmin(admin.ModelAdmin):
    ordering = ('name',)
    filter_horizontal = ('members', 'chairpersons', 'replacements')
    inlines = (CommitteeRelatedVideosInline,)


admin.site.register(Committee, CommitteeAdmin)


class MissingProtocolListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('Missing Protocol')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'is_missing_protocol'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('missing_protocol', _('Has Missing Protocol')),
            ('has_protocol', _('Has Protocol')),
            # ('90s', _('in the nineties')),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.
        if self.value() == 'missing_protocol':
            return queryset.filter(parts=None)
        elif self.value() == 'has_protocol':
            return queryset.exclude(parts=None)
        else:
            return queryset


class CommitteeMeetingAdmin(admin.ModelAdmin):
    ordering = ('-date',)
    list_display = ('__unicode__', 'date', 'committee_type', 'protocol_parts')
    list_filter = ('committee', 'committee__type', MissingProtocolListFilter)

    def committee_type(self, obj):
        return obj.committee.type

    def protocol_parts(self, obj):
        return obj.parts.all().count()


admin.site.register(CommitteeMeeting, CommitteeMeetingAdmin)


class LinksTable(GenericTabularInline):
    model = Link
    ct_field = 'content_type'
    ct_fk_field = 'object_pk'


class TopicAdmin(admin.ModelAdmin):
    ordering = ('-created',)
    list_select_related = True
    exclude = ('meetings',)
    inlines = [
        LinksTable,
    ]


admin.site.register(Topic, TopicAdmin)
