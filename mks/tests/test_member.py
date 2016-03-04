import datetime

from django.test import TestCase

from mks.models import Knesset, Party, Member, Membership, MemberAltname
from mks.tests.base import ten_days_ago, two_days_ago


class TestMember(TestCase):
    def setUp(self):
        super(TestMember, self).setUp()

        self.previous_knesset = Knesset.objects.create(number=1,
                                                       start_date=ten_days_ago,
                                                       end_date=two_days_ago)
        self.current_knesset = Knesset.objects.create(number=2,
                                                      start_date=two_days_ago)
        self.previous_party = self.given_party_exists_in_knesset('a_party', self.previous_knesset)
        self.current_party = self.given_party_exists_in_knesset('a_party', self.current_knesset)
        self.member = self.given_member_exists_in_knesset('member_1', self.previous_party)
        self.member = self.given_member_exists_in_knesset('member_1', self.current_party)

    def tearDown(self):
        super(TestMember, self).tearDown()

    def test_party_at_calculates_correct_party_by_date_when_no_end_date_for_two_periods(self):
        five_days_ago = datetime.datetime.today() - datetime.timedelta(days=5)
        party_at = self.member.party_at(five_days_ago.date())
        self.assertEqual(party_at, self.previous_party)

        today = datetime.datetime.today()
        party_at = self.member.party_at(today.date())
        self.assertEqual(party_at, self.current_party)

    def test_party_at_calculates_correct_party_by_date_when_given_end_date(self):
        self.given_member_exists_in_knesset(self.member.name, self.previous_party, end_date=two_days_ago.date())
        five_days_ago = datetime.datetime.today() - datetime.timedelta(days=5)
        party_at = self.member.party_at(five_days_ago.date())
        self.assertEqual(party_at, self.previous_party)

        today = datetime.datetime.today()
        party_at = self.member.party_at(today.date())
        self.assertEqual(party_at, self.current_party)

    def testNames(self):
        m = Member(name='test member')
        self.assertEqual(m.names, ['test member'])
        m.save()
        MemberAltname(member=m, name='test2').save()
        self.assertEqual(m.names, ['test member', 'test2'])

    def given_party_exists_in_knesset(self, party_name, knesset):
        party, create = Party.objects.get_or_create(name='{0}_{1}'.format(party_name, knesset.number),
                                                    knesset=knesset,
                                                    start_date=knesset.start_date,
                                                    end_date=knesset.end_date)
        return party

    def given_member_exists_in_knesset(self, member_name, party, end_date=None):
        member, create = Member.objects.get_or_create(name=member_name, start_date=ten_days_ago.date())
        membership, create = Membership.objects.get_or_create(member=member, party=party,
                                                              start_date=party.knesset.start_date)
        if end_date:
            membership.end_date = end_date
            membership.save()
        return member


