# -*- coding: utf-8 -*
import unittest

from simple.parsers.utils import laws_parser_utils


class TestPrivateLawTitleParser(unittest.TestCase):

    def test_title_parser_with_regular_prefix(self):
        law_name = u'הצעת חוק עסקאות גופים ציבוריים (תיקון - מניעת העסקה במיקור חוץ בשירות הציבורי), התשע"ז - 2016'
        parsed_title = laws_parser_utils.parse_title(law_name)
        self.assertEqual(u'חוק עסקאות גופים ציבוריים', parsed_title.group(1).strip())

    def test_title_parser_with_hatzaa_prefix(self):
        law_name = u'הצעה חוק זכויות החולה (תיקון - תיקון פרק ז": אחראי לזכויות מטופל במוסד רפואי), התשע"ו-2016'
        parsed_title = laws_parser_utils.parse_title(law_name)
        self.assertEqual(u'חוק זכויות החולה', parsed_title.group(1).strip())