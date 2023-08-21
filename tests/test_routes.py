"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service import talisman
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

ACCOUNT_BASE_URL = "/account"
ACCOUNTS_BASE_URL = "/accounts"
HTTPS_ENVIRON = {'wsgi.url_scheme': 'https'}

######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)
        talisman.force_https = False

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(ACCOUNTS_BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            ACCOUNTS_BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        self.assert_account(response.get_json(), account)

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(ACCOUNTS_BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            ACCOUNTS_BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ADD YOUR TEST CASES HERE ...
    def test_read_account_found_returns_200_with_expected_account(self):
        """It should read a newly created account"""
        account = AccountFactory()
        response = self.client.post(
            ACCOUNTS_BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        account_id = (response.get_json())["id"]

        response = self.client.get(
           ACCOUNT_BASE_URL + "/" + str(account_id)
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assert_account(response.get_json(), account)

    def test_read_account_not_found_returns_404(self):
        """It should return 404 for an invalid account id"""

        response = self.client.get(
           ACCOUNT_BASE_URL + "/" + str(0)
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_accounts_returns_accounts(self):
        """It should return all accounts"""

        response = self.client.get(
            ACCOUNTS_BASE_URL
        )

        self.assertEqual(len(response.get_json()), 0)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self._create_accounts(5)

        response = self.client.get(
            ACCOUNTS_BASE_URL
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.get_json()), 5)

    def test_update_acount_for_known_account_correctly_updates_account(self):
        """It should create and then update the account"""
        account = AccountFactory()
        response = self.client.post(
            ACCOUNTS_BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_account = response.get_json()
        new_account["name"] = "New Name"
        response = self.client.put(
            f"{ACCOUNT_BASE_URL}/{new_account['id']}",
            json=new_account,
            content_type="application/json"
        )
        account.name = "New Name"
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assert_account(response.get_json(), account)

    def test_update_acount_for_unknown_account_returns_404(self):
        """It should return 404 for an unknown account"""

        response = self.client.put(
            f"{ACCOUNT_BASE_URL}/0",
            json={},
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_account_for_known_account(self):
        """It should create and then delete the account"""
        account = AccountFactory()
        response = self.client.post(
            ACCOUNTS_BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        account_id = response.get_json()['id']
        response = self.client.delete(
            f"{ACCOUNT_BASE_URL}/{account_id}",
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.client.get(
            f"{ACCOUNT_BASE_URL}/{account_id}",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_account_for_unknown_account(self):
        """It should do nothing and return 200"""

        response = self.client.delete(
            f"{ACCOUNT_BASE_URL}/0",
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)    

    def test_security_headers(self):
        """It should return security headers"""
        response = self.client.get('/', environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        headers = {
            'X-Frame-Options': 'SAMEORIGIN',
            'X-Content-Type-Options': 'nosniff',
            'Content-Security-Policy': 'default-src \'self\'; object-src \'none\'',
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        for key, value in headers.items():
            self.assertEqual(response.headers.get(key), value)

    def assert_account(self, actual_account, expected_account):
        self.assertEqual(actual_account["name"], expected_account.name)
        self.assertEqual(actual_account["email"], expected_account.email)
        self.assertEqual(actual_account["address"], expected_account.address)
        self.assertEqual(actual_account["phone_number"], expected_account.phone_number)
        self.assertEqual(actual_account["date_joined"], str(expected_account.date_joined))    
