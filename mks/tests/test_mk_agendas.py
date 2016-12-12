import datetime
import json

from django.contrib.sites.models import Site
from django.test import TestCase

from agendas.models import Agenda, AgendaVote
from laws.models import Vote, VoteAction
from mks.models import Knesset, Party, Member


class MKAgendasTestCase(TestCase):
    def setUp(self):
        super(MKAgendasTestCase, self).setUp()
        self.knesset = Knesset.objects.create(
            number=1,
            start_date=datetime.date(2010, 1, 1))
        self.party_1 = Party.objects.create(
            name='party 1',
            number_of_seats=1,
            knesset=self.knesset)
        self.mk_1 = Member.objects.create(name='mk_1',
                                          start_date=datetime.date(2010, 1, 1),
                                          current_party=self.party_1)

        self.mk_2 = Member.objects.create(name='mk_2',
                                          start_date=datetime.date(2010, 1, 1),
                                          current_party=self.party_1)

        self.mk_3 = Member.objects.create(name='mk_3',
                                          start_date=datetime.date(2010, 1, 1),
                                          current_party=self.party_1)

        self.agenda_1 = Agenda.objects.create(name='agenda 1',
                                              description='a bloody good agenda 1',
                                              public_owner_name='Dr. Jacob',
                                              is_public=True)
        self.agenda_2 = Agenda.objects.create(name='agenda 2',
                                              description='a bloody good agenda 2',
                                              public_owner_name='Greenpeace',
                                              is_public=True)
        self.agenda_3 = Agenda.objects.create(name='agenda 3',
                                              description='a bloody good agenda 3',
                                              public_owner_name='Hidden One',
                                              is_public=False)
        self.vote_1 = Vote.objects.create(title='vote 1', time=datetime.datetime.now())
        self.vote_2 = Vote.objects.create(title='vote 2', time=datetime.datetime.now())
        self.voteactions = [VoteAction.objects.create(vote=self.vote_1,
                                                      member=self.mk_1, type='for', party=self.mk_1.current_party),
                            VoteAction.objects.create(vote=self.vote_2,
                                                      member=self.mk_1, type='for', party=self.mk_1.current_party),
                            VoteAction.objects.create(vote=self.vote_1,
                                                      member=self.mk_2, type='against', party=self.mk_2.current_party),
                            VoteAction.objects.create(vote=self.vote_2,
                                                      member=self.mk_2, type='against', party=self.mk_2.current_party)
                            ]
        self.agendavotes = [AgendaVote.objects.create(agenda=self.agenda_1,
                                                      vote=self.vote_1,
                                                      score=-1,
                                                      reasoning="there's got to be a reason 1"),
                            AgendaVote.objects.create(agenda=self.agenda_2,
                                                      vote=self.vote_2,
                                                      score=0.5,
                                                      reasoning="there's got to be a reason 2"),
                            AgendaVote.objects.create(agenda=self.agenda_1,
                                                      vote=self.vote_2,
                                                      score=0.5,
                                                      reasoning="there's got to be a reason 3"),
                            ]

        self.domain = 'http://' + Site.objects.get_current().domain

    def testMemberValues(self):
        agenda_values1 = self.mk_1.get_agendas_values()
        self.assertEqual(len(agenda_values1), 2)
        agenda_values2 = self.mk_2.get_agendas_values()
        self.assertEqual(len(agenda_values2), 2)
        self.assertEqual(agenda_values1,
                         {1: {'numvotes': 2, 'rank': 2, 'score': -33.33, 'volume': 100.0},
                          2: {'numvotes': 1, 'rank': 1, 'score': 100.0, 'volume': 100.0}})
        self.assertEqual(agenda_values2,
                         {1: {'numvotes': 2, 'rank': 1, 'score': 33.33, 'volume': 100.0},
                          2: {'numvotes': 1, 'rank': 2, 'score': -100.0, 'volume': 100.0}})
        agenda_values = self.mk_3.get_agendas_values()
        self.assertFalse(agenda_values)

    def testAPIv2(self):
        res = self.client.get('/api/v2/member/%s/?format=json' % self.mk_1.id)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.content)
        self.assertEqual(data['name'], 'mk_1')
        self.assertEqual(data['party_name'], self.party_1.name)
        self.assertEqual(data['party_url'], self.party_1.get_absolute_url())
        agendas_uri = data['agendas_uri']
        expected_agendas_uri = '/api/v2/member-agendas/%s/' % self.mk_1.id
        self.assertEqual(agendas_uri, expected_agendas_uri, "Wrong agendas URI returned for member")
        res2 = self.client.get(expected_agendas_uri + '?format=json')
        agendas = json.loads(res2.content)
        self.assertEqual(agendas['agendas'], [
            {'id': 1, 'owner': 'Dr. Jacob', 'absolute_url': '/agenda/1/',
             'score': -33.33, 'name': 'agenda 1', 'rank': 2,
             'min': -33.33, 'max': 33.33,
             'party_min': -33.33, 'party_max': 33.33,
             },
            {'id': 2, 'owner': 'Greenpeace', 'absolute_url': '/agenda/2/',
             'score': 100.0, 'name': 'agenda 2', 'rank': 1,
             'min': -100.0, 'max': 100.0,
             'party_min': -100.0, 'party_max': 100.0,
             }])

    def tearDown(self):
        super(MKAgendasTestCase, self).tearDown()
        for av in self.agendavotes:
            av.delete()
        for va in self.voteactions:
            va.delete()
        self.vote_1.delete()
        self.vote_2.delete()
        self.mk_1.delete()
        self.mk_2.delete()
        self.party_1.delete()
        self.agenda_1.delete()
        self.agenda_2.delete()
        self.agenda_3.delete()
