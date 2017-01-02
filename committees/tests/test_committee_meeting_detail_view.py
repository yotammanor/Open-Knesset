import unittest
from datetime import datetime, timedelta

from actstream.models import Action
from annotatetext.models import Annotation
from django.conf import settings
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse

from tagging.models import Tag
from waffle import testutils as waffle_testutils

from committees.models import Committee
from committees.tests.base import BaseCommitteeTestCase
from laws.models import Bill
from mks.models import Member, Knesset

APP = 'committees'


class CommitteeMeetingDetailViewTestCase(BaseCommitteeTestCase):
    def setUp(self):
        super(CommitteeMeetingDetailViewTestCase, self).setUp()
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
        self.given_mk_attended_meeting(self.meeting_1, self.mk_1)

    def given_mk_attended_meeting(self, meeting, mk):
        meeting.mks_attended.add(mk)

    def tearDown(self):
        super(CommitteeMeetingDetailViewTestCase, self).tearDown()
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

    def test_protocol_parts_return_correctly(self):
        parts_list = self.meeting_1.parts.list()
        self.assertEqual(parts_list.count(), 2)
        self.assertEqual(parts_list[0].header, u'jacob')
        self.assertEqual(parts_list[0].body, 'I am a perfectionist')
        self.assertEqual(parts_list[1].header, u'adrian')
        self.assertEqual(parts_list[1].body, 'I have a deadline')

    def test_annotating_protocol_part(self):
        '''this is more about testing the annotatext app '''
        self.assertTrue(self.client.login(username='jacob', password='JKM'))
        part = self.meeting_1.parts.list()[0]
        res = self._given_protocol_annotation(part)
        self.assertEqual(res.status_code, 302)
        annotation = Annotation.objects.get(object_id=part.id,
                                            content_type=ContentType.objects.get_for_model(
                                                part).id)
        self.assertEqual(annotation.selection, 'perfect')
        # ensure the activity has been recorded
        stream = Action.objects.stream_for_actor(self.jacob)
        self.assertEqual(stream.count(), 2)
        self.assertEqual(stream[0].verb, 'started following')
        self.assertEqual(stream[0].target.id, self.meeting_1.id)
        self.assertEqual(stream[1].verb, 'annotated')
        self.assertEqual(stream[1].target.id, annotation.id)
        # ensure we will see it on the committee page
        annotations = self.committee_1.annotations
        self.assertEqual(annotations.count(), 1)
        self.assertEqual(annotations[0].comment, 'just perfect')
        # test the deletion of an annotation
        annotation.delete()
        stream = Action.objects.stream_for_actor(self.jacob)
        self.assertEqual(stream.count(), 1)

    def test_adding_and_removing_two_annotation_to_protocol(self):
        '''create two annotations on same part, and delete them'''
        self.assertTrue(self.client.login(username='jacob', password='JKM'))
        part = self.meeting_1.parts.list()[0]
        res = self._given_protocol_annotation(part)
        self.assertEqual(res.status_code, 302)
        res = self.client.post(reverse('annotatetext-post_annotation'),
                               {'selection_start': 8,
                                'selection_end': 15,
                                'flags': 0,
                                'color': '#000',
                                'lengthcheck': len(part.body),
                                'comment': 'not quite',
                                'object_id': part.id,
                                'content_type': ContentType.objects.get_for_model(
                                    part).id,
                                })
        self.assertEqual(res.status_code, 302)

        annotations = Annotation.objects.filter(object_id=part.id,
                                                content_type=ContentType.objects.get_for_model(
                                                    part).id)
        self.assertEqual(annotations.count(), 2)
        # ensure we will see it on the committee page
        c_annotations = self.committee_1.annotations
        self.assertEqual(c_annotations.count(), 2)
        self.assertEqual(c_annotations[0].comment, 'just perfect')
        self.assertEqual(c_annotations[1].comment, 'not quite')
        # test the deletion of an annotation
        annotations[0].delete()
        c_annotations = self.committee_1.annotations
        self.assertEqual(c_annotations.count(), 1)

    def test_cannot_annotate_without_known_email(self):
        self.jacob.groups.clear()  # invalidate this user's email
        self.assertTrue(self.client.login(username='jacob', password='JKM'))
        part = self.meeting_1.parts.list()[0]
        res = self._given_protocol_annotation(part)
        self.assertEqual(res.status_code,
                         403)  # 403 Forbidden. 302 means a user with unverified email has posted an annotation.

    def _given_protocol_annotation(self, part):
        return self.client.post(reverse('annotatetext-post_annotation'),
                                {'selection_start': 7,
                                 'selection_end': 14,
                                 'flags': 0,
                                 'color': '#000',
                                 'lengthcheck': len(part.body),
                                 'comment': 'just perfect',
                                 'object_id': part.id,
                                 'content_type': ContentType.objects.get_for_model(
                                     part).id,
                                 })

    def test_committee_meeting_returns_correct_members(self):
        res = self.client.get(self.meeting_1.get_absolute_url())
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res,
                                'committees/committeemeeting_detail.html')
        self.verify_expected_members_in_context(res, [self.mk_1.id])

    def test_mk_from_current_knesset_that_are_not_current_members_are_also_displayed(
            self):
        not_current_mk = Member.objects.create(name='mk is no more',
                                               is_current=False)
        self.given_mk_attended_meeting(self.meeting_1, not_current_mk)
        self._given_mk_added_to_meeting(self.meeting_1, not_current_mk)
        res = self.client.get(self.meeting_1.get_absolute_url())
        self.assertEqual(res.status_code, 200)
        self.verify_expected_members_in_context(res, [self.mk_1.id,
                                                      not_current_mk.pk])

    def test_user_can_not_add_a_bill_to_meetings_if_not_login(self):
        res = self.client.post(reverse('committee-meeting',
                                       kwargs={'pk': self.meeting_1.id}))
        self._verify_bill_not_in_meeting(self.bill_1, self.meeting_1)
        self.assertEqual(res.status_code, 302)
        self.assertTrue(res['location'].startswith('%s%s' %
                                                   ('http://testserver',
                                                    settings.LOGIN_URL)))

    def test_post_removing_and_adding_mk_to_committee_meetings(self):
        mk_1 = self.mk_1
        meeting = self.meeting_1
        self._verify_mk_has_meeting(meeting, mk_1)
        self.assertTrue(self.client.login(username='jacob', password='JKM'))
        res = self._given_mk_removed_from_meeting(meeting, mk_1)
        self.assertEqual(res.status_code, 302)

        self._verify_mk_does_not_have_meeting(meeting, mk_1)
        res = self._given_mk_added_to_meeting(meeting, mk_1)
        self.assertEqual(res.status_code, 302)
        self._verify_mk_has_meeting(meeting, mk_1)

    def test_post_removing_and_adding_mk_without_params_get_404_response(self):
        mk_1 = self.mk_1
        mk_1.name = ''
        meeting = self.meeting_1
        self._verify_mk_has_meeting(meeting, mk_1)
        self.assertTrue(self.client.login(username='jacob', password='JKM'))
        res = self._given_mk_removed_from_meeting(meeting, mk_1)
        self.assertEqual(res.status_code, 404)

        self._verify_mk_has_meeting(meeting, mk_1)
        res = self._given_mk_added_to_meeting(meeting, mk_1)
        self.assertEqual(res.status_code, 404)

    def test_post_adds_bill_to_committee_meeting(self):
        bill_1 = self.bill_1
        meeting = self.meeting_1
        self._verify_bill_not_in_meeting(bill_1, meeting)
        self.assertTrue(self.client.login(username='jacob', password='JKM'))
        res = self._given_bill_added_to_meeting(bill_1, meeting)
        self.assertEqual(res.status_code, 302)
        self._verify_bill_in_meeting(bill_1, meeting)

    def test_post_adds_and_removes_lobbyist_to_committee_meeting(self):
        lobbyist = self._setup_lobbyist()
        meeting = self.meeting_1
        self._verify_lobbyist_not_mentioned_in_meetings(lobbyist, meeting)
        self.assertTrue(self.client.login(username='jacob', password='JKM'))
        res = self._given_lobbyist_added_to_meeting(meeting, lobbyist)
        self.assertEqual(res.status_code, 302)
        self._verify_lobbyist_mentioned_in_meetings(lobbyist, meeting)

        res = self._given_lobbyist_removed_from_meeting(meeting, lobbyist)
        self._verify_lobbyist_not_mentioned_in_meetings(lobbyist, meeting)

    def test_post_adds_and_removes_lobbyist_by_aliased_name(self):
        lobbyist = self._setup_lobbyist()
        alias = self._setup_alias_for_person(lobbyist.person)
        meeting = self.meeting_1
        self._verify_lobbyist_not_mentioned_in_meetings(lobbyist, meeting)
        self.assertTrue(self.client.login(username='jacob', password='JKM'))
        res = self._given_lobbyist_added_to_meeting(meeting,
                                                    lobbyist_name=alias.name)
        self.assertEqual(res.status_code, 302)
        self._verify_lobbyist_mentioned_in_meetings(lobbyist, meeting)

        res = self._given_lobbyist_removed_from_meeting(meeting,
                                                        lobbyist_name=alias.name)
        self._verify_lobbyist_not_mentioned_in_meetings(lobbyist, meeting)

    def test_adding_non_existent_lobbyist_returns_404(self):
        self.assertTrue(self.client.login(username='jacob', password='JKM'))
        meeting = self.meeting_1
        res = self._given_lobbyist_added_to_meeting(meeting,
                                                    lobbyist_name='non existing')
        self.assertEqual(res.status_code, 404)

    def test_committee_meetings_handles_missing_lobbyist_data(self):
        lobbyist = self._setup_lobbyist()

        meeting = self.meeting_1

        self.assertTrue(self.client.login(username='jacob', password='JKM'))
        self._given_lobbyist_added_to_meeting(meeting, lobbyist=lobbyist)
        res = self.client.get(self.meeting_1.get_absolute_url())
        self.assertEqual(res.status_code, 200)

        lobbyist.data.all().delete()

        res = self.client.get(self.meeting_1.get_absolute_url())
        self.assertEqual(res.status_code, 200)

    def test_add_tag_committee_login_required(self):
        url = reverse('add-tag-to-object',
                      kwargs={'app': APP,
                              'object_type': 'committeemeeting',
                              'object_id': self.meeting_1.id})
        res = self.client.post(url, {'tag_id': self.tag_1})
        self.assertRedirects(res, "%s?next=%s" % (settings.LOGIN_URL, url),
                             status_code=302)

    def test_post_adds_tag_to_meeting(self):
        self.assertNotIn(self.tag_1, self.meeting_1.tags)
        self.assertTrue(self.client.login(username='jacob', password='JKM'))
        url = reverse('add-tag-to-object',
                      kwargs={'app': APP,
                              'object_type': 'committeemeeting',
                              'object_id': self.meeting_1.id})
        res = self.client.post(url, {'tag_id': self.tag_1.id})
        self.assertEqual(res.status_code, 200)
        self.assertIn(self.tag_1, self.meeting_1.tags)

    @unittest.skip("creating tags currently disabled")
    def test_create_tag_permission_required(self):
        self.assertTrue(self.client.login(username='jacob', password='JKM'))
        url = reverse('create-tag',
                      kwargs={'app': APP,
                              'object_type': 'committeemeeting',
                              'object_id': self.meeting_1.id})
        res = self.client.post(url, {'tag': 'new tag'})
        self.assertRedirects(res, "%s?next=%s" % (settings.LOGIN_URL, url),
                             status_code=302)

    @unittest.skip("creating tags currently disabled")
    def test_create_tag(self):
        self.assertTrue(self.client.login(username='adrian',
                                          password='ADRIAN'))
        url = reverse('create-tag',
                      kwargs={'app': APP,
                              'object_type': 'committeemeeting',
                              'object_id': self.meeting_1.id})
        res = self.client.post(url, {'tag': 'new tag'})
        self.assertEqual(res.status_code, 200)
        self.new_tag = Tag.objects.get(name='new tag')
        self.assertIn(self.new_tag, self.meeting_1.tags)

    @waffle_testutils.override_flag('show_member_presence', active=True)
    def test_meeting_has_show_presence_in_context_when_flag_is_set(
            self):
        res = self.client.get(self.meeting_1.get_absolute_url())
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.context['show_member_presence'],
                        msg="context property 'show_member_presence'"
                            " was not set to True.")

    @waffle_testutils.override_flag('show_member_presence', active=False)
    def test_meeting_does_not_show_presence_in_context_when_flag_is_unset(
            self):
        res = self.client.get(self.meeting_1.get_absolute_url())
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.context['show_member_presence'],
                         msg="context property 'show_member_presence'"
                             " was not set to False.")
