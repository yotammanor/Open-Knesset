# encoding: utf-8
from django.contrib.auth.models import User
from django.db import models
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from knesset.utils import get_thousands_string
import logging
logger = logging.getLogger("open-knesset.laws.models")


class BillBudgetEstimation(models.Model):
    class Meta:
        app_label = 'laws'
        unique_together = (("bill", "estimator"),)

    bill = models.ForeignKey("laws.Bill", related_name="budget_ests")
    # costs are in thousands NIS
    one_time_gov = models.IntegerField(blank=True, null=True)
    yearly_gov = models.IntegerField(blank=True, null=True)
    one_time_ext = models.IntegerField(blank=True, null=True)
    yearly_ext = models.IntegerField(blank=True, null=True)
    estimator = models.ForeignKey(User, related_name="budget_ests", blank=True, null=True)
    time = models.DateTimeField(auto_now=True)
    summary = models.TextField(null=True, blank=True)

    def as_p(self):
        return mark_safe(("<p><label><b>%s</b></label> %s</p>\n" * 7) % \
                         (
                             # leave this; the lazy translator does not evaluate for some reason.
                             _('Estimation of').format(),
                             "<b>%s</b>" % self.estimator.username,
                             _('Estimated on:').format(),
                             self.time,
                             _('One-time costs to government:').format(),
                             get_thousands_string(self.one_time_gov),
                             _('Yearly costs to government:').format(),
                             get_thousands_string(self.yearly_gov),
                             _('One-time costs to external bodies:').format(),
                             get_thousands_string(self.one_time_ext),
                             _('Yearly costs to external bodies:').format(),
                             get_thousands_string(self.yearly_ext),
                             _('Summary of the estimation:').format(),
                             escape(self.summary if self.summary else "", )))