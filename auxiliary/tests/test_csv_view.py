# -*- coding: utf-8 -*
from django.test.testcases import TestCase

from auxiliary.mixins import CsvView


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