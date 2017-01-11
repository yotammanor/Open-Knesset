# encoding: utf-8
#

import unittest
from datetime import date, timedelta, datetime
import json

from django.conf import settings
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.test import TestCase
from tagging.models import Tag

from laws.models import Vote, Bill, KnessetProposal, BillBudgetEstimation
from mks.models import Knesset, Member
from committees.models import Committee, CommitteeMeeting

just_id = lambda x: x.id
APP = 'laws'


class BillDetailViewsTest(TestCase):

    def setUp(self):
        super(BillDetailViewsTest, self).setUp()

        d = date.today()
        self.knesset = Knesset.objects.create(
            number=1,
            start_date=d - timedelta(10))
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
        self.bill_1 = Bill.objects.create(stage='1', title='bill 1', popular_name="The Bill")
        self.bill_2 = Bill.objects.create(stage='2', title='bill 2')
        self.bill_3 = Bill.objects.create(stage='2', title='bill 1')
        self.kp_1 = KnessetProposal.objects.create(booklet_number=2,
                                                   bill=self.bill_1,
                                                   date=date.today())
        self.mk_1 = Member.objects.create(name='mk 1')
        self.tag_1 = Tag.objects.create(name='tag1')

        self.committee_1 = Committee.objects.create(name='laws bill details view committee 1')
        self.committee_meeting_1 = self.committee_1.meetings.create(date=datetime.now(), topics="laws bill details view committee meeting 1")

    def tearDown(self):
        super(BillDetailViewsTest, self).tearDown()

    def testBillDetail(self):
        res = self.client.get(reverse('bill-detail',
                                      kwargs={'pk': self.bill_1.id}))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res,
                                'laws/bill_detail.html')
        self.assertEqual(res.context['object'].id, self.bill_1.id)

    def test_bill_detail_by_slug(self):
        res = self.client.get(reverse('bill-detail-with-slug',
                                      kwargs={'slug': self.bill_1.slug,
                                              'pk': self.bill_1.id}))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res,
                                'laws/bill_detail.html')
        self.assertEqual(res.context['object'].id, self.bill_1.id)

    def test_bill_popular_name(self):
        res = self.client.get('/bill/' + self.bill_1.popular_name + '/')
        self.assertEqual(res.status_code, 404)

    def test_bill_popular_name_by_slug(self):
        res = self.client.get(reverse('bill-detail-with-slug',
                                      kwargs={'slug': self.bill_1.popular_name_slug,
                                              'pk': self.bill_1.id}))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res,
                                'laws/bill_detail.html')
        self.assertEqual(res.context['object'].id, self.bill_1.id)

    '''
    def test_bill_detail_hebrew_name_by_slug(self):
        res = self.client.get(reverse('bill-detail',
                                 kwargs={'slug': self.bill_hebrew_name.slug}))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res,
                                'laws/bill_detail.html')
        self.assertEqual(res.context['object'].id, self.bill_1.id)
    '''

    def testLoginRequired(self):
        res = self.client.post(reverse('bill-detail',
                                       kwargs={'pk': self.bill_1.id}))
        self.assertEqual(res.status_code, 302)
        self.assertTrue(res['location'].startswith('%s%s' %
                                                   ('http://testserver', settings.LOGIN_URL)))

    def testPOSTApprovalVote(self):
        self.assertTrue(self.client.login(username='jacob', password='JKM'))
        res = self.client.post(reverse('bill-detail',
                                       kwargs={'pk': self.bill_1.id}),
                               {'user_input_type': 'approval vote',
                                'vote_id': self.vote_1.id})
        self.assertEqual(res.status_code, 302)
        self.bill_1 = Bill.objects.get(pk=self.bill_1.id)
        self.assertEqual(self.bill_1.approval_vote, self.vote_1)
        self.assertEqual(self.bill_1.first_vote, None)
        self.assertFalse(self.bill_1.pre_votes.all())
        # cleanup
        self.bill_1.approval_vote = None
        self.bill_1.save()
        self.client.logout()

    def testPOSTFirstVote(self):
        self.assertTrue(self.client.login(username='jacob', password='JKM'))
        res = self.client.post(reverse('bill-detail',
                                       kwargs={'pk': self.bill_1.id}),
                               {'user_input_type': 'first vote',
                                'vote_id': self.vote_2.id})
        self.assertEqual(res.status_code, 302)
        self.bill_1 = Bill.objects.get(pk=self.bill_1.id)
        self.assertEqual(self.bill_1.first_vote, self.vote_2)
        self.assertEqual(self.bill_1.approval_vote, None)
        self.assertFalse(self.bill_1.pre_votes.all())
        # cleanup
        self.bill_1.first_vote = None
        self.bill_1.save()
        self.client.logout()

    def testPOSTPreVote(self):
        self.assertTrue(self.client.login(username='jacob', password='JKM'))
        res = self.client.post(reverse('bill-detail',
                                       kwargs={'pk': self.bill_1.id}),
                               {'user_input_type': 'pre vote',
                                'vote_id': self.vote_2.id})
        self.assertEqual(res.status_code, 302)
        self.bill_1 = Bill.objects.get(pk=self.bill_1.id)
        self.assertTrue(self.vote_2 in self.bill_1.pre_votes.all())
        self.assertEqual(self.bill_1.first_vote, None)
        self.assertEqual(self.bill_1.approval_vote, None)
        # cleanup
        self.bill_1.pre_votes.clear()
        self.client.logout()

    ''' TODO: test the feed
    def testFeeds(self):
        res = self.client.get(reverse('bills-feed'))
        self.assertEqual(res.status_code, 200)
        ...use feedparser to analyze res
    '''

    def test_add_tag_to_bill_login_required(self):
        url = reverse('add-tag-to-object',
                      kwargs={'app': APP, 'object_type': 'bill', 'object_id': self.bill_1.id})
        res = self.client.post(url, {'tag_id': self.tag_1})
        self.assertRedirects(res, "%s?next=%s" % (settings.LOGIN_URL, url), status_code=302)

    def test_add_tag_to_bill(self):
        self.assertTrue(self.client.login(username='jacob', password='JKM'))
        url = reverse('add-tag-to-object',
                      kwargs={'app': APP, 'object_type': 'bill', 'object_id': self.bill_1.id})
        res = self.client.post(url, {'tag_id': self.tag_1.id})
        self.assertEqual(res.status_code, 200)
        self.assertIn(self.tag_1, self.bill_1.tags)

    @unittest.skip("creating tags currently disabled")
    def test_create_tag_permission_required(self):
        self.assertTrue(self.client.login(username='jacob', password='JKM'))
        url = reverse('create-tag',
                      kwargs={'app': APP, 'object_type': 'bill', 'object_id': self.bill_1.id})
        res = self.client.post(url, {'tag': 'new tag'})
        self.assertRedirects(res, "%s?next=%s" % (settings.LOGIN_URL, url), status_code=302)

    @unittest.skip("creating tags currently disabled")
    def test_create_tag(self):
        self.assertTrue(self.client.login(username='adrian', password='ADRIAN'))
        url = reverse('create-tag',
                      kwargs={'app': APP, 'object_type': 'bill', 'object_id': self.bill_1.id})
        res = self.client.post(url, {'tag': 'new tag'})
        self.assertEqual(res.status_code, 200)
        self.new_tag = Tag.objects.get(name='new tag')
        self.assertIn(self.new_tag, self.bill_1.tags)

    def test_add_budget_est(self):
        self.assertTrue(self.client.login(username='jacob', password='JKM'))
        res = self.client.post(reverse('bill-detail',
                                       kwargs={'pk': self.bill_1.id}),
                               {'user_input_type': 'budget_est',
                                'be_one_time_gov': 1,
                                'be_yearly_gov': 2,
                                'be_one_time_ext': 3,
                                # explicitly missing: 'be_yearly_ext': 4,
                                'be_summary': 'Trust me.'})
        self.assertEqual(res.status_code, 302)
        budget_est = self.bill_1.budget_ests.get(estimator__username='jacob')
        self.assertEqual(budget_est.one_time_gov, 1)
        self.assertEqual(budget_est.yearly_gov, 2)
        self.assertEqual(budget_est.one_time_ext, 3)
        self.assertEqual(budget_est.yearly_ext, None)
        self.assertEqual(budget_est.summary, 'Trust me.')
        # cleanup
        budget_est.delete()
        self.client.logout()

    def test_update_budget_est(self):
        self.assertTrue(self.client.login(username='jacob', password='JKM'))
        # add
        res = self.client.post(reverse('bill-detail',
                                       kwargs={'pk': self.bill_1.id}),
                               {'user_input_type': 'budget_est',
                                'be_one_time_gov': 1,
                                'be_yearly_gov': 2,
                                'be_one_time_ext': 3,
                                # explicitly missing: 'be_yearly_ext': 4,
                                'be_summary': 'Trust me.'})
        self.assertEqual(res.status_code, 302)
        budget_est = self.bill_1.budget_ests.get(estimator__username='jacob')
        self.assertEqual(budget_est.one_time_gov, 1)
        self.assertEqual(budget_est.yearly_gov, 2)
        self.assertEqual(budget_est.one_time_ext, 3)
        self.assertEqual(budget_est.yearly_ext, None)
        self.assertEqual(budget_est.summary, 'Trust me.')
        # now update
        res = self.client.post(reverse('bill-detail',
                                       kwargs={'pk': self.bill_1.id}),
                               {'user_input_type': 'budget_est',
                                # explicitly missing: 'be_one_time_gov': 4,
                                'be_yearly_gov': 3,
                                'be_one_time_ext': 2,
                                'be_yearly_ext': 1,
                                'be_summary': 'Trust him.'})
        self.assertEqual(res.status_code, 302)
        budget_est = self.bill_1.budget_ests.get(estimator__username='jacob')
        self.assertEqual(budget_est.one_time_gov, None)
        self.assertEqual(budget_est.yearly_gov, 3)
        self.assertEqual(budget_est.one_time_ext, 2)
        self.assertEqual(budget_est.yearly_ext, 1)
        self.assertEqual(budget_est.summary, 'Trust him.')
        # cleanup
        budget_est.delete()
        self.client.logout()

    def test_bad_add_budget_est(self):
        self.assertTrue(self.client.login(username='jacob', password='JKM'))
        res = self.client.post(reverse('bill-detail',
                                       kwargs={'pk': self.bill_1.id}),
                               {'user_input_type': 'budget_est',
                                'be_one_time_gov': 'aaa',
                                'be_yearly_gov': 2,
                                'be_one_time_ext': 3,
                                'be_yearly_ext': 4,
                                'be_summary': 'Trust me.'})
        self.assertEqual(res.status_code, 200)
        try:
            budget_est = self.bill_1.budget_ests.get(estimator__username='jacob')
            budget_est.delete()
            raise AssertionError('Budget shouldn\'t be created.')
        except BillBudgetEstimation.DoesNotExist:
            pass
        # cleanup
        self.client.logout()

    def test_other_adds_budget_est(self):
        self.assertTrue(self.client.login(username='jacob', password='JKM'))
        # add
        res = self.client.post(reverse('bill-detail',
                                       kwargs={'pk': self.bill_1.id}),
                               {'user_input_type': 'budget_est',
                                'be_one_time_gov': 1,
                                'be_yearly_gov': 2,
                                'be_one_time_ext': 3,
                                # explicitly missing: 'be_yearly_ext': 4,
                                'be_summary': 'Trust me.'})
        self.assertEqual(res.status_code, 302)
        budget_est = self.bill_1.budget_ests.get(estimator__username='jacob')
        self.assertEqual(budget_est.one_time_gov, 1)
        self.assertEqual(budget_est.yearly_gov, 2)
        self.assertEqual(budget_est.one_time_ext, 3)
        self.assertEqual(budget_est.yearly_ext, None)
        self.assertEqual(budget_est.summary, 'Trust me.')
        self.client.logout()
        # now add with other user.
        self.assertTrue(self.client.login(username='adrian', password='ADRIAN'))
        res = self.client.post(reverse('bill-detail',
                                       kwargs={'pk': self.bill_1.id}),
                               {'user_input_type': 'budget_est',
                                # explicitly missing: 'be_one_time_gov': 4,
                                'be_yearly_gov': 3,
                                'be_one_time_ext': 2,
                                'be_yearly_ext': 1,
                                'be_summary': 'Trust him.'})
        self.assertEqual(res.status_code, 302)
        # check first user, should give same result.
        budget_est = self.bill_1.budget_ests.get(estimator__username='jacob')
        self.assertEqual(budget_est.one_time_gov, 1)
        self.assertEqual(budget_est.yearly_gov, 2)
        self.assertEqual(budget_est.one_time_ext, 3)
        self.assertEqual(budget_est.yearly_ext, None)
        self.assertEqual(budget_est.summary, 'Trust me.')
        self.client.logout()
        # now add with first user, different bill.
        self.assertTrue(self.client.login(username='jacob', password='JKM'))
        res = self.client.post(reverse('bill-detail',
                                       kwargs={'pk': self.bill_2.id}),
                               {'user_input_type': 'budget_est',
                                # explicitly missing: 'be_one_time_gov': 4,
                                'be_yearly_gov': 3,
                                'be_one_time_ext': 2,
                                'be_yearly_ext': 1,
                                'be_summary': 'Trust him.'})
        self.assertEqual(res.status_code, 302)
        # check first bill, should give same result.
        budget_est = self.bill_1.budget_ests.get(estimator__username='jacob')
        self.assertEqual(budget_est.one_time_gov, 1)
        self.assertEqual(budget_est.yearly_gov, 2)
        self.assertEqual(budget_est.one_time_ext, 3)
        self.assertEqual(budget_est.yearly_ext, None)
        self.assertEqual(budget_est.summary, 'Trust me.')
        # cleanup
        budget_est.delete()
        self.bill_1.budget_ests.get(estimator__username='adrian').delete()
        self.bill_2.budget_ests.get(estimator__username='jacob').delete()
        self.client.logout()

    def test_bind_committee_meeting(self):
        self.assertTrue(self.client.login(username='jacob', password='JKM'))
        for bill_committee_meetings, cm_stage in ((self.bill_1.first_committee_meetings, "1"),
                                                  (self.bill_1.second_committee_meetings, "2")):
            bill_committee_meetings.remove(self.committee_meeting_1)
            self.assertFalse(bill_committee_meetings.filter(pk=self.committee_meeting_1.pk).exists())
            res = self.client.post(reverse('bill-detail',
                                           kwargs={'pk': self.bill_1.id}),
                                   {'user_input_type': 'committee_meetings',
                                    'cm_id': self.committee_meeting_1.pk,
                                    'cm_stage': cm_stage})
            self.assertEqual(res.status_code, 302)
            self.assertEqual(res.url, 'http://testserver' + reverse('bill-detail', args=(self.bill_1.pk,)))
            self.assertTrue(bill_committee_meetings.filter(pk=self.committee_meeting_1.pk).exists())

    def test_unbind_committee_meeting(self):
        self.assertTrue(self.client.login(username='jacob', password='JKM'))
        for bill_committee_meetings, cm_stage in ((self.bill_1.first_committee_meetings, "1"),
                                                  (self.bill_1.second_committee_meetings, "2")):
            bill_committee_meetings.add(self.committee_meeting_1)
            self.assertTrue(bill_committee_meetings.filter(pk=self.committee_meeting_1.pk).exists())
            res = self.client.post(reverse('bill-unbind-committee-meeting', args=(self.bill_1.pk, self.committee_meeting_1.pk, cm_stage)),
                                   {'explanation': 'sorry, must do it!'})
            self.assertEqual(res.status_code, 302)
            self.assertEqual(res.url, 'http://testserver'+reverse('bill-detail', args=(self.bill_1.pk,)))
            self.assertFalse(bill_committee_meetings.filter(pk=self.committee_meeting_1.pk).exists())

    def test_committee_meeting_auto_complete(self):
        self.assertTrue(self.client.login(username='jacob', password='JKM'))
        res = self.client.get(reverse('committee-meeting-auto-complete'), {'query': self.committee_meeting_1.topics})
        self.assertDictContainsSubset({
            "query": self.committee_meeting_1.topics,
            "suggestions": ["{date_string} - {topics}".format(date_string=self.committee_meeting_1.date_string, topics=self.committee_meeting_1.topics)],
            'data': [self.committee_meeting_1.pk]
        }, json.loads(res.content))

    # def tearDown(self):
    #     self.vote_1.delete()
    #     self.vote_2.delete()
    #     self.bill_1.delete()
    #     self.bill_2.delete()
    #     self.bill_3.delete()
    #     self.jacob.delete()
    #     self.mk_1.delete()
    #     self.tag_1.delete()
