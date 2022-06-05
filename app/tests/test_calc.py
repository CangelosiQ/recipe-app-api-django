"""
"""
from django.test import SimpleTestCase

from app import calc


class CalcTests(SimpleTestCase):
    def test_add(self):
        assert calc.add(2, 3) == 5
