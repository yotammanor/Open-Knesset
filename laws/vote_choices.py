from django.utils.translation import ugettext_lazy as _
from django.db.models import Q
from collections import OrderedDict

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
    ('UNKNOWN', u'?'),
    ('FROZEN', u'0'),
    ('PROPOSED', u'1'),
    ('PRE_APPROVED', u'2'),
    ('FAILED_PRE_APPROVAL', u'-2'),
    ('CONVERTED_TO_DISCUSSION', u'-2.1'),
    ('IN_COMMITTEE', u'3'),
    ('FIRST_VOTE', u'4'),
    ('FAILED_FIRST_VOTE', u'-4'),
    ('COMMITTEE_CORRECTIONS', u'5'),
    ('APPROVED', u'6'),
    ('FAILED_APPROVAL', u'-6'),
))

BILL_STAGE_CHOICES = (
        (BILL_STAGES['UNKNOWN'], _(u'Unknown')),
        (BILL_STAGES['FROZEN'], _(u'Frozen in previous knesset')),
        (BILL_STAGES['PROPOSED'], _(u'Proposed')),
        (BILL_STAGES['PRE_APPROVED'], _(u'Pre-Approved')),
        (BILL_STAGES['FAILED_PRE_APPROVAL'],_(u'Failed Pre-Approval')),
        (BILL_STAGES['CONVERTED_TO_DISCUSSION'], _(u'Converted to discussion')),
        (BILL_STAGES['IN_COMMITTEE'], _(u'In Committee')),
        (BILL_STAGES['FIRST_VOTE'], _(u'First Vote')),
        (BILL_STAGES['FAILED_FIRST_VOTE'],_(u'Failed First Vote')),
        (BILL_STAGES['COMMITTEE_CORRECTIONS'], _(u'Committee Corrections')),
        (BILL_STAGES['APPROVED'], _(u'Approved')),
        (BILL_STAGES['FAILED_APPROVAL'],_(u'Failed Approval')),
)

BILL_AGRR_STAGES = { 'proposed':Q(stage__isnull=False),
                'pre':Q(stage='2')|Q(stage='3')|Q(stage='4')|Q(stage='5')|Q(stage='6'),
                'first':Q(stage='4')|Q(stage='5')|Q(stage='6'),
                'approved':Q(stage='6'),
              }

BILL_TAGGED_CHOICES = (
    ('all', _('All')),
    ('false', _('Untagged Proposals')),
)

