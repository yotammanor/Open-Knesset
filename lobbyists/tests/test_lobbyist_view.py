# -*- coding: utf-8 -*
from django.core.urlresolvers import reverse
from django.test import TestCase

from lobbyists.models import Lobbyist
from persons.models import Person


class LobbyistDetailViewTestCase(TestCase):
    def setUp(self):
        return super(LobbyistDetailViewTestCase, self).setUp()

    def tearDown(self):
        return super(LobbyistDetailViewTestCase, self).tearDown()

    def given_lobbyist_exists(self, name='kressni'):
        person = Person.objects.create(name=name)
        return Lobbyist.objects.create(person=person)

    def test_endpoint_returns_lobbyist(self):
        kresni = self.given_lobbyist_exists()
        res = self.client.get(reverse('lobbyist-detail', args=[kresni.pk]))

        self.assertEqual(res.status_code, 200)

    def test_endpoint_returns_lobbyist_with_missing_data(self):
        kresni = self.given_lobbyist_exists()
        kresni.data.all().delete()
        res = self.client.get(reverse('lobbyist-detail', args=[kresni.pk]))

        self.assertEqual(res.status_code, 200)
