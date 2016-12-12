# encoding: utf-8
from django.conf import settings
from django.core.cache import cache
from django.db import models

from laws.models.vote_action import VoteAction
import logging

logger = logging.getLogger("open-knesset.laws.models")


class MemberVotingStatistics(models.Model):
    # TODO: why is this a django model? could be method on member or a projection class
    class Meta:
        app_label = 'laws'

    member = models.OneToOneField('mks.Member', related_name='voting_statistics')

    def votes_against_party_count(self, from_date=None):
        if from_date:
            return VoteAction.objects.filter(member=self.member, against_party=True, vote__time__gt=from_date).count()
        return VoteAction.objects.filter(member=self.member, against_party=True).count()

    def votes_count(self, from_date=None):
        if from_date:
            return VoteAction.objects.filter(member=self.member, vote__time__gt=from_date).exclude(
                type='no-vote').count()
        vc = cache.get('votes_count_%d' % self.member.id)
        if not vc:
            vc = VoteAction.objects.filter(member=self.member).exclude(type='no-vote').count()
            cache.set('votes_count_%d' % self.member.id, vc, settings.LONG_CACHE_TIME)
        return vc

    def average_votes_per_month(self):
        if hasattr(self, '_average_votes_per_month'):
            return self._average_votes_per_month
        st = self.member.service_time()
        self._average_votes_per_month = (30.0 * self.votes_count() / st) if st else 0
        return self._average_votes_per_month

    def discipline(self, from_date=None):
        total_votes = self.votes_count(from_date)
        if total_votes <= 3:  # not enough data
            return None
        votes_against_party = self.votes_against_party_count(from_date)
        return round(100.0 * (total_votes - votes_against_party) / total_votes, 1)

    def coalition_discipline(self,
                             from_date=None):  # if party is in opposition this actually returns opposition_discipline
        total_votes = self.votes_count(from_date)
        if total_votes <= 3:  # not enough data
            return None
        if self.member.current_party.is_coalition:
            v = VoteAction.objects.filter(member=self.member, against_coalition=True)
        else:
            v = VoteAction.objects.filter(member=self.member, against_opposition=True)
        if from_date:
            v = v.filter(vote__time__gt=from_date)
        votes_against_coalition = v.count()
        return round(100.0 * (total_votes - votes_against_coalition) / total_votes, 1)

    def __unicode__(self):
        return "{}".format(self.member.name)
