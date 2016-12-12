import datetime
import json

from tastypie.test import ResourceTestCase

from mks.managers import KnessetManager
from mks.models import Knesset, Party, Member
from mmm.models import Document
from persons.models import PersonAlias, Person


class MemberAPITestCase(ResourceTestCase):
    def setUp(self):
        super(MemberAPITestCase, self).setUp()

        d = datetime.date.today()
        self.knesset = Knesset.objects.create(
            number=1,
            start_date=d - datetime.timedelta(10))
        KnessetManager._current_knesset = self.knesset
        self.party_1 = Party.objects.create(name='party 1',
                                            knesset=self.knesset)

        matches = [{
                       "entity_id": 10012 + i,
                       "docid": "m00079",
                       "entity_name": "bbbb",
                       "entity_type": "COMM",
                       "url": "http://knesset.gov.il/mmm/data/pdf/m00079.pdf" + str(i),
                       "title": "aaaaaa" + str(i),
                       "authors": [
                           "mk_1"
                       ],
                       "pub_date": "2000-01-01",
                       "session_date": None,
                       "heading": "bbbb",
                   } for i in xrange(10)]

        for match in matches:
            match['date'] = datetime.datetime.strptime(match['pub_date'], '%Y-%m-%d').date()

        self.mmm_docs = [Document.objects.create(
            url=match['url'],
            title=match['title'],
            publication_date=match['pub_date'],
            author_names=match['authors'],
        ) for match in matches]

        self.mk_1 = Member.objects.create(name='mk_1',
                                          start_date=datetime.date(2010, 1, 1),
                                          current_party=self.party_1,
                                          backlinks_enabled=True,
                                          bills_stats_first=2,
                                          bills_stats_proposed=5,
                                          average_weekly_presence_hours=3.141)
        for mmm_doc in self.mmm_docs:
            mmm_doc.req_mks = [self.mk_1, ]
        PersonAlias.objects.create(name="mk_1_alias",
                                   person=Person.objects.get(mk=self.mk_1))

    def testSimpleGet(self):
        res1 = self.api_client.get('/api/v2/member/', data={'name': 'mk_1'})
        self.assertValidJSONResponse(res1)
        ret = self.deserialize(res1)
        self.assertEqual(ret['meta']['total_count'], 1)

    def testAliases(self):
        res1 = self.api_client.get('/api/v2/member/', data={'name': 'mk_1'}, format='json')
        self.assertValidJSONResponse(res1)
        res2 = self.api_client.get('/api/v2/member/', data={'name': 'mk_1_alias'}, format='json')
        self.assertValidJSONResponse(res2)
        self.assertEqual(self.deserialize(res1), self.deserialize(res2))

    def testMemberList(self):
        res1 = self.api_client.get('/api/v2/member/', format='json')
        self.assertEqual(res1.status_code, 200)
        data = json.loads(res1.content)

        self.assertEqual(len(data['objects']), 1)
        rmks = data['objects'][0]
        self.assertEqual(rmks['mmms_count'], 10)
        self.assertEqual(rmks['bills_stats_first'], 2)
        self.assertEqual(rmks['bills_stats_proposed'], 5)
        self.assertEqual(rmks['average_weekly_presence_hours'], 3.141)

    def tearDown(self):
        super(MemberAPITestCase, self).tearDown()
        for mmm_doc in self.mmm_docs:
            mmm_doc.delete()
        self.mk_1.delete()
        KnessetManager._current_knesset = None
