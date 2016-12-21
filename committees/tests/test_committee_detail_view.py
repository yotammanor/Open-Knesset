from datetime import datetime, timedelta

from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType

from waffle import testutils as waffle_testutils
from tagging.models import Tag, TaggedItem
from waffle import testutils as waffle_testutils

from committees.tests.base import BaseCommitteeTestCase
from laws.models import Bill
from mks.models import Member, Knesset
from committees.models import Committee, CommitteeMeeting

just_id = lambda x: x.id
APP = 'committees'


class CommitteeDetailViewTest(BaseCommitteeTestCase):
    def setUp(self):
        super(CommitteeDetailViewTest, self).setUp()
        self.knesset = Knesset.objects.create(number=1,
                                              start_date=datetime.today() - timedelta(
                                                  days=1))
        self.committee_1 = Committee.objects.create(name='c1')
        self.committee_2 = Committee.objects.create(name='c2')
        self.meeting_1 = self.committee_1.meetings.create(date=datetime.now(),
                                                          topics="django",
                                                          protocol_text='''jacob:
I am a perfectionist
adrian:
I have a deadline''')
        self.meeting_1.create_protocol_parts()
        self.meeting_2 = self.committee_1.meetings.create(date=datetime.now(),
                                                          topics="python",
                                                          protocol_text='m2')
        self.meeting_2.create_protocol_parts()
        self.jacob = User.objects.create_user('jacob', 'jacob@example.com',
                                              'JKM')
        self.adrian = User.objects.create_user('adrian', 'adrian@example.com',
                                               'ADRIAN')
        (self.group, created) = Group.objects.get_or_create(name='Valid Email')
        if created:
            self.group.save()
        self.group.permissions.add(
            Permission.objects.get(name='Can add annotation'))
        self.jacob.groups.add(self.group)

        ct = ContentType.objects.get_for_model(Tag)
        self.adrian.user_permissions.add(
            Permission.objects.get(codename='add_tag', content_type=ct))

        self.bill_1 = Bill.objects.create(stage='1', title='bill 1')
        self.mk_1 = Member.objects.create(name='mk 1')
        self.topic = self.committee_1.topic_set.create(creator=self.jacob,
                                                       title="hello",
                                                       description="hello world")
        self.tag_1 = Tag.objects.create(name='tag1')
        self.meeting_1.mks_attended.add(self.mk_1)

    def tearDown(self):
        super(CommitteeDetailViewTest, self).tearDown()
        self.client.logout()
        self.meeting_1.delete()
        self.meeting_2.delete()
        self.committee_1.delete()
        self.committee_2.delete()
        self.jacob.delete()
        self.group.delete()
        self.bill_1.delete()
        self.mk_1.delete()
        self.topic.delete()

    @waffle_testutils.override_flag('show_committee_topics', active=True)
    def test_committee_list_view(self):
        res = self.client.get(reverse('committee-list'))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'committees/committee_list.html')
        committees = res.context['committees']
        self.assertEqual(map(just_id, committees),
                         [self.committee_1.id, self.committee_2.id, ])
        self.assertQuerysetEqual(res.context['topics'],
                                 ["<Topic: hello>"])

    @waffle_testutils.override_flag('show_committee_topics', active=False)
    def test_committee_list_view_topics_are_hidden_when_flag_inactive(self):
        res = self.client.get(reverse('committee-list'))
        self.assertEqual(res.status_code, 200)

        self.verify_topics_in_response(res, is_expected_in_response=False)


    @waffle_testutils.override_flag('show_committee_topics', active=True)
    def test_committee_topics_is_displayed_when_flag_is_active(self):
        res = self.client.get(self.committee_1.get_absolute_url())
        self.assertEqual(res.status_code, 200)

        self.verify_topics_in_response(res, is_expected_in_response=True)

    @waffle_testutils.override_flag('show_committee_topics', active=False)
    def test_committee_topics_is_hidden_when_flag_is_not_active(self):
        res = self.client.get(self.committee_1.get_absolute_url())
        self.assertEqual(res.status_code, 200)

        self.verify_topics_in_response(res, is_expected_in_response=False)


    def test_committee_returns_a_list_of_meetings(self):
        res = self.client.get(self.committee_1.get_absolute_url())
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res,
                                'committees/committee_detail.html')
        object_list = res.context['meetings_list']
        self.assertEqual(map(just_id, object_list),
                         [self.meeting_1.id, self.meeting_2.id, ],
                         'object_list has wrong objects: %s' % object_list)

    def test_committee_does_not_return_non_active_current_knesset_members(
            self):
        non_current_mk = Member.objects.create(name='mk is no more',
                                               is_current=False)
        self.given_mk_is_added_to_committee(self.committee_1, non_current_mk)
        self.given_mk_is_added_to_committee(self.committee_1, self.mk_1)

        res = self.client.get(self.committee_1.get_absolute_url())
        self.assertEqual(res.status_code, 200)

        self.verify_expected_members_in_context(res, [self.mk_1.pk])
        self.verify_unexpected_members_not_in_context(res, [non_current_mk.pk])

    def test_committee_does_not_return_non_active_current_knesset_members_who_were_replacements(
            self):
        non_current_mk = Member.objects.create(name='mk is no more',
                                               is_current=False)
        self.given_mk_is_added_to_committee(self.committee_1, non_current_mk)
        self.given_mk_is_added_to_committee_as_replacment(self.committee_1,
                                                          non_current_mk)
        self.given_mk_is_added_to_committee(self.committee_1, self.mk_1)

        res = self.client.get(self.committee_1.get_absolute_url())
        self.assertEqual(res.status_code, 200)

        self.verify_expected_members_in_context(res, [self.mk_1.pk])
        self.verify_unexpected_members_not_in_context(res, [non_current_mk.pk])

    def test_committee_does_not_return_non_active_current_knesset_members_who_were_person(
            self):
        non_current_mk = Member.objects.create(name='mk is no more',
                                               is_current=False)
        self.given_mk_is_added_to_committee(self.committee_1, non_current_mk)
        self.given_mk_is_added_to_committee_as_chairperson(self.committee_1,
                                                           non_current_mk)
        self.given_mk_is_added_to_committee(self.committee_1, self.mk_1)

        res = self.client.get(self.committee_1.get_absolute_url())
        self.assertEqual(res.status_code, 200)

        self.verify_expected_members_in_context(res, [self.mk_1.pk])
        self.verify_unexpected_members_not_in_context(res, [non_current_mk.pk])

    def test_committeemeeting_by_tag(self):
        res = self.client.get(
            '%s?tagged=false' % reverse('committee-all-meetings'))
        self.assertQuerysetEqual(res.context['object_list'],
                                 ['<CommitteeMeeting: c1 - python>',
                                  '<CommitteeMeeting: c1 - django>'],
                                 )
        self.ti = TaggedItem._default_manager.create(
            tag=self.tag_1,
            content_type=ContentType.objects.get_for_model(CommitteeMeeting),
            object_id=self.meeting_1.id)
        res = self.client.get(
            reverse('committeemeeting-tag', args=[self.tag_1.name]))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res,
                                'committees/committeemeeting_list_by_tag.html')
        tag = res.context['tag']
        self.assertEqual(tag, self.tag_1)
        self.assertQuerysetEqual(res.context['object_list'],
                                 ['<CommitteeMeeting: c1 - django>'])
        res = self.client.get(
            '%s?tagged=false' % reverse('committee-all-meetings'))
        self.assertQuerysetEqual(res.context['object_list'],
                                 ['<CommitteeMeeting: c1 - python>'])
        # cleanup
        self.ti.delete()

    @waffle_testutils.override_flag('show_member_presence', active=True)
    def test_committee_has_show_presence_in_context_when_flag_is_set(
            self):
        res = self.client.get(self.committee_1.get_absolute_url())
        self.assertEqual(res.status_code, 200)

        self.verify_presence_data_in_response(res,
                                              is_expected_in_response=True)

    @waffle_testutils.override_flag('show_member_presence', active=False)
    def test_committee_does_not_show_presence_in_context_when_flag_is_unset(
            self):
        res = self.client.get(self.committee_1.get_absolute_url())
        self.assertEqual(res.status_code, 200)

        self.verify_presence_data_in_response(res,
                                              is_expected_in_response=False)
