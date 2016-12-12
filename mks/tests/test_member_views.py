import datetime

import feedparser
from actstream import follow
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test import TestCase

from committees.models import Committee
from laws.models import Law, PrivateProposal, Bill, Vote, VoteAction
from mks.models import Knesset, Party, Member
from mks.tests.base import just_id


class MemberViewsTestCase(TestCase):
    def setUp(self):
        # make sure cache is clean, to prevent some failing tests with
        # unexpected caches
        super(MemberViewsTestCase, self).setUp()
        from django.core.cache import cache

        cache.clear()

        d = datetime.date.today()

        self.knesset = Knesset.objects.create(
            number=1,
            start_date=d - datetime.timedelta(10))
        self.party_1 = Party.objects.create(name='party 1',
                                            knesset=self.knesset)
        self.party_2 = Party.objects.create(name='party 2',
                                            knesset=self.knesset)
        self.mk_1 = Member.objects.create(name='mk_1',
                                          start_date=datetime.date(2010, 1, 1),
                                          current_party=self.party_1,
                                          backlinks_enabled=True)
        self.mk_2 = Member.objects.create(name='mk_2',
                                          start_date=datetime.date(2010, 1, 1),
                                          current_party=self.party_1,
                                          backlinks_enabled=False)
        self.jacob = User.objects.create_user('jacob', 'jacob@jacobian.org',
                                              'JKM')

        self.committee_1 = Committee.objects.create(name='c1')
        self.meeting_1 = self.committee_1.meetings.create(
            date=d - datetime.timedelta(1),
            protocol_text='jacob:\nI am a perfectionist\nadrian:\nI have a deadline')
        self.meeting_2 = self.committee_1.meetings.create(
            date=d - datetime.timedelta(2),
            protocol_text='adrian:\nYou are a perfectionist\njacob:\nYou have a deadline')
        self.law = Law.objects.create(title='law 1')
        self.pp = PrivateProposal.objects.create(title='private proposal 1',
                                                 date=datetime.date.today() - datetime.timedelta(3))
        self.pp.proposers.add(self.mk_1)
        self.bill_1 = Bill.objects.create(stage='1', title='bill 1', law=self.law)
        self.bill_1.proposals.add(self.pp)
        self.bill_1.proposers.add(self.mk_1)
        self.meeting_1.mks_attended.add(self.mk_1)
        self.meeting_1.save()
        self.meeting_2.mks_attended.add(self.mk_1)
        self.meeting_2.save()
        self.vote = Vote.objects.create(title='vote 1', time=datetime.datetime.now())
        self.vote_action = VoteAction.objects.create(member=self.mk_1, vote=self.vote, type='for',
                                                     party=self.mk_1.current_party)
        self.domain = 'http://' + Site.objects.get_current().domain

    def test_member_by_bills_pre(self):
        res = self.client.get(reverse('member-list'))
        self.assertEqual(res.status_code, 301)

        res = self.client.get(reverse('member-stats', kwargs={'stat_type': 'bills_pre'}))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'mks/member_list.html')
        object_list = res.context['object_list']
        self.assertItemsEqual(map(just_id, object_list), [self.mk_1.id, self.mk_2.id])

    def test_member_by_non_active_stat_is_404(self):
        endpoint = 'member/by/graaph/'
        res = self.client.get(endpoint)
        self.assertEqual(res.status_code, 404)

    def testMemberDetail(self):
        res = self.client.get(reverse('member-detail', args=[self.mk_1.id]))
        self.assertTemplateUsed(res,
                                'mks/member_detail.html')
        self.assertEqual(res.context['object'].id, self.mk_1.id)

    def testMemberDetailOtherVerbs(self):
        """Tests the member detail view with parameters that make it render
        actions other than the default ones"""
        res = self.client.get('%s?verbs=attended&verbs=voted' %
                              reverse('member-detail', args=[self.mk_1.id]))
        self.assertTemplateUsed(res,
                                'mks/member_detail.html')
        self.assertEqual(res.context['object'].id, self.mk_1.id)

    def testPartyList(self):
        # party list should redirect to stats by seat
        res = self.client.get(reverse('party-list'))
        self.assertRedirects(res, reverse('party-stats', kwargs={'stat_type': 'seats'}), 301)

        # self.assertTemplateUsed(res, 'mks/party_list.html')
        # object_list = res.context['object_list']
        # self.assertEqual(map(just_id, object_list),
        #                 [ self.party_1.id, self.party_2.id, ])

    def testPartyDetail(self):
        res = self.client.get(reverse('party-detail',
                                      args=[self.party_1.id]))
        self.assertTemplateUsed(res, 'mks/party_detail.html')
        self.assertEqual(res.context['object'].id, self.party_1.id)

    def testMemberDetailsContext(self):
        # test anonymous user
        mk_1_url = self.mk_1.get_absolute_url()
        res = self.client.get(mk_1_url)
        self.assertFalse(res.context['watched_member'])
        # test autherized user
        self.assertTrue(self.client.login(username='jacob', password='JKM'))
        res = self.client.get(mk_1_url)
        self.assertFalse(res.context['watched_member'])
        # test autherized user that follows
        follow(self.jacob, self.mk_1)
        res = self.client.get(mk_1_url)
        self.assertTrue(res.context['watched_member'])

    def testMemberActivityFeed(self):
        res = self.client.get(reverse('member-activity-feed',
                                      args=[self.mk_1.id]))
        self.assertEqual(res.status_code, 200)
        parsed = feedparser.parse(res.content)
        # self.assertEqual(len(parsed['entries']),4)
        self.assertEqual(parsed['entries'][0]['link'], self.domain +
                         self.vote.get_absolute_url())
        self.assertEqual(parsed['entries'][1]['link'], self.domain +
                         self.meeting_1.get_absolute_url())
        self.assertEqual(parsed['entries'][2]['link'], self.domain +
                         self.meeting_2.get_absolute_url())
        self.assertEqual(parsed['entries'][3]['link'], self.domain +
                         self.bill_1.get_absolute_url())

    def testMemberActivityFeedWithVerbProposed(self):
        res = self.client.get(reverse('member-activity-feed',
                                      kwargs={'object_id': self.mk_1.id}), {'verbs': 'proposed'})
        self.assertEqual(res.status_code, 200)
        parsed = feedparser.parse(res.content)
        self.assertEqual(len(parsed['entries']), 1)

        res = self.client.get(reverse('member-activity-feed',
                                      kwargs={'object_id': self.mk_2.id}), {'verbs': 'proposed'})
        self.assertEqual(res.status_code, 200)
        parsed = feedparser.parse(res.content)
        self.assertEqual(len(parsed['entries']), 0)

    def testMemberActivityFeedWithVerbAttended(self):
        res = self.client.get(reverse('member-activity-feed',
                                      kwargs={'object_id': self.mk_1.id}), {'verbs': 'attended'})
        self.assertEqual(res.status_code, 200)
        parsed = feedparser.parse(res.content)
        self.assertEqual(len(parsed['entries']), 2)

        res = self.client.get(reverse('member-activity-feed',
                                      kwargs={'object_id': self.mk_2.id}), {'verbs': 'attended'})
        self.assertEqual(res.status_code, 200)
        parsed = feedparser.parse(res.content)
        self.assertEqual(len(parsed['entries']), 0)

    def testMemberActivityFeedWithVerbJoined(self):
        res = self.client.get(reverse('member-activity-feed',
                                      kwargs={'object_id': self.mk_1.id}), {'verbs': 'joined'})
        self.assertEqual(res.status_code, 200)
        parsed = feedparser.parse(res.content)
        self.assertEqual(len(parsed['entries']), 0)

    def testMemberActivityFeedWithVerbPosted(self):
        res = self.client.get(reverse('member-activity-feed',
                                      kwargs={'object_id': self.mk_1.id}), {'verbs': 'posted'})
        self.assertEqual(res.status_code, 200)
        parsed = feedparser.parse(res.content)
        self.assertEqual(len(parsed['entries']), 0)

    def tearDown(self):
        super(MemberViewsTestCase, self).tearDown()
        self.party_1.delete()
        self.party_2.delete()
        self.mk_1.delete()
        self.mk_2.delete()
        self.jacob.delete()
