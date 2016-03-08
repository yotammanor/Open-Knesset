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
