# encoding: utf-8
from django.db import models
import logging

logger = logging.getLogger("open-knesset.laws.models")


class GovLegislationCommitteeDecision(models.Model):
    class Meta:
        app_label = 'laws'

    title = models.CharField(max_length=1000)
    subtitle = models.TextField(null=True, blank=True)
    text = models.TextField(blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    source_url = models.URLField(max_length=1024, null=True, blank=True)
    bill = models.ForeignKey('Bill', blank=True, null=True, related_name='gov_decisions')
    stand = models.IntegerField(blank=True, null=True)
    number = models.IntegerField(blank=True, null=True)

    def __unicode__(self):
        return u"%s" % self.title

    def get_absolute_url(self):
        return self.bill.get_absolute_url()
