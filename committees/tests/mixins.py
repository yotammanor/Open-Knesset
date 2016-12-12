# encoding: utf-8
from committees.models import Committee, CommitteeMeeting
import datetime


class CommitteesTestsMixin(object):

    def get_committee(self, name=u'ועדת הכנסת'):
        committee, created = Committee.objects.get_or_create(name=name)
        return committee

    def get_committee_meeting(self, committee=None):
        committee = self.get_committee() if not committee else committee
        committee_meeting, created = CommitteeMeeting.objects.get_or_create(
            committee = committee if committee else self.get_committee(),
            date_string = u'22/02/2016',
            date = datetime.date(2016, 2, 22)
        )
        return committee_meeting
