# encoding: utf-8
from django.db import models
from django.utils.translation import ugettext_lazy as _

from laws.models.vote_action import VoteAction
from mks.models import Knesset
import logging

logger = logging.getLogger("open-knesset.laws.models")


class PartyVotingStatistics(models.Model):
    # TODO: why is this a django model? could be method on Party or a projection class
    class Meta:
        app_label = 'laws'

    party = models.OneToOneField('mks.Party', related_name='voting_statistics')

    def votes_against_party_count(self):
        d = Knesset.objects.current_knesset().start_date
        return VoteAction.objects.filter(
            vote__time__gt=d,
            member__current_party=self.party,
            against_party=True).count()

    def votes_count(self):
        d = Knesset.objects.current_knesset().start_date
        return VoteAction.objects.filter(
            member__current_party=self.party,
            vote__time__gt=d).exclude(type='no-vote').count()

    def votes_per_seat(self):
        return round(float(self.votes_count()) / self.party.number_of_seats, 1)

    def discipline(self):
        total_votes = self.votes_count()
        if total_votes:
            votes_against_party = self.votes_against_party_count()
            return round(100.0 * (total_votes - votes_against_party) /
                         total_votes, 1)
        return _('N/A')

    def coalition_discipline(self):  # if party is in opposition this actually
        # returns opposition_discipline
        d = Knesset.objects.current_knesset().start_date
        total_votes = self.votes_count()
        if total_votes:
            if self.party.is_coalition:
                votes_against_coalition = VoteAction.objects.filter(
                    vote__time__gt=d,
                    member__current_party=self.party,
                    against_coalition=True).count()
            else:
                votes_against_coalition = VoteAction.objects.filter(
                    vote__time__gt=d,
                    member__current_party=self.party,
                    against_opposition=True).count()
            return round(100.0 * (total_votes - votes_against_coalition) /
                         total_votes, 1)
        return _('N/A')

    def __unicode__(self):
        return "{}".format(self.party.name)
