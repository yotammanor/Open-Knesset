import datetime
import re
from urllib import urlencode
from xmlrpclib import Fault, loads

from backlinks.models import InboundBacklink
from backlinks.tests.xmlrpc import TestClientServerProxy
from django import template
from django.contrib.auth.models import User
from django.test import TestCase, Client

from committees.models import Committee
from laws.models import Law, PrivateProposal, Bill, Vote, VoteAction
from mks.mock import PINGABLE_MEMBER_ID
from mks.models import Party, Member
from mks.tests.base import TRACKBACK_CONTENT_TYPE


class MemberBacklinksViewsTestCase(TestCase):
    urls = 'mks.server_urls'

    def setUp(self):
        super(MemberBacklinksViewsTestCase, self).setUp()
        self.party_1 = Party.objects.create(name='party 1')
        self.party_2 = Party.objects.create(name='party 2')
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

        self.mk_1.save()
        self.mk_2.save()

        self.committee_1 = Committee.objects.create(name='c1')
        self.meeting_1 = self.committee_1.meetings.create(date=datetime.date.today() - datetime.timedelta(1),
                                                          protocol_text='jacob:\nI am a perfectionist\nadrian:\nI have a deadline')
        self.meeting_2 = self.committee_1.meetings.create(date=datetime.date.today() - datetime.timedelta(2),
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

        self.client = Client(SERVER_NAME='example.com')
        self.xmlrpc_client = TestClientServerProxy('/pingback/')
        self.PINGABLE_MEMBER_ID = str(self.mk_1.id)
        self.NON_PINGABLE_MEMBER_ID = str(self.mk_2.id)

    def trackbackPOSTRequest(self, path, params):
        return self.client.post(path, urlencode(params), content_type=TRACKBACK_CONTENT_TYPE)

    def assertTrackBackErrorResponse(self, response, msg):
        if response.content.find('<error>1</error>') == -1:
            raise self.failureException, msg

    '''
    def testTrackBackRDFTemplateTag(self):
        t = template.Template("{% load trackback_tags %}{% trackback_rdf object_url object_title trackback_url True %}")
        c = template.Context({'trackback_url': '/trackback/member/'+self.PINGABLE_MEMBER_ID+'/',
                              'object_url': self.pingableTargetUrl,
                              'object_title': 'Pingable Test Entry'})
        rendered = t.render(c)
        link_re = re.compile(r'dc:identifier="(?P<link>[^"]+)"')
        match = link_re.search(rendered)
        self.assertTrue(bool(match), 'TrackBack RDF not rendered')
        self.assertEquals(match.groups('link')[0], self.pingableTargetUrl,
                          'TrackBack RDF did not contain a valid target URI')
        ping_re = re.compile(r'trackback:ping="(?P<link>[^"]+)"')
        match = ping_re.search(rendered)
        self.assertTrue(bool(match), 'TrackBack RDF not rendered')
        self.assertEquals(match.groups('link')[0], '/trackback/member/'+self.PINGABLE_MEMBER_ID+'/',
                          'TrackBack RDF did not contain a TrackBack server URI')

    '''

    def testPingNonLinkingSourceURI(self):
        self.assertRaises(Fault,
                          self.xmlrpc_client.pingback.ping,
                          'http://example.com/bad-source-document/',
                          'http://example.com/member/' + PINGABLE_MEMBER_ID + '/')

        try:
            self.xmlrpc_client.pingback.ping('http://example.com/bad-source-document/',
                                             'http://example.com/member/' + PINGABLE_MEMBER_ID + '/')
        except Fault, f:
            self.assertEquals(f.faultCode,
                              17,
                              'Server did not return "source URI does not link" response')

    def testDisallowedMethod(self):
        response = self.client.get('/pingback/')
        self.assertEquals(response.status_code,
                          405,
                          'Server returned incorrect status code for disallowed HTTP method')

    def testNonExistentRPCMethod(self):
        self.assertRaises(Fault, self.xmlrpc_client.foo)

    def testBadPostData(self):
        post_data = urlencode({'sourceURI': 'http://example.com/good-source-document/',
                               'targetURI': 'http://example.com/member/' + PINGABLE_MEMBER_ID + '/'})
        response = self.client.post('/pingback/', post_data, TRACKBACK_CONTENT_TYPE)
        self.assertRaises(Fault,
                          loads,
                          response.content)

    def testPingNonExistentTargetURI(self):
        self.assertRaises(Fault,
                          self.xmlrpc_client.pingback.ping,
                          'http://example.com/member/non-existent-resource/',
                          'http://example.com/member/non-existent-resource')
        try:
            self.xmlrpc_client.pingback.ping('http://example.com/member/non-existent-resource/',
                                             'http://example.com/member/non-existent-resource')
        except Fault, f:
            self.assertEquals(f.faultCode,
                              32,
                              'Server did not return "target does not exist" error')

    def testPingAlreadyRegistered(self):
        self.xmlrpc_client.pingback.ping('http://example.com/another-good-source-document/',
                                         'http://example.com/member/' + PINGABLE_MEMBER_ID + '/')
        self.assertRaises(Fault,
                          self.xmlrpc_client.pingback.ping,
                          'http://example.com/another-good-source-document/',
                          'http://example.com/member/' + PINGABLE_MEMBER_ID + '/')

        try:
            self.xmlrpc_client.pingback.ping('http://example.com/another-good-source-document/',
                                             'http://example.com/member/' + PINGABLE_MEMBER_ID + '/')
        except Fault, f:
            self.assertEqual(f.faultCode,
                             48,
                             'Server did not return "ping already registered" error')

    def testPingbackLinkTemplateTag(self):
        t = template.Template("{% load pingback_tags %}{% pingback_link pingback_path %}")
        c = template.Context({'pingback_path': '/pingback/'})
        rendered = t.render(c)
        link_re = re.compile(r'<link rel="pingback" href="([^"]+)" ?/?>')
        match = link_re.search(rendered)
        self.assertTrue(bool(match), 'Pingback link tag did not render')
        self.assertEquals(match.groups(0)[0], 'http://example.com/pingback/',
                          'Pingback link tag rendered incorrectly')

    def testPingNonPingableTargetURI(self):
        self.assertRaises(Fault,
                          self.xmlrpc_client.pingback.ping,
                          'http://example.com/member/non-existent-resource/',
                          'http://example.com/member/' + str(self.NON_PINGABLE_MEMBER_ID) + '/')
        try:
            self.xmlrpc_client.pingback.ping('http://example.com/member/non-existent-resource/',
                                             'http://example.com/member/' + str(self.NON_PINGABLE_MEMBER_ID) + '/')
        except Fault, f:
            self.assertEquals(f.faultCode,
                              33,
                              'Server did not return "target not pingable" error')

    def testPingSourceURILinks(self):
        r = self.xmlrpc_client.pingback.ping('http://example.com/good-source-document/',
                                             'http://example.com/member/' + self.PINGABLE_MEMBER_ID + '/')

        self.assertEquals(r,
                          "Ping from http://example.com/good-source-document/ to http://example.com/member/1/ registered",
                          "Failed registering ping")

        registered_ping = InboundBacklink.objects.get(source_url='http://example.com/good-source-document/',
                                                      target_url='http://example.com/member/' + self.PINGABLE_MEMBER_ID + '/')
        self.assertEquals(str(registered_ping.target_object.id),
                          PINGABLE_MEMBER_ID,
                          'Server did not return "target not pingable" error')

    def testDisallowedTrackbackMethod(self):
        response = self.client.get('/trackback/member/' + PINGABLE_MEMBER_ID + '/')
        self.assertEquals(response.status_code,
                          405,
                          'Server returned incorrect status code for disallowed HTTP method')

    def testPingNoURLParameter(self):
        params = {'title': 'Example', 'excerpt': 'Example'}
        response = self.trackbackPOSTRequest('/trackback/member/' + self.PINGABLE_MEMBER_ID + '/',
                                             params)
        self.assertTrackBackErrorResponse(response,
                                          'Server did not return error response'
                                          'for ping with no URL parameter')

    def testPingBadURLParameter(self):
        params = {'url': 'bad url'}
        response = self.trackbackPOSTRequest('http://example.com/trackback/member/' + self.PINGABLE_MEMBER_ID + '/',
                                             params)
        self.assertTrackBackErrorResponse(response,
                                          'Server did not return error response for ping with bad URL parameter')

    def testPingNonExistentTarget(self):
        params = {'url': 'http://example.com/good-source-document/'}
        response = self.trackbackPOSTRequest('/trackback/member/5000/',
                                             params)
        self.assertTrackBackErrorResponse(response,
                                          'Server did not return error response for ping against non-existent resource')

    def testPingNonPingableTarget(self):
        params = {'url': 'http://example.com/member/' + PINGABLE_MEMBER_ID + '/'}
        response = self.trackbackPOSTRequest('/trackback/member/' + self.NON_PINGABLE_MEMBER_ID + '/',
                                             params)
        self.assertTrackBackErrorResponse(response,
                                          'Server did not return error response for ping against non-pingable resource')

    def testPingSuccess(self):
        title = 'Backlinks Test - Test Good Source Document'
        excerpt = 'This is a summary of the good source document'
        params = {'url': 'http://example.com/good-source-document/', 'title': title, 'excerpt': excerpt}
        track_target = '/trackback/member/' + self.PINGABLE_MEMBER_ID + '/'
        response = self.trackbackPOSTRequest(track_target,
                                             params)
        self.assertTrue(response.content.find('<error>0</error>') > -1,
                        'Server did not return success response for a valid ping request')
        registered_ping = InboundBacklink.objects.get(source_url='http://example.com/good-source-document/',
                                                      target_url='http://example.com' + self.mk_1.get_absolute_url())
        self.assertEquals(registered_ping.title,
                          title,
                          'Server did not use title from ping request when registering')
        self.assertEquals(registered_ping.excerpt,
                          excerpt,
                          'Server did not use excerpt from ping request when registering')

    def tearDown(self):
        super(MemberBacklinksViewsTestCase, self).tearDown()
        self.party_1.delete()
        self.party_2.delete()
        self.mk_1.delete()
        self.mk_2.delete()
        self.jacob.delete()
