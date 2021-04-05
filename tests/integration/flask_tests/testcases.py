import os
import unittest

from tests.integration.flask_tests.server import app, INVALID_TOKEN_RESPONSE

MOCK_DEVICE_CHECK_DECORATOR_TOKEN = os.environ['MOCK_DEVICE_CHECK_DECORATOR_TOKEN']


class TestFlaskApi(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.route = '/validate'

    def test_invalid_token(self):
        response = self.app.post(self.route)
        self.assertEqual(INVALID_TOKEN_RESPONSE[1], response.status_code)
        self.assertEqual(INVALID_TOKEN_RESPONSE[0], response.data.decode('utf-8'))

    def test_valid_token_header(self):
        response = self.app.post(self.route, headers={'Device-Token': MOCK_DEVICE_CHECK_DECORATOR_TOKEN})
        self.assertEqual(200, response.status_code)

    def test_valid_token_body(self):
        response = self.app.post(self.route, json={'device_token': MOCK_DEVICE_CHECK_DECORATOR_TOKEN})
        self.assertEqual(200, response.status_code)
