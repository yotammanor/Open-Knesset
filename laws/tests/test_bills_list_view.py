# encoding: utf-8
#
import json
from datetime import date, timedelta, datetime

from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.test import TestCase
from tagging.models import Tag

from laws.models import Vote, Bill, KnessetProposal, Law

from mks.models import Knesset, Member

just_id = lambda x: x.id
APP = 'laws'


class BillListViewsTest(TestCase):
    def setUp(self):
        super(BillListViewsTest, self).setUp()

        today = date.today()
        current_knesset_start = today - timedelta(10)
        self.knesset = Knesset.objects.create(
            number=2,
            start_date=current_knesset_start)

        self.previous_knesset = Knesset.objects.create(
            number=1,
            end_date=current_knesset_start - timedelta(days=1),
            start_date=current_knesset_start - timedelta(days=10))
        self.vote_1 = Vote.objects.create(time=datetime.now(),
                                          title='vote 1')
        self.vote_2 = Vote.objects.create(time=datetime.now(),
                                          title='vote 2')
        self.jacob = User.objects.create_user('jacob', 'jacob@example.com',
                                              'JKM')
        self.adrian = User.objects.create_user('adrian', 'adrian@example.com',
                                               'ADRIAN')
        g, created = Group.objects.get_or_create(name='Valid Email')
        ct = ContentType.objects.get_for_model(Tag)
        p = Permission.objects.get(codename='add_tag', content_type=ct)
        g.permissions.add(p)

        self.adrian.groups.add(g)
        self.bill_1 = Bill.objects.create(stage='1', title='bill 1', popular_name="The Bill", stage_date=date.today())
        self.bill_2 = Bill.objects.create(stage='2', title='bill 2', stage_date=date.today())
        self.bill_3 = Bill.objects.create(stage='2', title='bill 1', stage_date=date.today())
        self.kp_1 = KnessetProposal.objects.create(booklet_number=2,
                                                   bill=self.bill_1,
                                                   title='first_kp',
                                                   date=date.today())
        self.mk_1 = Member.objects.create(name='mk 1')
        self.tag_1 = Tag.objects.create(name='tag1')

    def tearDown(self):
        super(BillListViewsTest, self).tearDown()

    def test_bill_list_returns_bills(self):
        res = self.client.get(reverse('bill-list'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'laws/bill_list.html')
        object_list = res.context['object_list']
        self.assertEqual(map(just_id, object_list),
                         [self.bill_3.id, self.bill_2.id, self.bill_1.id])

    def test_bills_are_filtered_by_stage(self):
        res = self.client.get(reverse('bill-list'), {'stage': 'all'})
        object_list = res.context['object_list']
        self.assertEqual(map(just_id, object_list),
                         [self.bill_3.id, self.bill_2.id, self.bill_1.id])
        res = self.client.get(reverse('bill-list'), {'stage': '1'})
        object_list = res.context['object_list']
        self.assertEqual(map(just_id, object_list), [self.bill_1.id])
        res = self.client.get(reverse('bill-list'), {'stage': '2'})
        object_list = res.context['object_list']
        self.assertEqual(set(map(just_id, object_list)), set([self.bill_2.id, self.bill_3.id]))

    def test_bill_list_with_member_returns_only_member_bills(self):
        "Test the view of bills proposed by specific MK"
        res = self.client.get(reverse('bill-list'), {'member': self.mk_1.id})
        self.assertEqual(res.status_code, 200)

    def test_bill_list_with_invalid_member(self):
        "test the view of bills proposed by specific mk, with invalid parameter"
        res = self.client.get(reverse('bill-list'), {'member': 'qwertyuiop'})
        self.assertEqual(res.status_code, 404)

    def test_bill_list_with_nonexisting_member(self):
        "test the view of bills proposed by specific mk, with nonexisting parameter"
        res = self.client.get(reverse('bill-list'), {'member': '0'})
        self.assertEqual(res.status_code, 404)

    def test_bill_list_filtered_by_knesset_booklet(self):
        res = self.client.get(reverse('bill-list'), {'knesset_booklet': '2'})
        object_list = res.context['object_list']
        self.assertEqual(map(just_id, object_list), [self.bill_1.id])

    def test_bill_list_filtered_by_knesset_id(self):
        date_in_previous_knesset = self.previous_knesset.start_date + timedelta(days=1)
        self.bill_1.stage_date = date_in_previous_knesset
        self.bill_1.save()

        res = self.client.get(reverse('bill-list'), {'knesset_id': '1'})
        object_list = res.context['object_list']
        self.assertItemsEqual(object_list, [self.bill_1])

        res = self.client.get(reverse('bill-list'), {'knesset_id': '2'})
        object_list = res.context['object_list']
        self.assertItemsEqual(object_list, [self.bill_2, self.bill_3])

    def test_knesset_proposal_autocomplete_with_booklet_id(self):
        law = self.given_law_exists('a_law')
        self.given_proposal_is_connected_to_law(self.kp_1, law)
        res = self.client.get(reverse('knesset-proposal-auto-complete'), {'query': 2})
        result = json.loads(res.content)['suggestions']
        self.assertItemsEqual(result, ['05/04/2016 - a_law - first_kp'])

    def test_knesset_proposal_autocomplete_with_law_title(self):
        law = self.given_law_exists('a_law')
        self.given_proposal_is_connected_to_law(self.kp_1, law)
        res = self.client.get(reverse('knesset-proposal-auto-complete'), {'query': 'a_law'})
        result = json.loads(res.content)['suggestions']
        self.assertItemsEqual(result, ['05/04/2016 - a_law - first_kp'])

    def given_law_exists(self, title):
        law, create = Law.objects.get_or_create(title=title)
        return law

    def given_proposal_is_connected_to_law(self, proposal, law):
        proposal.law = law
        proposal.save()
