"""
Error Handler Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from service import talisman
from service.common import status  # HTTP Status Codes
from service.routes import app

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

NOT_FOUND_URL = "/unknown"
ACCOUNTS_BASE_URL = "/accounts"

######################################################################
#  T E S T   C A S E S
######################################################################
class TestErrorHandler(TestCase):
    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.logger.setLevel(logging.CRITICAL)
        talisman.force_https = False

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()

    def test_method_not_allowed(self):
        """It should not allow an illegal method call"""
        resp = self.client.delete(ACCOUNTS_BASE_URL)
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_method_not_found(self):
        """It should not allow an illegal method call"""
        resp = self.client.get(NOT_FOUND_URL)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)        