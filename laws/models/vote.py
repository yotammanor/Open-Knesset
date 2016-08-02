# encoding: utf-8
import sys
import traceback
from datetime import timedelta

from django.contrib.contenttypes import generic
from django.db import models
from django.utils.translation import ugettext_lazy as _
from tagging.models import TaggedItem, Tag

from laws import constants
from laws.models.bill import Bill
from laws.models.vote_action import VoteAction
from laws.vote_choices import TYPE_CHOICES
from mks.models import Party, Member
from ok_tag.forms import TagForm
from tagvotes.models import TagVote
import logging

logger = logging.getLogger("open-knesset.laws.models")


class VoteManager(models.Manager):
    # TODO: add i18n to the types so we'd have
    #   {'law-approve': _('approve law'), ...
    VOTE_TYPES = {'law-approve': u'אישור החוק', 'second-call': u'קריאה שנייה', 'demurrer': u'הסתייגות',
                  'no-confidence': u'הצעת אי-אמון', 'pass-to-committee': u'להעביר את ',
                  'continuation': u'להחיל דין רציפות'}

    def filter_and_order(self, *args, **kwargs):
        qs = self.all()
        filter_kwargs = {}
        if kwargs.get('vtype') and kwargs['vtype'] != 'all':
            filter_kwargs['title__startswith'] = self.VOTE_TYPES[kwargs['vtype']]

        if filter_kwargs:
            qs = qs.filter(**filter_kwargs)

        # In dealing with 'tagged' we use an ugly workaround for the fact that generic relations
        # don't work as expected with annotations.
        # please read http://code.djangoproject.com/ticket/10461 before trying to change this code
        if kwargs.get('tagged'):
            if kwargs['tagged'] == 'false':
                qs = qs.exclude(tagged_items__isnull=False)
            elif kwargs['tagged'] != 'all':
                qs = qs.filter(tagged_items__tag__name=kwargs['tagged'])

        if kwargs.get('to_date'):
            qs = qs.filter(time__lte=kwargs['to_date'] + timedelta(days=1))

        if kwargs.get('from_date'):
            qs = qs.filter(time__gte=kwargs['from_date'])

        exclude_agendas = kwargs.get('exclude_agendas')
        if exclude_agendas:
            # exclude votes that are ascribed to any of the given agendas
            from agendas.models import AgendaVote
            qs = qs.exclude(id__in=AgendaVote.objects.filter(
                agenda__in=exclude_agendas).values('vote__id'))

        if 'order' in kwargs:
            if kwargs['order'] == 'controversy':
                qs = qs.order_by('-controversy')
            if kwargs['order'] == 'against-party':
                qs = qs.order_by('-against_party')
            if kwargs['order'] == 'votes':
                qs = qs.order_by('-votes_count')

        if kwargs.get('exclude_ascribed', False):  # exclude votes ascribed to
            # any bill.
            qs = qs.exclude(bills_pre_votes__isnull=False).exclude(
                bills_first__isnull=False).exclude(bill_approved__isnull=False)
        return qs


class Vote(models.Model):
    meeting_number = models.IntegerField(null=True, blank=True)
    vote_number = models.IntegerField(null=True, blank=True)
    src_id = models.IntegerField(null=True, blank=True)
    src_url = models.URLField(max_length=1024, null=True, blank=True)
    title = models.CharField(max_length=1000)
    vote_type = models.CharField(max_length=32, choices=TYPE_CHOICES,
                                 blank=True)
    time = models.DateTimeField(db_index=True)
    time_string = models.CharField(max_length=100)
    votes = models.ManyToManyField('mks.Member', related_name='votes', blank=True, through='VoteAction')
    votes_count = models.IntegerField(null=True, blank=True)
    for_votes_count = models.IntegerField(null=True, blank=True)
    against_votes_count = models.IntegerField(null=True, blank=True)
    abstain_votes_count = models.IntegerField(null=True, blank=True)
    importance = models.FloatField(default=0.0)
    controversy = models.IntegerField(null=True, blank=True)
    against_party = models.IntegerField(null=True, blank=True)
    against_coalition = models.IntegerField(null=True, blank=True)
    against_opposition = models.IntegerField(null=True, blank=True)
    against_own_bill = models.IntegerField(null=True, blank=True)
    summary = models.TextField(null=True, blank=True)
    full_text = models.TextField(null=True, blank=True)
    full_text_url = models.URLField(max_length=1024, null=True, blank=True)

    tagged_items = generic.GenericRelation(TaggedItem,
                                           object_id_field="object_id",
                                           content_type_field="content_type")

    objects = VoteManager()

    class Meta:
        app_label = 'laws'
        ordering = ('-time', '-id')
        verbose_name = _('Vote')
        verbose_name_plural = _('Votes')

    def __unicode__(self):
        return "%s (%s)" % (self.title, self.time_string)

    @property
    def passed(self):
        return self.for_votes_count > self.against_votes_count

    def get_voters_id(self, vote_type):
        return VoteAction.objects.filter(vote=self,
                                         type=vote_type).values_list('member__id', flat=True)

    def for_votes(self):
        return self.actions.select_related().filter(type='for')

    def against_votes(self):
        return self.actions.select_related().filter(type='against')

    def abstain_votes(self):
        return self.actions.select_related().filter(type='abstain')

    def against_party_votes(self):
        return self.votes.filter(voteaction__against_party=True)

    def against_coalition_votes(self):
        return self.votes.filter(voteaction__against_coalition=True)

    def against_own_bill_votes(self):
        return self.votes.filter(voteaction__against_own_bill=True)

    def _vote_type(self):
        if type(self.title) == str:
            f = str.decode
        else:  # its already unicode, do nothing
            f = lambda x, y: x
        for vtype, vtype_prefix in VoteManager.VOTE_TYPES.iteritems():
            if f(self.title, 'utf8').startswith(vtype_prefix):
                return vtype
        return ''

    def short_summary(self):
        if self.summary is None:
            return ''
        return self.summary[:60]

    def full_text_link(self):
        if self.full_text_url is None:
            return ''
        return '<a href="{}">link</a>'.format(self.full_text_url)

    full_text_link.allow_tags = True

    def bills(self):
        """Return a list of all bills related to this vote"""
        result = list(self.bills_pre_votes.all())
        result.extend(self.bills_first.all())
        b = Bill.objects.filter(approval_vote=self)
        if b:
            result.extend(b)
        return result

    @models.permalink
    def get_absolute_url(self):
        return ('vote-detail', [str(self.id)])

    def _get_tags(self):
        tags = Tag.objects.get_for_object(self)
        return tags

    def _set_tags(self, tag_list):
        Tag.objects.update_tags(self, tag_list)

    tags = property(_get_tags, _set_tags)

    def tags_with_user_votes(self, user):
        tags = Tag.objects.get_for_object(self)
        for t in tags:
            ti = TaggedItem.objects.filter(tag=t).filter(object_id=self.id)[0]
            t.score = sum(TagVote.objects.filter(tagged_item=ti).values_list('vote', flat=True))
            v = TagVote.objects.filter(tagged_item=ti).filter(user=user)
            if v:
                t.user_score = v[0].vote
            else:
                t.user_score = 0
        return tags.sorted(cmp=lambda x, y: cmp(x.score, y.score))

    def tag_form(self):
        # Ugly hack around import problems
        # from ok_tag.forms import TagForm
        tf = TagForm()
        tf.tags = self.tags
        tf.initial = {'tags': ', '.join([str(t) for t in self.tags])}
        return tf

    def update_vote_properties(self):
        # TODO: this can be heavily optimized. somewhere sometimes..
        party_ids = Party.objects.values_list('id', flat=True)
        d = self.time.date()
        party_is_coalition = dict(zip(
            party_ids,
            [x.is_coalition_at(self.time.date())
             for x in Party.objects.all()]
        ))

        def party_at_or_error(member, vote_date):
            party = member.party_at(vote_date)
            if party:
                return party
            else:
                raise Exception(
                    'could not find which party member %s belonged to during vote %s' % (member.pk, self.pk))

        for_party_ids = [party_at_or_error(va.member, vote_date=d).id for va in self.for_votes()]
        party_for_votes = [sum([x == party_id for x in for_party_ids]) for party_id in party_ids]

        against_party_ids = [party_at_or_error(va.member, vote_date=d).id for va in self.against_votes()]
        party_against_votes = [sum([x == party_id for x in against_party_ids]) for party_id in party_ids]

        party_stands_for = [float(for_votes) > constants.STANDS_FOR_THRESHOLD * (for_votes + against_votes) for (for_votes, against_votes) in
                            zip(party_for_votes, party_against_votes)]
        party_stands_against = [float(against_votes) > constants.STANDS_FOR_THRESHOLD * (for_votes + against_votes) for (for_votes, against_votes) in
                                zip(party_for_votes, party_against_votes)]

        party_stands_for = dict(zip(party_ids, party_stands_for))
        party_stands_against = dict(zip(party_ids, party_stands_against))

        coalition_for_votes = sum([x for (x, y) in zip(party_for_votes, party_ids) if party_is_coalition[y]])
        coalition_against_votes = sum([x for (x, y) in zip(party_against_votes, party_ids) if party_is_coalition[y]])
        opposition_for_votes = sum([x for (x, y) in zip(party_for_votes, party_ids) if not party_is_coalition[y]])
        opposition_against_votes = sum(
            [x for (x, y) in zip(party_against_votes, party_ids) if not party_is_coalition[y]])

        coalition_total_votes = coalition_for_votes + coalition_against_votes
        coalition_stands_for = (
            float(coalition_for_votes) > constants.STANDS_FOR_THRESHOLD * (coalition_total_votes))
        coalition_stands_against = float(coalition_against_votes) > constants.STANDS_FOR_THRESHOLD * (
            coalition_total_votes)
        opposition_total_votes = opposition_for_votes + opposition_against_votes
        opposition_stands_for = float(opposition_for_votes) > constants.STANDS_FOR_THRESHOLD * opposition_total_votes
        opposition_stands_against = float(
            opposition_against_votes) > constants.STANDS_FOR_THRESHOLD * opposition_total_votes

        # a set of all MKs that proposed bills this vote is about.
        proposers = [set(b.proposers.all()) for b in self.bills()]
        if proposers:
            proposers = reduce(lambda x, y: set.union(x, y), proposers)

        against_party_count = 0
        against_coalition_count = 0
        against_opposition_count = 0
        against_own_bill_count = 0
        for va in VoteAction.objects.filter(vote=self):
            va.against_party = False
            va.against_coalition = False
            va.against_opposition = False
            va.against_own_bill = False
            voting_member_party_at_vote = party_at_or_error(va.member, vote_date=d)
            vote_action_member_party_id = voting_member_party_at_vote.id
            if party_stands_for[vote_action_member_party_id] and va.type == 'against':
                va.against_party = True
                against_party_count += 1
            if party_stands_against[vote_action_member_party_id] and va.type == 'for':
                va.against_party = True
                against_party_count += 1
            if voting_member_party_at_vote.is_coalition_at(self.time.date()):
                if (coalition_stands_for and va.type == 'against') or (coalition_stands_against and va.type == 'for'):
                    va.against_coalition = True
                    against_coalition_count += 1
            else:
                if (opposition_stands_for and va.type == 'against') or (opposition_stands_against and va.type == 'for'):
                    va.against_opposition = True
                    against_opposition_count += 1

            if va.member in proposers and va.type == 'against':
                va.against_own_bill = True
                against_own_bill_count += 1

            va.save()

        self.against_party = against_party_count
        self.against_coalition = against_coalition_count
        self.against_opposition = against_opposition_count
        self.against_own_bill = against_own_bill_count
        self.votes_count = VoteAction.objects.filter(vote=self).count()
        self.for_votes_count = VoteAction.objects.filter(vote=self, type='for').count()
        self.against_votes_count = VoteAction.objects.filter(vote=self, type='against').count()
        self.abstain_votes_count = VoteAction.objects.filter(vote=self, type='abstain').count()
        self.controversy = min(self.for_votes_count or 0,
                               self.against_votes_count or 0)
        self.vote_type = self._vote_type()
        self.save()

    def redownload_votes_page(self):
        from simple.management.commands.syncdata import Command as SyncdataCommand
        (page, vote_src_url) = SyncdataCommand().read_votes_page(self.src_id)
        return page

    def update_from_knesset_data(self):
        from knesset_data.html_scrapers.votes import HtmlVote
        resolve_vote_types = {
            'voted for': u'for',
            'voted against': u'against',
            'abstain': u'abstain',
            'did not vote': u'no-vote',
        }
        html_votes = HtmlVote.get_from_vote_id(self.src_id).member_votes
        for vote_type in ['for', 'against', 'abstain']:
            expected_member_ids = [int(member_id) for member_id, member_vote_type in html_votes if
                                   resolve_vote_types[member_vote_type] == vote_type]
            actual_member_ids = [int(member_id) for member_id in
                                 self.actions.filter(type=vote_type).values_list('member_id', flat=True)]
            if len(expected_member_ids) > len(actual_member_ids):
                missing_member_ids = [member_id for member_id in expected_member_ids if
                                      member_id not in actual_member_ids]
                for member_id in missing_member_ids:
                    logger.info('fixing for member id %s' % member_id)
                    vote_action, created = VoteAction.objects.get_or_create(member=Member.objects.get(pk=member_id),
                                                                            vote=self, defaults={'type': vote_type})
                    if created:
                        vote_action.save()
            elif len(expected_member_ids) != len(actual_member_ids):
                raise Exception(
                    'strange mismatch in members, actual has more members then expected, this is unexpected')

    def reparse_members_from_votes_page(self, page=None):
        from simple.management.commands.syncdata import Command as SyncdataCommand
        page = self.redownload_votes_page() if page is None else page
        syncdata = SyncdataCommand()
        results = syncdata.read_member_votes(page, return_ids=True)
        for (voter_id, voter_party, vote) in results:
            try:
                m = Member.objects.get(pk=int(voter_id))
            except:
                exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
                logger.error("%svoter_id = %s",
                             ''.join(traceback.format_exception(exceptionType, exceptionValue, exceptionTraceback)),
                             str(voter_id))
                continue
            va, created = VoteAction.objects.get_or_create(vote=self, member=m,
                                                           defaults={'type': vote, 'party': m.current_party})
            if created:
                va.save()
