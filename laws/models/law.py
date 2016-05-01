# encoding: utf-8
from django.db import models
import logging
logger = logging.getLogger("open-knesset.laws.models")

class Law(models.Model):
    class Meta:
        app_label = 'laws'

    title = models.CharField(max_length=1000)
    merged_into = models.ForeignKey('Law', related_name='duplicates', blank=True, null=True)

    def __unicode__(self):
        return self.title

    def merge(self, another_law):
        """
        Merges another_law into this one.
        Move all pointers from another_law to self,
        Then mark another_law as deleted by setting its merged_into field to self.
        """
        if another_law is self:
            return  # don't accidentally delete myself by trying to merge.
        for pp in another_law.laws_privateproposal_related.all():
            pp.law = self
            pp.save()
        for kp in another_law.laws_knessetproposal_related.all():
            kp.law = self
            kp.save()
        # TODO: is it missing a type of proposals? government?
        for bill in another_law.bills.all():
            bill.law = self
            bill.save()
        another_law.merged_into = self
        another_law.save()
