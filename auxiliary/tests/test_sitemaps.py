# -*- coding: utf-8 -*
from django.core.urlresolvers import reverse
from django.test.testcases import TestCase

from knesset.sitemap import sitemaps


class SiteMapTest(TestCase):
    def setUp(self):
        pass

    def test_sitemap(self):
        res = self.client.get(reverse('sitemap'))
        self.assertEqual(res.status_code, 200)
        for s in sitemaps.keys():
            res = self.client.get(reverse('sitemaps', kwargs={'section': s}))
            self.assertEqual(res.status_code, 200, 'sitemap %s returned %d' %
                             (s, res.status_code))