from django.utils.translation import ugettext_lazy as _
from django.db.models import Q
from collections import OrderedDict

from laws.enums import BillStages

TYPE_CHOICES = (
    ('all', _('All votes')),
    ('law-approve', _('Law Approvals')),
    ('second-call', _('Second Call')),
    ('demurrer', _('Demurrer')),
    ('no-confidence', _('Motion of no confidence')),
    ('pass-to-committee', _('Pass to committee')),
    ('continuation', _('Continuation')),
)

SIMPLE_TYPE_CHOICES = (
    ('', '---'),
    ('pre vote', _('Pre Vote')),
    ('first vote', _('First Vote')),
    ('approve vote', _('Approval Vote')),
)

TAGGED_CHOICES = (
    ('all', _('All')),
    ('false', _('Untagged Votes')),
)

ORDER_CHOICES = (
    ('time', _('Time')),
    ('controversy', _('Controversy')),
    ('against-party', _('Against Party')),
    ('votes', _('Number of votes')),
)

BILL_STAGES = OrderedDict((
    ('UNKNOWN', BillStages.UNKNOWN),
    ('FROZEN', BillStages.FROZEN),
    ('PROPOSED', BillStages.PROPOSED),
    ('PRE_APPROVED', BillStages.PRE_APPROVED),
    ('FAILED_PRE_APPROVAL', BillStages.FAILED_PRE_APPROVAL),
    ('CONVERTED_TO_DISCUSSION', BillStages.CONVERTED_TO_DISCUSSION),
    ('IN_COMMITTEE', BillStages.IN_COMMITTEE),
    ('FIRST_VOTE', BillStages.FIRST_VOTE),
    ('FAILED_FIRST_VOTE', BillStages.FAILED_FIRST_VOTE),
    ('COMMITTEE_CORRECTIONS', BillStages.COMMITTEE_CORRECTIONS),
    ('APPROVED', BillStages.APPROVED),
    ('FAILED_APPROVAL', BillStages.FAILED_APPROVAL),
))

BILL_STAGE_CHOICES = (
    (BillStages.UNKNOWN, _(u'Unknown')),
    (BillStages.FROZEN, _(u'Frozen in previous knesset')),
    (BillStages.PROPOSED, _(u'Proposed')),
    (BillStages.PRE_APPROVED, _(u'Pre-Approved')),
    (BillStages.FAILED_PRE_APPROVAL, _(u'Failed Pre-Approval')),
    (BillStages.CONVERTED_TO_DISCUSSION, _(u'Converted to discussion')),
    (BillStages.IN_COMMITTEE, _(u'In Committee')),
    (BillStages.FIRST_VOTE, _(u'First Vote')),
    (BillStages.FAILED_FIRST_VOTE, _(u'Failed First Vote')),
    (BillStages.COMMITTEE_CORRECTIONS, _(u'Committee Corrections')),
    (BillStages.APPROVED, _(u'Approved')),
    (BillStages.FAILED_APPROVAL, _(u'Failed Approval')),
)

BILL_AGRR_STAGES = {'proposed': Q(stage__isnull=False),
                    'pre': Q(stage=BillStages.PRE_APPROVED) | Q(stage=BillStages.IN_COMMITTEE) | Q(
                        stage=BillStages.FIRST_VOTE) | Q(stage=BillStages.COMMITTEE_CORRECTIONS) | Q(
                        stage=BillStages.APPROVED),
                    'first': Q(stage=BillStages.FIRST_VOTE) | Q(stage=BillStages.COMMITTEE_CORRECTIONS) | Q(
                        stage=BillStages.APPROVED),
                    'approved': Q(stage=BillStages.APPROVED),
                    }

BILL_TAGGED_CHOICES = (
    ('all', _('All')),
    ('false', _('Untagged Proposals')),
)
