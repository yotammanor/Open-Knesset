# -*- coding: utf-8 -*
from django.core.urlresolvers import reverse
from django.test import TestCase

from lobbyists.models import Lobbyist
from persons.models import Person, PersonAlias

just_id = lambda x: x.id


class BaseCommitteeTestCase(TestCase):
    def setUp(self):
        super(BaseCommitteeTestCase, self).setUp()

    def tearDown(self):
        super(BaseCommitteeTestCase, self).tearDown()

    def verify_expected_members_in_context(self, res, expected_mks):
        members = res.context['members']
        self.assertEqual(map(just_id, members),
                         expected_mks,
                         'members has wrong objects: %s' % members)

    def verify_unexpected_members_not_in_context(self, res,
                                                 unexpected_members):
        members = res.context['members']
        self.assertNotIn(unexpected_members, map(just_id, members),
                         'members has wrong objects: %s' % members)

    def _given_mk_added_to_meeting(self, meeting, mk):
        return self.client.post(reverse('committee-meeting',
                                        kwargs={'pk': meeting.id}),
                                {'user_input_type': 'mk',
                                 'mk_name': mk.name})

    def _given_mk_removed_from_meeting(self, meeting, mk):
        return self.client.post(reverse('committee-meeting',
                                        kwargs={'pk': meeting.id}),
                                {'user_input_type': 'remove-mk',
                                 'mk_name_to_remove': mk.name})

    def _given_lobbyist_added_to_meeting(self, meeting, lobbyist=None,
                                         lobbyist_name=None):
        lobbyist_name = lobbyist.person.name if lobbyist else lobbyist_name
        return self.client.post(reverse('committee-meeting',
                                        kwargs={'pk': meeting.id}),
                                {'user_input_type': 'add-lobbyist',
                                 'lobbyist_name': lobbyist_name})

    def _given_lobbyist_removed_from_meeting(self, meeting, lobbyist=None,
                                             lobbyist_name=None):
        lobbyist_name = lobbyist.person.name if lobbyist else lobbyist_name
        return self.client.post(reverse('committee-meeting',
                                        kwargs={'pk': meeting.id}),
                                {'user_input_type': 'remove-lobbyist',
                                 'lobbyist_name': lobbyist_name})

    def _verify_mk_does_not_have_meeting(self, meeting, mk_1):
        self.assertFalse(meeting in mk_1.committee_meetings.all())

    def _verify_mk_has_meeting(self, meeting, mk_1):
        self.assertTrue(meeting in mk_1.committee_meetings.all())

    def _verify_bill_in_meeting(self, bill_1, meeting):
        self.assertTrue(bill_1 in meeting.bills_first.all())

    def _given_bill_added_to_meeting(self, bill_1, meeting):
        return self.client.post(reverse('committee-meeting',
                                        kwargs={'pk':
                                                    meeting.id}),
                                {'user_input_type': 'bill',
                                 'bill_id': bill_1.id})

    def _verify_bill_not_in_meeting(self, bill_1, meeting):
        self.assertFalse(bill_1 in meeting.bills_first.all())

    def _verify_lobbyist_mentioned_in_meetings(self, lobbyist, meeting):
        self.assertTrue(lobbyist in meeting.lobbyists_mentioned.all())

    def _verify_lobbyist_not_mentioned_in_meetings(self, lobbyist, meeting):
        self.assertFalse(lobbyist in meeting.lobbyists_mentioned.all())

    def verify_presence_data_in_response(self, res, is_expected_in_response):
        self._verify_attribute_in_response_context_equals_to_value(
            res,
            attribute='show_member_presence',
            value=is_expected_in_response
        )

    def _verify_attribute_in_response_context_equals_to_value(self, res,
                                                              attribute,
                                                              value):
        self.assertIn(attribute, res.context,
                      msg="attribute {} should exists in response context, "
                          "but isn't.".format(attribute))

        attr_val = res.context[attribute]
        self.assertEquals(attr_val, value,
                          msg="context property {} Should be of value {}, "
                              "but is {}.".format(attribute, value, attr_val))

    def _setup_lobbyist(self, name='kressni'):
        person = Person.objects.create(name=name)
        return Lobbyist.objects.create(person=person)

    def _setup_alias_for_person(self, person, alias_name='alias_name'):
        return PersonAlias.objects.create(person=person, name=alias_name)

    def given_mk_is_added_to_committee(self, committee, mk):
        committee.members.add(mk)

    def given_mk_is_added_to_committee_as_replacment(self, committee, mk):
        committee.replacements.add(mk)

    def given_mk_is_added_to_committee_as_chairperson(self, committee, mk):
        committee.chairpersons.add(mk)
