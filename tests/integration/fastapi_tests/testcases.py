import os
import unittest

from fastapi.testclient import TestClient

from tests.integration.fastapi_tests.server import app, INVALID_TOKEN_RESPONSE

MOCK_DEVICE_CHECK_DECORATOR_TOKEN = os.environ['MOCK_DEVICE_CHECK_DECORATOR_TOKEN']


class TestFastApi(unittest.TestCase):
    def setUp(self):
        self.app = TestClient(app)
        self.route = '/validate'

    def test_invalid_token(self):
        response = self.app.post(self.route)
        self.assertEqual(INVALID_TOKEN_RESPONSE.status_code, response.status_code)
        self.assertEqual(INVALID_TOKEN_RESPONSE.body.decode('utf-8'), response.text)

    def test_valid_token_header(self):
        response = self.app.post(self.route, headers={'Device-Token': MOCK_DEVICE_CHECK_DECORATOR_TOKEN})
        self.assertEqual(200, response.status_code)

    def test_valid_token_body(self):
        response = self.app.post(self.route, json={'device_token': MOCK_DEVICE_CHECK_DECORATOR_TOKEN})
        self.assertEqual(200, response.status_code)
