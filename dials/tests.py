# -*- coding: utf-8 -*
from django.core.urlresolvers import reverse
from django.test import TestCase

from dials.models import Dial


class DialTestCase(TestCase):

    def test_dial_pages(self):
        Dial.objects.create(slug="dial", precent="42",
                description="ככה")
        ret = self.client.get(reverse('dial-svg',
                                        kwargs={'slug': "dial"}))
        self.assertGreater(ret.content.index('42'), 0)
        ret = self.client.get(reverse('dial-desc',
                                        kwargs={'slug': "dial"}))
        self.assertGreater(ret.content.index('ככה'), 0)

