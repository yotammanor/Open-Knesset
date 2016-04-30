# encoding: utf-8
from django.db import models
from django.utils.translation import ugettext_lazy as _

from laws.models.vote_action import VoteAction
import logging

logger = logging.getLogger("open-knesset.laws.models")


class CandidateListVotingStatistics(models.Model):
    # TODO: why is this a django model? could be method on CandidateList or a projection class
    class Meta:
        app_label = 'laws'

    candidates_list = models.OneToOneField('polyorg.CandidateList', related_name='voting_statistics')

    def votes_against_party_count(self):
        return VoteAction.objects.filter(member__id__in=self.candidates_list.member_ids, against_party=True).count()

    def votes_count(self):
        return VoteAction.objects.filter(member__id__in=self.candidates_list.member_ids).exclude(type='no-vote').count()

    def votes_per_seat(self):
        return round(float(self.votes_count()) / len(self.candidates_list.member_ids))

    def discipline(self):
        total_votes = self.votes_count()
        if total_votes:
            votes_against_party = self.votes_against_party_count()
            return round(100.0 * (total_votes - votes_against_party) / total_votes, 1)
        return _('N/A')
