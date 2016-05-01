# encoding: utf-8
from django.db import models

from laws.enums import VOTE_ACTION_TYPE_CHOICES
import logging

logger = logging.getLogger("open-knesset.laws.models")


class VoteAction(models.Model):
    class Meta:
        app_label = 'laws'

    type = models.CharField(max_length=10, choices=VOTE_ACTION_TYPE_CHOICES)
    member = models.ForeignKey('mks.Member')
    party = models.ForeignKey('mks.Party')
    vote = models.ForeignKey('Vote', related_name='actions')
    against_party = models.BooleanField(default=False)
    against_coalition = models.BooleanField(default=False)
    against_opposition = models.BooleanField(default=False)
    against_own_bill = models.BooleanField(default=False)

    def __unicode__(self):
        return u"{} {} {}".format(self.member.name, self.type, self.vote.title)

    def save(self, **kwargs):
        if not self.party_id:
            party = self.member.party_at(self.vote.time.date())
            if party:
                self.party_id = party.id
        super(VoteAction, self).save(**kwargs)
