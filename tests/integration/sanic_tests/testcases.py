import os
import unittest

from sanic_testing.testing import SanicTestClient

from tests.integration.sanic_tests.server import app, INVALID_TOKEN_RESPONSE

MOCK_DEVICE_CHECK_DECORATOR_TOKEN = os.environ['MOCK_DEVICE_CHECK_DECORATOR_TOKEN']


class TestSanicApi(unittest.TestCase):
    def setUp(self):
        self.app = SanicTestClient(app, port=None)
        self.route = '/validate'

    def test_invalid_token(self):
        request, response = self.app.post(self.route)
        self.assertEqual(INVALID_TOKEN_RESPONSE.status, response.status_code)
        self.assertEqual(INVALID_TOKEN_RESPONSE.body, response.body)

    def test_valid_token_header(self):
        request, response = self.app.post(self.route, headers={'Device-Token': MOCK_DEVICE_CHECK_DECORATOR_TOKEN})
        self.assertEqual(200, response.status_code)

    def test_valid_token_body(self):
        request, response = self.app.post(self.route, json={'device_token': MOCK_DEVICE_CHECK_DECORATOR_TOKEN})
        self.assertEqual(200, response.status_code)
