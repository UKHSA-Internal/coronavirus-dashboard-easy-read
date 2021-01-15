from unittest import TestCase
from .models import BaseModel


class TestCov9Api(TestCase):
    def setUp(self) -> None:
        self.model = BaseModel()

    def test_filter(self):
        pass
