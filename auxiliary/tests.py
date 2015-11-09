import datetime
import json
import re
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.utils import translation
from django.conf import settings
from tagging.models import Tag,TaggedItem
from laws.models import Vote, VoteAction, Bill, Law
from mks.models import Member,Party,WeeklyPresence,Knesset
from committees.models import Committee
from committees.models import CommitteeMeeting
from agendas.models import Agenda
from knesset.sitemap import sitemaps
from auxiliary.views import CsvView
from django.core import cache
from django.contrib.auth.models import User,Group,Permission

from tag_suggestions.tests import TestApprove, TestForm

class TagDetailViewTest(TestCase):

    def setUp(self):
        self.knesset1 = Knesset.objects.create(number=1,
                            start_date=datetime.datetime.today()-datetime.timedelta(days=3),
                            end_date=datetime.datetime.today()-datetime.timedelta(days=1))
        self.knesset2 = Knesset.objects.create(number=2,
                            start_date=datetime.datetime.today()-datetime.timedelta(days=1))
        self.committee_1 = Committee.objects.create(name='c1')
        self.committee_2 = Committee.objects.create(name='c2')
        self.meeting_1 = self.committee_1.meetings.create(date=datetime.datetime.now(),
                                 topics = "tagged meeting",
                                 protocol_text="tm1")
        self.meeting_1.create_protocol_parts()
        self.meeting_3 = self.committee_1.meetings.create(date=datetime.datetime.now(),
                                 topics = "untagged2",
                                 protocol_text='untagged')
        self.meeting_3.create_protocol_parts()
        self.meeting_4 = self.committee_1.meetings.create(date=datetime.datetime.now(),
                                 topics = "tagged_as_2",
                                 protocol_text='untagged')
        self.meeting_4.create_protocol_parts()
        self.meeting_2 = self.committee_1.meetings.create(date=datetime.datetime.now()-datetime.timedelta(days=2),
                                                         topics = "python",
                                                         protocol_text='m2')
        self.meeting_2.create_protocol_parts()
        self.jacob = User.objects.create_user('jacob', 'jacob@example.com',
                                              'JKM')
        self.adrian = User.objects.create_user('adrian', 'adrian@example.com',
                                              'ADRIAN')
        (self.group, created) = Group.objects.get_or_create(name='Valid Email')
        if created:
            self.group.save()
        self.group.permissions.add(Permission.objects.get(name='Can add annotation'))
        self.jacob.groups.add(self.group)

        ct = ContentType.objects.get_for_model(Tag)
        self.adrian.user_permissions.add(Permission.objects.get(codename='add_tag', content_type=ct))
        self.tag_1 = Tag.objects.create(name='tag1')
        self.tag_2 = Tag.objects.create(name='tag2')
        self.tag_3 = Tag.objects.create(name='tag3')

        self.vote_pre_time_1 = Vote.objects.create(title="vote pre time 1", time=datetime.datetime.now())
        self.vote_pre_time_2 = Vote.objects.create(title="vote pre time 2", time=datetime.datetime.now()-datetime.timedelta(days=2))
        self.vote_pre_time_3 = Vote.objects.create(title="vote pre time 3", time=datetime.datetime.now())
        self.vote_pre_time_4 = Vote.objects.create(title="vote pre time 4", time=datetime.datetime.now())
        self.bill_pre_1 = Bill.objects.create(stage='1', title='bill pre 1')
        self.bill_pre_2 = Bill.objects.create(stage='1', title='bill pre 2')
        self.bill_pre_3 = Bill.objects.create(stage='1', title='bill pre 3')
        self.bill_pre_4 = Bill.objects.create(stage='1', title='bill pre 4')
        Tag.objects.add_tag(self.bill_pre_1, 'tag1')
        Tag.objects.add_tag(self.bill_pre_2, 'tag1')
        Tag.objects.add_tag(self.bill_pre_4, 'tag2')
        self.bill_pre_1.pre_votes.add(self.vote_pre_time_1)
        self.bill_pre_2.pre_votes.add(self.vote_pre_time_2)
        self.bill_pre_3.pre_votes.add(self.vote_pre_time_3)
        self.bill_pre_4.pre_votes.add(self.vote_pre_time_4)

        
        self.vote_first_time_1 = Vote.objects.create(title="vote first time 1", time=datetime.datetime.now())
        self.vote_first_time_2 = Vote.objects.create(title="vote first time 2", time=datetime.datetime.now()-datetime.timedelta(days=2))
        self.vote_first_time_3 = Vote.objects.create(title="vote first time 3", time=datetime.datetime.now())
        self.vote_first_time_4 = Vote.objects.create(title="vote first time 4", time=datetime.datetime.now())
        self.bill_first_1 = Bill.objects.create(stage='1', title='bill first 1')
        self.bill_first_2 = Bill.objects.create(stage='1', title='bill first 2')
        self.bill_first_3 = Bill.objects.create(stage='1', title='bill first 3')
        self.bill_first_4 = Bill.objects.create(stage='1', title='bill first 4')
        Tag.objects.add_tag(self.bill_first_1, 'tag1')
        Tag.objects.add_tag(self.bill_first_2, 'tag1')
        Tag.objects.add_tag(self.bill_first_4, 'tag2')
        self.bill_first_1.first_vote=self.vote_first_time_1
        self.bill_first_2.first_vote=self.vote_first_time_2
        self.bill_first_3.first_vote=self.vote_first_time_3
        self.bill_first_4.first_vote=self.vote_first_time_4
        self.bill_first_1.save()
        self.bill_first_2.save()
        self.bill_first_3.save()
        self.bill_first_4.save()
        


        self.vote_approval_time_1 = Vote.objects.create(title="vote approval time 1", time=datetime.datetime.now())
        self.vote_approval_time_2 = Vote.objects.create(title="vote approval time 2", time=datetime.datetime.now()-datetime.timedelta(days=2))
        self.vote_approval_time_3 = Vote.objects.create(title="vote approval time 3", time=datetime.datetime.now())
        self.vote_approval_time_4 = Vote.objects.create(title="vote approval time 4", time=datetime.datetime.now())
        self.bill_approval_1 = Bill.objects.create(stage='1', title='bill approval 1')
        self.bill_approval_2 = Bill.objects.create(stage='1', title='bill approval 2')
        self.bill_approval_3 = Bill.objects.create(stage='1', title='bill approval 3')
        self.bill_approval_4 = Bill.objects.create(stage='1', title='bill approval 4')
        Tag.objects.add_tag(self.bill_approval_1, 'tag1')
        Tag.objects.add_tag(self.bill_approval_2, 'tag1')
        Tag.objects.add_tag(self.bill_approval_4, 'tag2')
        self.bill_approval_1.approval_vote=self.vote_approval_time_1
        self.bill_approval_2.approval_vote=self.vote_approval_time_2
        self.bill_approval_3.approval_vote=self.vote_approval_time_3
        self.bill_approval_4.approval_vote=self.vote_approval_time_4
        self.bill_approval_1.save()
        self.bill_approval_2.save()
        self.bill_approval_3.save()
        self.bill_approval_4.save()


        self.bill_first_meeting_1 = Bill.objects.create(stage='1', title='bill first meeting 1')
        self.bill_first_meeting_2 = Bill.objects.create(stage='1', title='bill first meeting 2')
        self.bill_first_meeting_3 = Bill.objects.create(stage='1', title='bill first meeting 3')
        self.bill_first_meeting_4 = Bill.objects.create(stage='1', title='bill first meeting 4')
        self.meeting_first_time_1 = self.committee_1.meetings.create(date=datetime.datetime.now(),
                                                         topics = "meeting first 1", protocol_text='mf1'
                                                         );self.meeting_first_time_1.create_protocol_parts()
        self.meeting_first_time_2 = self.committee_1.meetings.create(date=datetime.datetime.now()-datetime.timedelta(days=2),
                                                         topics = "meeting first 2", protocol_text='mf2'
                                                         );self.meeting_first_time_2.create_protocol_parts()
        self.meeting_first_time_3 = self.committee_1.meetings.create(date=datetime.datetime.now(),
                                                         topics = "meeting first 3", protocol_text='mf3'
                                                         );self.meeting_first_time_3.create_protocol_parts()
        self.meeting_first_time_4 = self.committee_1.meetings.create(date=datetime.datetime.now(),
                                                         topics = "meeting first 4", protocol_text='mf4'
                                                         );self.meeting_first_time_4.create_protocol_parts()
        Tag.objects.add_tag(self.bill_first_meeting_1, 'tag1')
        Tag.objects.add_tag(self.bill_first_meeting_2, 'tag1')
        Tag.objects.add_tag(self.bill_first_meeting_4, 'tag2')
        self.bill_first_meeting_1.first_committee_meetings.add(self.meeting_first_time_1)
        self.bill_first_meeting_2.first_committee_meetings.add(self.meeting_first_time_2)
        self.bill_first_meeting_3.first_committee_meetings.add(self.meeting_first_time_3)
        self.bill_first_meeting_4.first_committee_meetings.add(self.meeting_first_time_4)
        self.bill_first_meeting_1.save()
        self.bill_first_meeting_2.save()
        self.bill_first_meeting_3.save()
        self.bill_first_meeting_4.save()


        self.bill_second_meeting_1 = Bill.objects.create(stage='1', title='bill second meeting 1')
        self.bill_second_meeting_2 = Bill.objects.create(stage='1', title='bill second meeting 2')
        self.bill_second_meeting_3 = Bill.objects.create(stage='1', title='bill second meeting 3')
        self.bill_second_meeting_4 = Bill.objects.create(stage='1', title='bill second meeting 4')
        self.meeting_second_time_1 = self.committee_1.meetings.create(date=datetime.datetime.now(),
                                                         topics = "meeting second 1", protocol_text='ms1'
                                                         );self.meeting_second_time_1.create_protocol_parts()
        self.meeting_second_time_2 = self.committee_1.meetings.create(date=datetime.datetime.now()-datetime.timedelta(days=2),
                                                         topics = "meeting second 2", protocol_text='ms2'
                                                         );self.meeting_second_time_2.create_protocol_parts()
        self.meeting_second_time_3 = self.committee_1.meetings.create(date=datetime.datetime.now(),
                                                         topics = "meeting second 3", protocol_text='ms3'
                                                         );self.meeting_second_time_3.create_protocol_parts()
        self.meeting_second_time_4 = self.committee_1.meetings.create(date=datetime.datetime.now(),
                                                         topics = "meeting second 4", protocol_text='ms4'
                                                         );self.meeting_second_time_4.create_protocol_parts()
        Tag.objects.add_tag(self.bill_second_meeting_1, 'tag1')
        Tag.objects.add_tag(self.bill_second_meeting_2, 'tag1')
        Tag.objects.add_tag(self.bill_second_meeting_4, 'tag2')
        self.bill_second_meeting_1.first_committee_meetings.add(self.meeting_second_time_1)
        self.bill_second_meeting_2.first_committee_meetings.add(self.meeting_second_time_2)
        self.bill_second_meeting_3.first_committee_meetings.add(self.meeting_second_time_3)
        self.bill_second_meeting_4.first_committee_meetings.add(self.meeting_second_time_4)
        self.bill_second_meeting_1.save()
        self.bill_second_meeting_2.save()
        self.bill_second_meeting_3.save()
        self.bill_second_meeting_4.save()

        self.mk_1 = Member.objects.create(name='mk 1')
        self.topic = self.committee_1.topic_set.create(creator=self.jacob,
                                                title="hello", description="hello world")
                                                
        cm_ct = ContentType.objects.get_for_model(CommitteeMeeting)
        
        self.meeting_1.mks_attended.add(self.mk_1)
        
        TaggedItem._default_manager.get_or_create(tag=self.tag_1, content_type=cm_ct, object_id=self.meeting_1.id)
        TaggedItem._default_manager.get_or_create(tag=self.tag_1, content_type=cm_ct, object_id=self.meeting_2.id)
        TaggedItem._default_manager.get_or_create(tag=self.tag_2, content_type=cm_ct, object_id=self.meeting_4.id)
        
        
        
        self.vote_time_1 = Vote.objects.create(title="vote time 1", time=datetime.datetime.now())
        self.vote_time_2 = Vote.objects.create(title="vote time 2", time=datetime.datetime.now()-datetime.timedelta(days=2))
        self.vote_time_3 = Vote.objects.create(title="vote time 3", time=datetime.datetime.now())
        self.vote_time_4 = Vote.objects.create(title="vote time 4", time=datetime.datetime.now())
        
        vote_ct = ContentType.objects.get_for_model(Vote)
        TaggedItem._default_manager.get_or_create(tag=self.tag_1, content_type=vote_ct, object_id=self.vote_time_1.id)
        TaggedItem._default_manager.get_or_create(tag=self.tag_1, content_type=vote_ct, object_id=self.vote_time_2.id)
        TaggedItem._default_manager.get_or_create(tag=self.tag_2, content_type=vote_ct, object_id=self.vote_time_4.id)
        
        self.bill_dup_second_meeting = Bill.objects.create(stage='1', title='bill dup second meeting')
        self.meeting_dup_second_time_1 = self.committee_1.meetings.create(date=datetime.datetime.now(),
                                                         topics = "meeting second 1", protocol_text='ms1'
                                                         );self.meeting_dup_second_time_1.create_protocol_parts()
        self.meeting_dup_second_time_2 = self.committee_1.meetings.create(date=datetime.datetime.now(),
                                                         topics = "meeting second 2", protocol_text='ms2'
                                                         );self.meeting_dup_second_time_2.create_protocol_parts()
        Tag.objects.add_tag(self.bill_dup_second_meeting, 'tag3')
        self.bill_dup_second_meeting.first_committee_meetings.add(self.meeting_dup_second_time_1)
        self.bill_dup_second_meeting.first_committee_meetings.add(self.meeting_dup_second_time_2)
        self.bill_dup_second_meeting.save()

    def testDefaultKnessetId(self):
        res = self.client.get(reverse('tag-detail',kwargs={'slug':'tag1'}))
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'auxiliary/tag_detail.html')
        knesset_id = res.context['knesset_id'].number
        self.assertEqual(knesset_id,2)

    def testInvalidKnessetId(self):
        res = self.client.get(reverse('tag-detail',kwargs={'slug':'tag1'}), {'page':10})
        self.assertEqual(res.status_code, 404)
        
    def testCurrentSelectedKnessetId(self):
        res = self.client.get(reverse('tag-detail',kwargs={'slug':'tag1'}), {'page':2})
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'auxiliary/tag_detail.html')
        knesset_id = res.context['knesset_id'].number
        self.assertEqual(knesset_id,2)
    def testPrevSelectedKnessetId(self):
        res = self.client.get(reverse('tag-detail',kwargs={'slug':'tag1'}), {'page':1})
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'auxiliary/tag_detail.html')
        knesset_id = res.context['knesset_id'].number
        self.assertEqual(knesset_id,1)
        
    def testVisibleCommitteeMeetings(self):
        res = self.client.get(reverse('tag-detail',kwargs={'slug':'tag1'}), {'page':2})
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'auxiliary/tag_detail.html')
        cms = res.context['cms']
        expected_cms = set([
            "meeting first 1",
            "meeting second 1",
            "tagged meeting",
        ])
        self.assertEqual(set([cm.topics for cm in cms]), expected_cms)

    def testVisibleBills(self):
        res = self.client.get(reverse('tag-detail',kwargs={'slug':'tag1'}), {'page':2})
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'auxiliary/tag_detail.html')
        bills = res.context['bills']
        expected_bills = set([
            "bill pre 1",
            "bill first 1",
            "bill approval 1",
            "bill first meeting 1",
            "bill second meeting 1",
        ])
        self.assertEqual(set([b.title for b in bills]), expected_bills)

    def testUniqueBills(self):
        res = self.client.get(reverse('tag-detail',kwargs={'slug':'tag3'}), {'page':2})
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'auxiliary/tag_detail.html')
        bills = res.context['bills']
        self.assertEqual(len(bills), 1)
        self.assertEqual(bills[0].title, "bill dup second meeting")

    def testVisibleVotes(self):
        res = self.client.get(reverse('tag-detail',kwargs={'slug':'tag1'}), {'page':2})
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'auxiliary/tag_detail.html')
        votes = res.context['votes']
        expected_votes = set([
            "vote time 1",
            "vote approval time 1",
            "vote first time 1",
        ])
        self.assertEqual(set([v.title for v in votes]), expected_votes)





class TagVoteBillTagOrderTest(TestCase):

    def setUp(self):
        self.knesset1 = Knesset.objects.create(number=1,
                            start_date=datetime.datetime.today()-datetime.timedelta(days=3),
                            end_date=datetime.datetime.today()-datetime.timedelta(days=1))
        self.knesset2 = Knesset.objects.create(number=2,
                            start_date=datetime.datetime.today()-datetime.timedelta(days=1))
        self.committee_1 = Committee.objects.create(name='c1')
        self.committee_2 = Committee.objects.create(name='c2')
        self.jacob = User.objects.create_user('jacob', 'jacob@example.com',
                                              'JKM')
        self.adrian = User.objects.create_user('adrian', 'adrian@example.com',
                                              'ADRIAN')
        (self.group, created) = Group.objects.get_or_create(name='Valid Email')
        if created:
            self.group.save()
        self.group.permissions.add(Permission.objects.get(name='Can add annotation'))
        self.jacob.groups.add(self.group)

        ct = ContentType.objects.get_for_model(Tag)
        self.adrian.user_permissions.add(Permission.objects.get(codename='add_tag', content_type=ct))
        self.tag_1 = Tag.objects.create(name='tag1')
        self.tag_2 = Tag.objects.create(name='tag2')        



        self.vote_tag_before_vote = Vote.objects.create(title="vote tag before vote", time=datetime.datetime.now())
        self.bill_tag_before_vote = Bill.objects.create(stage='1', title='bill tag before vote')
        self.bill_tag_before_vote.save()
        Tag.objects.add_tag(self.bill_tag_before_vote, 'tag1')
        self.bill_tag_before_vote.approval_vote=self.vote_tag_before_vote
        self.bill_tag_before_vote.save()


        self.vote_tag_after_vote = Vote.objects.create(title="vote tag after vote", time=datetime.datetime.now())
        self.bill_tag_after_vote = Bill.objects.create(stage='1', title='bill tag after vote') #, approval_vote=self.vote_tag_after_vote)
        self.bill_tag_after_vote.approval_vote=self.vote_tag_after_vote
        self.bill_tag_after_vote.save()
        Tag.objects.add_tag(self.bill_tag_after_vote, 'tag1')
        
        self.vote_tag_after_vote_ctor = Vote.objects.create(title="vote tag after vote ctor", time=datetime.datetime.now())
        self.bill_tag_after_vote_ctor = Bill.objects.create(stage='1', title='bill tag after vote ctor', approval_vote=self.vote_tag_after_vote_ctor)
        self.vote_tag_after_vote_ctor.save()
        Tag.objects.add_tag(self.bill_tag_after_vote_ctor, 'tag1')
        
        self.vote_with_tag = Vote.objects.create(title="vote with tag", time=datetime.datetime.now())
        
        vote_ct = ContentType.objects.get_for_model(Vote)
        TaggedItem._default_manager.get_or_create(tag=self.tag_1, content_type=vote_ct, object_id=self.vote_with_tag.id)

    def testVisibleVotes(self):
        res = self.client.get(reverse('tag-detail',kwargs={'slug':'tag1'}), {'page':2})
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'auxiliary/tag_detail.html')
        votes = res.context['votes']
        expected_votes = set([
            "vote with tag",
            "vote tag before vote",
            "vote tag after vote",
            "vote tag after vote ctor",
        ]) 
        self.assertEqual(set([v.title for v in votes]), expected_votes)


        
class TagResourceTest(TestCase):

    def setUp(self):
        cache.cache.clear()
        self.tags = []
        self.tags.append(Tag.objects.create(name = 'tag1'))
        self.tags.append(Tag.objects.create(name = 'tag2'))
        self.tags.append(Tag.objects.create(name = 'tag3'))

        self.vote = Vote.objects.create(title="vote 1", time=datetime.datetime.now())
        ctype = ContentType.objects.get_for_model(Vote)
        TaggedItem._default_manager.get_or_create(tag=self.tags[0], content_type=ctype, object_id=self.vote.id)
        TaggedItem._default_manager.get_or_create(tag=self.tags[1], content_type=ctype, object_id=self.vote.id)
        self.law = Law.objects.create(title='law 1')
        self.bill = Bill.objects.create(stage='1',
                                          stage_date=datetime.date.today(),
                                          title='bill 1',
                                          law=self.law)
        self.bill2 = Bill.objects.create(stage='2',
                                          stage_date=datetime.date.today(),
                                          title='bill 2',
                                          law=self.law)
        Tag.objects.add_tag(self.bill, 'tag1')
        Tag.objects.add_tag(self.bill2, 'tag3')

    def _reverse_api(self, name, **args):
        args.update(dict(api_name='v2', resource_name='tag'))
        return reverse(name, kwargs=args)

    def test_api_tag_list(self):
        res = self.client.get(self._reverse_api('api_dispatch_list'))
        self.assertEqual(res.status_code, 200)
        res_json = json.loads(res.content)['objects']
        self.assertEqual(len(res_json), 3)
        self.assertEqual(set([x['name'] for x in res_json]), set(Tag.objects.values_list('name',flat=True)))

    def test_api_tag(self):
        res = self.client.get(self._reverse_api('api_dispatch_detail', pk = self.tags[0].id))
        self.assertEqual(res.status_code, 200)
        res_json = json.loads(res.content)
        self.assertEqual(res_json['name'], self.tags[0].name)

    def test_api_tag_not_found(self):
        res = self.client.get(self._reverse_api('api_dispatch_detail', pk = 12345))
        self.assertEqual(res.status_code, 404)

    def test_api_tag_for_vote(self):
        res = self.client.get(self._reverse_api('tags-for-object', app_label='laws',
                                                object_type='vote', object_id=self.vote.id))
        self.assertEqual(res.status_code, 200)
        res_json = json.loads(res.content)['objects']
        self.assertEqual(len(res_json), 2)

    def test_api_related_tags(self):
        res = self.client.get(self._reverse_api('related-tags', app_label='laws',
                                                object_type='law', object_id=self.law.id, related_name='bills'))
        self.assertEqual(res.status_code, 200)
        res_json = json.loads(res.content)['objects']
        self.assertEqual(len(res_json), 2)
        received_tags = set(Tag.objects.get(pk=x) for x in (res_json[0]['id'], res_json[1]['id']))
        self.assertEqual(received_tags, set([self.tags[0], self.tags[2]]))

class InternalLinksTest(TestCase):

    def setUp(self):
        Knesset.objects._current_knesset = None
        #self.vote_1 = Vote.objects.create(time=datetime.now(),title='vote 1')
        self.knesset = Knesset.objects.create(number=1,
                        start_date=datetime.date.today()-datetime.timedelta(days=100))
        self.party_1 = Party.objects.create(name='party 1', number_of_seats=4,
                                            knesset=self.knesset)
        self.vote_1 = Vote.objects.create(title="vote 1", time=datetime.datetime.now())
        self.mks = []
        self.plenum = Committee.objects.create(name='Plenum',type='plenum')
        self.voteactions = []
        self.num_mks = 4
        for i in range(self.num_mks):
            mk = Member.objects.create(name='mk %d' % i, current_party=self.party_1)
            wp = WeeklyPresence(member=mk,date=datetime.date.today(),hours=float(i))
            wp.save()
            self.mks.append(mk)
            if i<2:
                self.voteactions.append(VoteAction.objects.create(member=mk,type='for',vote=self.vote_1, party=mk.current_party))
            else:
                self.voteactions.append(VoteAction.objects.create(member=mk,type='against',vote=self.vote_1, party=mk.current_party))
        self.vote_1.controversy = min(self.vote_1.for_votes_count, self.vote_1.against_votes_count)
        self.vote_1.save()
        self.tags = []
        self.tags.append(Tag.objects.create(name = 'tag1'))
        self.tags.append(Tag.objects.create(name = 'tag2'))
        ctype = ContentType.objects.get_for_model(Vote)
        TaggedItem._default_manager.get_or_create(tag=self.tags[0], content_type=ctype, object_id=self.vote_1.id)
        TaggedItem._default_manager.get_or_create(tag=self.tags[1], content_type=ctype, object_id=self.vote_1.id)
        self.agenda = Agenda.objects.create(name="agenda 1 (public)", public_owner_name="owner", is_public=True)
        self.private_agenda = Agenda.objects.create(name="agenda 2 (private)", public_owner_name="owner")
        self.bill_1 = Bill.objects.create(stage='1', title='bill 1', popular_name="The Bill")
        ctype = ContentType.objects.get_for_model(Bill)
        TaggedItem._default_manager.get_or_create(tag=self.tags[0], content_type=ctype, object_id=self.bill_1.id)
        self.domain = 'http://' + Site.objects.get_current().domain

    def test_internal_links(self):
        """
        Internal links general test.
        This test reads the site, starting from the main page,
        looks for links, and makes sure all internal pages return HTTP200
        """
        from django.conf import settings
        translation.activate(settings.LANGUAGE_CODE)
        visited_links = set()

        test_pages = [reverse('main'), reverse('vote-list'),
                      reverse('bill-list'),
                      reverse('parties-members-list', kwargs={'pk': '1' })]

        redirects = [
            reverse('party-list'), reverse('member-list'),
        ]

        temp_redirects = [
            reverse('parties-members-index'),
        ]

        for page in test_pages:

            links_to_visit = []
            res = self.client.get(page)
            self.assertEqual(res.status_code, 200)
            visited_links.add(page)
            for link in re.findall("href=\"(.*?)\"",res.content):
                link = link.lower()
                self.failUnless(link, "There seems to be an empty link in %s (href='')" % page)
                if (link in visited_links or link.startswith("http") or
                        link.startswith("//") or link.startswith("#")):
                    continue
                if link.startswith("../"):
                    link = '/' + '/'.join(link.split('/')[1:])
                elif link.startswith("./"):
                    link = link[2:]
                elif link.startswith("."):
                    link = link[1:]
                if not link.startswith("/"): # relative
                    link = "%s%s" % (page,link)

                if link.find(settings.STATIC_URL)>=0: # skip testing static files
                    continue

                links_to_visit.append(link)

            while links_to_visit:
                link = links_to_visit.pop()
                res0 = self.client.get(link)

                if link in temp_redirects:
                    self.assertEqual(res0.status_code, 302, msg="internal (temporary) redirect %s from page %s seems to be broken" % (link,page))
                elif link in redirects:
                    self.assertEqual(res0.status_code, 301, msg="internal redirect %s from page %s seems to be broken" % (link,page))
                else:
                    self.assertEqual(res0.status_code, 200, msg="internal link %s from page %s seems to be broken" % (link,page))
                visited_links.add(link)

        # generate a txt file report of the visited links. for debugging the test
        #visited_links = list(visited_links)
        #visited_links.sort()
        #f = open('internal_links_tested.txt','wt')
        #f.write('\n'.join(visited_links))
        #f.close()


class SiteMapTest(TestCase):

    def setUp(self):
        pass

    def test_sitemap(self):
        res = self.client.get(reverse('sitemap'))
        self.assertEqual(res.status_code, 200)
        for s in sitemaps.keys():
            res = self.client.get(reverse('sitemaps', kwargs={'section':s}))
            self.assertEqual(res.status_code, 200, 'sitemap %s returned %d' %
                             (s,res.status_code))


class CsvViewTest(TestCase):

    class TestModel(object):
        def __init__(self, value):
            self.value = value

        def squared(self):
            return self.value ** 2

    class ConcreteCsvView(CsvView):
        filename = 'test.csv'
        list_display = (("value", "value"),
                        ("squared", "squared"))

    def test_csv_view(self):
        view = self.ConcreteCsvView()
        view.model = self.TestModel
        view.queryset = [self.TestModel(2), self.TestModel(3)]
        response = view.dispatch(None)
        rows = response.content.splitlines()
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[1], '2,4')
        self.assertEqual(rows[2], '3,9')
