# encoding: utf-8
import re
import logging
import sys
import traceback
from datetime import datetime, timedelta, date
from django.db import models
from django.db.models.query_utils import Q
from django.utils.translation import ugettext_lazy as _, ugettext
from django.utils.text import Truncator
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User
from django.core.cache import cache
from django.utils.functional import cached_property
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from tagging.models import Tag, TaggedItem
from djangoratings.fields import RatingField
from annotatetext.models import Annotation

from committees.enums import CommitteeTypes
from events.models import Event
from links.models import Link
from plenum.create_protocol_parts import create_plenum_protocol_parts
from mks.models import Knesset
from lobbyists.models import LobbyistHistory, LobbyistCorporation
from itertools import groupby
from hebrew_numbers import gematria_to_int
from mks.utils import get_all_mk_names
from knesset_data.protocols.committee import \
    CommitteeMeetingProtocol as KnessetDataCommitteeMeetingProtocol
from knesset_data.protocols.exceptions import AntiwordException

COMMITTEE_PROTOCOL_PAGINATE_BY = 120

logger = logging.getLogger("open-knesset.committees.models")


class Committee(models.Model):
    name = models.CharField(max_length=256)
    # comma separated list of names used as name aliases for harvesting
    aliases = models.TextField(null=True, blank=True)
    members = models.ManyToManyField('mks.Member', related_name='committees',
                                     blank=True)
    chairpersons = models.ManyToManyField('mks.Member',
                                          related_name='chaired_committees',
                                          blank=True)
    replacements = models.ManyToManyField('mks.Member',
                                          related_name='replacing_in_committees',
                                          blank=True)
    events = generic.GenericRelation(Event, content_type_field="which_type",
                                     object_id_field="which_pk")
    description = models.TextField(null=True, blank=True)
    portal_knesset_broadcasts_url = models.URLField(max_length=1000,
                                                    blank=True)
    type = models.CharField(max_length=10, default=CommitteeTypes.committee,
                            choices=CommitteeTypes.as_choices(),
                            db_index=True)
    hide = models.BooleanField(default=False)
    # Deprecated? In use? does not look in use
    protocol_not_published = models.BooleanField(default=False)
    knesset_id = models.IntegerField(null=True, blank=True)
    knesset_type_id = models.IntegerField(null=True, blank=True)
    knesset_parent_id = models.IntegerField(null=True, blank=True)
    # Deprecated? In use? does not look
    last_scrape_time = models.DateTimeField(null=True, blank=True)
    name_eng = models.CharField(max_length=256, null=True, blank=True)
    name_arb = models.CharField(max_length=256, null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    knesset_description = models.TextField(null=True, blank=True)
    knesset_description_eng = models.TextField(null=True, blank=True)
    knesset_description_arb = models.TextField(null=True, blank=True)
    knesset_note = models.TextField(null=True, blank=True)
    knesset_note_eng = models.TextField(null=True, blank=True)
    knesset_portal_link = models.TextField(null=True, blank=True)

    @property
    def gender_presence(self):
        # returns a touple of (female_presence, male_presence
        r = {'F': 0, 'M': 0}
        for cm in self.meetings.all():
            try:
                results = groupby(cm.mks_attended.all(), lambda mk: mk.gender)
            except ValueError:
                continue
            for i in results:
                key, count = i[0], len(list(i[1]))
                r[key] += count
        return r['F'], r['M']

    def __unicode__(self):
        if self.type == 'plenum':
            return "%s" % ugettext('Plenum')
        else:
            return "%s" % self.name

    @models.permalink
    def get_absolute_url(self):
        if self.type == 'plenum':
            return 'plenum', []
        else:
            return 'committee-detail', [str(self.id)]

    @property
    def annotations(self):
        protocol_part_tn = ProtocolPart._meta.db_table
        meeting_tn = CommitteeMeeting._meta.db_table
        committee_tn = Committee._meta.db_table
        annotation_tn = Annotation._meta.db_table
        protocol_part_ct = ContentType.objects.get_for_model(ProtocolPart)
        ret = Annotation.objects.select_related().filter(
            content_type=protocol_part_ct)
        return ret.extra(tables=[protocol_part_tn,
                                 meeting_tn, committee_tn],
                         where=["%s.object_id=%s.id" % (
                             annotation_tn, protocol_part_tn),
                                "%s.meeting_id=%s.id" % (
                                    protocol_part_tn, meeting_tn),
                                "%s.committee_id=%%s" % meeting_tn],
                         params=[self.id]).distinct()

    def members_by_name(self, ids=None, current_only=False):
        """Return a queryset of all members, sorted by their name.
        """
        members = self.members_extended(current_only=current_only, ids=ids)
        return members.order_by('name')

    def members_by_presence(self, ids=None, from_date=None,
                            current_only=False):
        """Returns a list of members with computed presence percentage.
        If ids is not provided, this will return committee members. if ids is
        provided, this will return presence data for the given members.
        """

        members = self.members_extended(current_only, ids)

        if from_date is not None:
            include_this_year = False
        else:
            # this is compatibility mode to support existing views
            include_this_year = True

        def count_percentage(res_set, total_count):
            return (100 * res_set.count() / total_count) if total_count else 0

        def filter_this_year(res_set):
            year_start = date.today().replace(month=1, day=1)
            return res_set.filter(date__gte=year_start)

        d = Knesset.objects.current_knesset().start_date if from_date is None \
            else from_date
        meetings_with_mks = self.meetings.filter(
            mks_attended__isnull=False).distinct()
        all_meet_count = meetings_with_mks.filter(
            date__gte=d).count()
        year_meet_count = filter_this_year(
            meetings_with_mks).count() if include_this_year else None
        for m in members:
            all_member_meetings = m.committee_meetings.filter(committee=self,
                                                              date__gte=d)
            m.meetings_percentage = count_percentage(all_member_meetings,
                                                     all_meet_count)
            if include_this_year:
                year_member_meetings = filter_this_year(all_member_meetings)
                m.meetings_percentage_year = count_percentage(
                    year_member_meetings,
                    year_meet_count)

        return sorted(members, key=lambda x: x.meetings_percentage,
                      reverse=True)

    def members_extended(self, current_only=False, ids=None):
        '''
        a queryset of Members who are part of the committee, as members,
        chairpersons or replacements.
        '''
        query = Q(committees=self) | Q(chaired_committees=self) | Q(
            replacing_in_committees=self)
        qs = Member.objects.filter(query).distinct()
        if ids is not None:
            return qs.filter(id__in=ids)
        if current_only:
            return qs.filter(is_current=True)
        return qs

    def recent_meetings(self, limit=10, do_limit=True):
        relevant_meetings = self.meetings.all().order_by('-date')
        if do_limit:
            more_available = relevant_meetings.count() > limit
            return relevant_meetings[:limit], more_available
        else:
            return relevant_meetings

    def future_meetings(self, limit=10, do_limit=True):
        current_date = datetime.now()
        relevant_events = self.events.filter(when__gt=current_date).order_by(
            'when')
        if do_limit:
            more_available = relevant_events.count() > limit
            return relevant_events[:limit], more_available
        else:
            return relevant_events

    def protocol_not_yet_published_meetings(self, end_date, limit=10,
                                            do_limit=True):
        start_date = self.meetings.all().order_by(
            '-date').first().date + timedelta(days=1) \
            if self.meetings.count() > 0 \
            else datetime.now()
        relevant_events = self.events.filter(when__gt=start_date,
                                             when__lte=end_date).order_by(
            '-when')

        if do_limit:
            more_available = relevant_events.count() > limit
            return relevant_events[:limit], more_available
        else:
            return relevant_events


not_header = re.compile(
    r'(^אני )|((אלה|אלו|יבוא|מאלה|ייאמר|אומר|אומרת|נאמר|כך|הבאים|הבאות):$)|(\(.\))|(\(\d+\))|(\d\.)'.decode(
        'utf8'))


def legitimate_header(line):
    """Returns true if 'line' looks like something should be a protocol part header"""
    if re.match(r'^\<.*\>\W*$', line):  # this is a <...> line.
        return True
    if not (line.strip().endswith(':')) or len(line) > 50 or not_header.search(
            line):
        return False
    return True


class CommitteeMeetingManager(models.Manager):
    def filter_and_order(self, *args, **kwargs):
        qs = self.all()
        # In dealing with 'tagged' we use an ugly workaround for the fact that generic relations
        # don't work as expected with annotations.
        # please read http://code.djangoproject.com/ticket/10461 before trying to change this code
        if kwargs.get('tagged'):
            if kwargs['tagged'] == ['false']:
                qs = qs.exclude(tagged_items__isnull=False)
            elif kwargs['tagged'] != ['all']:
                qs = qs.filter(tagged_items__tag__name__in=kwargs['tagged'])

        if kwargs.get('to_date'):
            qs = qs.filter(time__lte=kwargs['to_date'] + timedelta(days=1))

        if kwargs.get('from_date'):
            qs = qs.filter(time__gte=kwargs['from_date'])

        return qs.select_related('committee')


class CommitteesMeetingsOnlyManager(CommitteeMeetingManager):
    def get_queryset(self):
        return super(CommitteesMeetingsOnlyManager,
                     self).get_queryset().exclude(
            committee__type=CommitteeTypes.plenum)


class CommitteeMeeting(models.Model):
    committee = models.ForeignKey(Committee, related_name='meetings')
    date_string = models.CharField(max_length=256)
    date = models.DateField(db_index=True)
    mks_attended = models.ManyToManyField('mks.Member',
                                          related_name='committee_meetings')
    votes_mentioned = models.ManyToManyField('laws.Vote',
                                             related_name='committee_meetings',
                                             blank=True)
    protocol_text = models.TextField(null=True, blank=True)
    # the date the protocol text was last downloaded and saved
    protocol_text_update_date = models.DateField(blank=True, null=True)
    # the date the protocol parts were last parsed and saved
    protocol_parts_update_date = models.DateField(blank=True, null=True)
    topics = models.TextField(null=True, blank=True)
    src_url = models.URLField(max_length=1024, null=True, blank=True)
    tagged_items = generic.GenericRelation(TaggedItem,
                                           object_id_field="object_id",
                                           content_type_field="content_type")
    lobbyists_mentioned = models.ManyToManyField('lobbyists.Lobbyist',
                                                 related_name='committee_meetings',
                                                 blank=True)
    lobbyist_corporations_mentioned = models.ManyToManyField(
        'lobbyists.LobbyistCorporation',
        related_name='committee_meetings', blank=True)
    datetime = models.DateTimeField(db_index=True, null=True, blank=True)
    knesset_id = models.IntegerField(null=True, blank=True)

    objects = CommitteeMeetingManager()

    committees_only = CommitteesMeetingsOnlyManager()

    class Meta:
        ordering = ('-date',)
        verbose_name = _('Committee Meeting')
        verbose_name_plural = _('Committee Meetings')

    def title(self):
        truncator = Truncator(self.topics)
        return truncator.words(12)

    def __unicode__(self):
        cn = cache.get('committee_%d_name' % self.committee_id)
        if not cn:
            if self.committee.type == 'plenum':
                cn = 'Plenum'
            else:
                cn = unicode(self.committee)
            cache.set('committee_%d_name' % self.committee_id,
                      cn,
                      settings.LONG_CACHE_TIME)
        if cn == 'Plenum':
            return (u"%s" % (self.title())).replace("&nbsp;", u"\u00A0")
        else:
            return (u"%s - %s" % (cn,
                                  self.title())).replace("&nbsp;", u"\u00A0")

    @models.permalink
    def get_absolute_url(self):
        if self.committee.type == 'plenum':
            return 'plenum-meeting', [str(self.id)]
        else:
            return 'committee-meeting', [str(self.id)]

    def _get_tags(self):
        tags = Tag.objects.get_for_object(self)
        return tags

    def _set_tags(self, tag_list):
        Tag.objects.update_tags(self, tag_list)

    tags = property(_get_tags, _set_tags)

    def save(self, **kwargs):
        super(CommitteeMeeting, self).save(**kwargs)

    def create_protocol_parts(self, delete_existing=False, mks=None,
                              mk_names=None):
        """ Create protocol parts from this instance's protocol_text
            Optionally, delete existing parts.
            If the meeting already has parts, and you don't ask to
            delete them, a ValidationError will be thrown, because
            it doesn't make sense to create the parts again.
        """
        logger.debug('create_protocol_parts %s' % delete_existing)
        if delete_existing:
            ppct = ContentType.objects.get_for_model(ProtocolPart)
            annotations = Annotation.objects.filter(content_type=ppct,
                                                    object_id__in=self.parts.all)
            logger.debug(
                'deleting %d annotations, because I was asked to delete the relevant protocol parts on cm.id=%d' % (
                    annotations.count(), self.id))
            annotations.delete()
            self.parts.all().delete()
        else:
            if self.parts.count():
                raise ValidationError(
                    'CommitteeMeeting already has parts. delete them if you want to run create_protocol_parts again.')
        if not self.protocol_text:  # sometimes there are empty protocols
            return  # then we don't need to do anything here.
        if self.committee.type == 'plenum':
            create_plenum_protocol_parts(self, mks=mks, mk_names=mk_names)
            return
        else:
            def get_protocol_part(i, part):
                logger.debug('creating protocol part %s' % i)
                return ProtocolPart(meeting=self, order=i, header=part.header,
                                    body=part.body)

            with KnessetDataCommitteeMeetingProtocol.get_from_text(
                    self.protocol_text) as protocol:
                # TODO: use bulk_create (I had a strange error when using it)
                # ProtocolPart.objects.bulk_create(
                # for testing, you could just save one part:
                # get_protocol_part(1, protocol.parts[0]).save()
                list([
                         get_protocol_part(i, part).save()
                         for i, part
                         in
                         zip(range(1, len(protocol.parts) + 1), protocol.parts)
                         ])
            self.protocol_parts_update_date = datetime.now()
            self.save()

    def redownload_protocol(self):
        if self.committee.type == 'plenum':
            # TODO: Using managment command this way is an antipattern, a common service should be extracted and used
            from plenum.management.commands.parse_plenum_protocols_subcommands.download import \
                download_for_existing_meeting
            download_for_existing_meeting(self)
        else:
            try:
                with KnessetDataCommitteeMeetingProtocol.get_from_url(
                        self.src_url) as protocol:
                    self.protocol_text = protocol.text
                    self.protocol_text_update_date = datetime.now()
                    self.save()
            except AntiwordException as e:
                logger.error(
                    e.message,
                    exc_info=True,
                    extra={
                        'output': e.output
                    }
                )
                raise e

    def reparse_protocol(self, redownload=True, mks=None, mk_names=None):
        if redownload: self.redownload_protocol()
        if self.committee.type == 'plenum':
            # See above
            from plenum.management.commands.parse_plenum_protocols_subcommands.parse import \
                parse_for_existing_meeting
            parse_for_existing_meeting(self)
        else:
            self.create_protocol_parts(delete_existing=True)
            self.find_attending_members(mks, mk_names)

    def update_from_dataservice(self, dataservice_object=None):
        from committees.management.commands.scrape_committee_meetings import \
            Command as ScrapeCommitteeMeetingCommand
        from knesset_data.dataservice.committees import \
            CommitteeMeeting as DataserviceCommitteeMeeting
        if dataservice_object is None:
            ds_meetings = [
                ds_meeting for ds_meeting
                in DataserviceCommitteeMeeting.get(self.committee.knesset_id,
                                                   self.date - timedelta(
                                                       days=1),
                                                   self.date + timedelta(
                                                       days=1))
                if str(ds_meeting.id) == str(self.knesset_id)
                ]
            if len(ds_meetings) != 1:
                raise Exception(
                    'could not found corresponding dataservice meeting')
            dataservice_object = ds_meetings[0]
        meeting_transformed = ScrapeCommitteeMeetingCommand().get_committee_meeting_fields_from_dataservice(
            dataservice_object)
        [setattr(self, k, v) for k, v in meeting_transformed.iteritems()]
        self.save()

    @property
    def plenum_meeting_number(self):
        res = None
        parts = self.parts.filter(body__contains=u'ישיבה')
        if parts.count() > 0:
            r = re.search(u'ישיבה (.*)$', self.parts.filter(
                body__contains=u'ישיבה').first().body)
            if r:
                res = gematria_to_int(r.groups()[0])
        return res

    def plenum_link_votes(self):
        from laws.models import Vote
        if self.plenum_meeting_number:
            for vote in Vote.objects.filter(
                    meeting_number=self.plenum_meeting_number):
                for part in self.parts.filter(header__contains=u'הצבעה'):
                    r = re.search(r' (\d+)$', part.header)
                    if r and vote.vote_number == int(r.groups()[0]):
                        url = part.get_absolute_url()
                        Link.objects.get_or_create(
                            object_pk=vote.pk,
                            content_type=ContentType.objects.get_for_model(
                                Vote),
                            url=url,
                            defaults={
                                'title': u'לדיון בישיבת המליאה'
                            }
                        )

    def get_bg_material(self):
        """
            returns any background material for the committee meeting, or [] if none
        """
        import urllib2
        from BeautifulSoup import BeautifulSoup

        time = re.findall(r'(\d\d:\d\d)', self.date_string)[0]
        date = self.date.strftime('%d/%m/%Y')
        cid = self.committee.knesset_id
        if cid is None:  # missing this committee knesset id
            return []  # can't get bg material

        url = 'http://www.knesset.gov.il/agenda/heb/material.asp?c=%s&t=%s&d=%s' % (
            cid, time, date)
        data = urllib2.urlopen(url)
        bg_links = []
        if data.url == url:  # if no bg material exists we get redirected to a different page
            bgdata = BeautifulSoup(data.read()).findAll('a')

            for i in bgdata:
                bg_links.append(
                    {'url': 'http://www.knesset.gov.il' + i['href'],
                     'title': i.string})

        return bg_links

    @property
    def bg_material(self):
        return Link.objects.filter(object_pk=self.id,
                                   content_type=ContentType.objects.get_for_model(
                                       CommitteeMeeting).id)

    def find_attending_members(self, mks=None, mk_names=None):
        logger.debug('find_attending_members')
        if mks is None and mk_names is None:
            logger.debug('get_all_mk_names')
            mks, mk_names = get_all_mk_names()
        with KnessetDataCommitteeMeetingProtocol.get_from_text(
                self.protocol_text) as protocol:
            attended_mk_names = protocol.find_attending_members(mk_names)
            for name in attended_mk_names:
                i = mk_names.index(name)
                if not mks[i].party_at(
                        self.date):  # not a member at time of this meeting?
                    continue  # then don't search for this MK.
                self.mks_attended.add(mks[i])
        logger.debug('meeting %d now has %d attending members' % (
            self.id,
            self.mks_attended.count()))

    @cached_property
    def main_lobbyist_corporations_mentioned(self):
        ret = []
        for corporation in self.lobbyist_corporations_mentioned.all():
            main_corporation = corporation.main_corporation
            if main_corporation not in ret:
                ret.append(main_corporation)
        for lobbyist in self.main_lobbyists_mentioned:
            latest_corporation = lobbyist.cached_data.get('latest_corporation')
            if latest_corporation:
                corporation = LobbyistCorporation.objects.get(
                    id=latest_corporation['id'])
                if corporation not in ret and corporation.main_corporation == corporation:
                    ret.append(corporation)
        return ret

    @cached_property
    def main_lobbyists_mentioned(self):
        return self.lobbyists_mentioned.all()


class ProtocolPartManager(models.Manager):
    def list(self):
        return self.order_by("order")


class ProtocolPart(models.Model):
    meeting = models.ForeignKey(CommitteeMeeting, related_name='parts')
    order = models.IntegerField()
    header = models.TextField(blank=True, null=True)
    body = models.TextField(blank=True, null=True)
    speaker = models.ForeignKey('persons.Person', blank=True, null=True,
                                related_name='protocol_parts')
    objects = ProtocolPartManager()
    type = models.TextField(blank=True, null=True, max_length=20)

    annotatable = True

    class Meta:
        ordering = ('order', 'id')

    def get_absolute_url(self):
        if self.order == 1:
            return self.meeting.get_absolute_url()
        else:
            page_num = 1 + (self.order - 1) / COMMITTEE_PROTOCOL_PAGINATE_BY
            if page_num == 1:  # this is on first page
                return "%s#speech-%d-%d" % (self.meeting.get_absolute_url(),
                                            self.meeting.id, self.order)
            else:
                return "%s?page=%d#speech-%d-%d" % (
                    self.meeting.get_absolute_url(),
                    page_num,
                    self.meeting.id, self.order)

    def __unicode__(self):
        return "%s %s: %s" % (self.meeting.committee.name, self.header,
                              self.body)


TOPIC_PUBLISHED, TOPIC_FLAGGED, TOPIC_REJECTED, \
TOPIC_ACCEPTED, TOPIC_APPEAL, TOPIC_DELETED = range(6)
PUBLIC_TOPIC_STATUS = (TOPIC_PUBLISHED, TOPIC_ACCEPTED)


class TopicManager(models.Manager):
    ''' '''
    get_public = lambda self: self.filter(status__in=PUBLIC_TOPIC_STATUS)

    by_rank = lambda self: self.extra(select={
        'rank': '((100/%s*rating_score/(1+rating_votes+%s))+100)/2' % (
            Topic.rating.range, Topic.rating.weight)
    }).order_by('-rank')

    def summary(self, order='-rank'):
        return self.filter(status__in=PUBLIC_TOPIC_STATUS).extra(select={
            'rank': '((100/%s*rating_score/(1+rating_votes+%s))+100)/2' % (
                Topic.rating.range, Topic.rating.weight)
        }).order_by(order)
        # TODO: rinse it so this will work
        return self.get_public().by_rank()


class Topic(models.Model):
    '''
        Topic is used to hold the latest event about a topic and a committee

        Fields:
            title - the title
            description - its description
            created - the time a topic was first connected to a committee
            modified - last time the status or the message was updated
            editor - the user that entered the data
            status - the current status
            log - a text log that keeps text messages for status changes
            committees - defined using a many to many from `Committee`
    '''

    creator = models.ForeignKey(User)
    editors = models.ManyToManyField(User, related_name='editing_topics',
                                     null=True, blank=True)
    title = models.CharField(max_length=256,
                             verbose_name=_('Title'))
    description = models.TextField(blank=True,
                                   verbose_name=_('Description'))
    status = models.IntegerField(choices=(
        (TOPIC_PUBLISHED, _('published')),
        (TOPIC_FLAGGED, _('flagged')),
        (TOPIC_REJECTED, _('rejected')),
        (TOPIC_ACCEPTED, _('accepted')),
        (TOPIC_APPEAL, _('appeal')),
        (TOPIC_DELETED, _('deleted')),
    ), default=TOPIC_PUBLISHED)
    rating = RatingField(range=7, can_change_vote=True, allow_delete=True)
    links = generic.GenericRelation(Link, content_type_field="content_type",
                                    object_id_field="object_pk")
    events = generic.GenericRelation(Event, content_type_field="which_type",
                                     object_id_field="which_pk")
    # no related name as `topics` is already defined in CommitteeMeeting as text
    committees = models.ManyToManyField(Committee,
                                        verbose_name=_('Committees'))
    meetings = models.ManyToManyField(CommitteeMeeting, null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    log = models.TextField(default="", blank=True)

    class Meta:
        verbose_name = _('Topic')
        verbose_name_plural = _('Topics')

    @models.permalink
    def get_absolute_url(self):
        return ('topic-detail', [str(self.id)])

    def __unicode__(self):
        return "%s" % self.title

    objects = TopicManager()

    def set_status(self, status, message=''):
        self.status = status
        self.log = '\n'.join(
            (u'%s: %s' % (self.get_status_display(), datetime.now()),
             u'\t%s' % message,
             self.log,)
        )
        self.save()

    def can_edit(self, user):
        return user.is_superuser or user == self.creator or \
               user in self.editors.all()


from listeners import *
