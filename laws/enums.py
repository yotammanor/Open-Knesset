# encoding: utf-8
from django.utils.translation import ugettext_lazy as _

from knesset.enums import Enum


class BillStages(Enum):
    UNKNOWN = u'?'
    FROZEN = u'0'
    PROPOSED = u'1'
    PRE_APPROVED = u'2'
    FAILED_PRE_APPROVAL = u'-2'
    CONVERTED_TO_DISCUSSION = u'-2.1'
    IN_COMMITTEE = u'3'
    FIRST_VOTE = u'4'
    FAILED_FIRST_VOTE = u'-4'
    COMMITTEE_CORRECTIONS = u'5'
    APPROVED = u'6'
    FAILED_APPROVAL = u'-6'


VOTE_TYPES = {'law-approve': u'אישור החוק', 'second-call': u'קריאה שנייה', 'demurrer': u'הסתייגות',
              'no-confidence': u'הצעת אי-אמון', 'pass-to-committee': u'להעביר את ',
              'continuation': u'להחיל דין רציפות'}

VOTE_ACTION_TYPE_CHOICES = (
    (u'for', _('For')),
    (u'against', _('Against')),
    (u'abstain', _('Abstain')),
    (u'no-vote', _('No Vote')),
)
