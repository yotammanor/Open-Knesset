import datetime

from django.test import TestCase

from laws.enums import BillStages
from laws.models import Bill
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

    def test_member_names_includes_alt_names(self):
        m = Member(name='test member')
        self.assertEqual(m.names, ['test member'])
        m.save()
        MemberAltname(member=m, name='test2').save()
        self.assertEqual(m.names, ['test member', 'test2'])

    def test_member_bill_statistics_calculation_counts_bill_per_stage_correctly(self):
        first_bill = self.given_bill_exists('first_bill')
        self.given_member_proposed_bill(self.member, first_bill)

        self.given_bill_stage(first_bill, stage=BillStages.PROPOSED)
        self.member.recalc_bill_statistics()

        self.assertEqual(self.member.bills_stats_proposed, 1)
        self.assertEqual(self.member.bills_stats_pre, 0)
        self.assertEqual(self.member.bills_stats_first, 0)
        self.assertEqual(self.member.bills_stats_approved, 0)

        self.given_bill_stage(first_bill, stage=BillStages.PRE_APPROVED)
        self.member.recalc_bill_statistics()

        self.assertEqual(self.member.bills_stats_proposed, 1)
        self.assertEqual(self.member.bills_stats_pre, 1)
        self.assertEqual(self.member.bills_stats_first, 0)
        self.assertEqual(self.member.bills_stats_approved, 0)

        self.given_bill_stage(first_bill, stage=BillStages.COMMITTEE_CORRECTIONS)
        self.member.recalc_bill_statistics()

        self.assertEqual(self.member.bills_stats_proposed, 1)
        self.assertEqual(self.member.bills_stats_pre, 1)
        self.assertEqual(self.member.bills_stats_first, 1)
        self.assertEqual(self.member.bills_stats_approved, 0)

        self.given_bill_stage(first_bill, stage=BillStages.APPROVED)
        self.member.recalc_bill_statistics()

        self.assertEqual(self.member.bills_stats_proposed, 1)
        self.assertEqual(self.member.bills_stats_pre, 1)
        self.assertEqual(self.member.bills_stats_first, 1)
        self.assertEqual(self.member.bills_stats_approved, 1)

    def test_member_bill_statistics_calculation_counts_bill_correctly_if_disapproved_in_the_end(self):
        first_bill = self.given_bill_exists('first_bill')
        self.given_member_proposed_bill(self.member, first_bill)

        self.given_bill_stage(first_bill, stage=BillStages.PROPOSED)
        self.member.recalc_bill_statistics()

        self.assertEqual(self.member.bills_stats_proposed, 1)
        self.assertEqual(self.member.bills_stats_pre, 0)
        self.assertEqual(self.member.bills_stats_first, 0)
        self.assertEqual(self.member.bills_stats_approved, 0)

        self.given_bill_stage(first_bill, stage=BillStages.PRE_APPROVED)
        self.member.recalc_bill_statistics()

        self.assertEqual(self.member.bills_stats_proposed, 1)
        self.assertEqual(self.member.bills_stats_pre, 1)
        self.assertEqual(self.member.bills_stats_first, 0)
        self.assertEqual(self.member.bills_stats_approved, 0)

        self.given_bill_stage(first_bill, stage=BillStages.FAILED_APPROVAL)
        self.member.recalc_bill_statistics()

        self.assertEqual(self.member.bills_stats_proposed, 1)
        self.assertEqual(self.member.bills_stats_pre, 1,
                         'Expected bill to exist in pre state although later disapproved')
        self.assertEqual(self.member.bills_stats_first, 1)
        self.assertEqual(self.member.bills_stats_approved, 0)

    def test_member_bill_statistics_calculation_does_not_count_bills_before_current_knesset(self):
        first_bill = self.given_bill_exists('first_bill')
        self.given_member_proposed_bill(self.member, first_bill)

        date_in_previous_knesset = self.previous_knesset.start_date + datetime.timedelta(days=1)
        self.given_bill_stage(first_bill, stage=BillStages.PROPOSED, stage_date=date_in_previous_knesset)
        self.member.recalc_bill_statistics()

        self.assertEqual(self.member.bills_stats_proposed, 0)
        self.assertEqual(self.member.bills_stats_pre, 0)
        self.assertEqual(self.member.bills_stats_first, 0)
        self.assertEqual(self.member.bills_stats_approved, 0)

    def test_member_current_knesset_bills_link(self):
        url = self.member.get_current_knesset_bills_by_stage_url(stage='first')
        current_knesset = Knesset.objects.current_knesset().number
        self.assertEqual(url, '/bill/?member={0}&knesset_id={1}&stage=first'.format(self.member.id, current_knesset))

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

    def given_bill_exists(self, title='bill 1', stage=BillStages.PROPOSED):
        bill = Bill.objects.create(stage=stage, title=title)
        return bill

    def given_bill_stage(self, bill, stage, stage_date=None):
        bill.stage = stage
        if stage_date:
            bill.stage_date = stage_date
        else:
            bill.stage_date = datetime.datetime.now()
        bill.save()

    def given_member_proposed_bill(self, member, bill):
        bill.proposers.add(member)
