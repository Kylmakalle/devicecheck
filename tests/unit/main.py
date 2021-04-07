import os
import unittest

import jwt
import requests_mock

from devicecheck import DeviceCheck, get_private_key_string, get_timestamp_milliseconds, AppleException

PRIVATE_KEY = """
-----BEGIN PRIVATE KEY-----
MIGTAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBHkwdwIBAQQgir767IOFOYHsYtNQ
wsvLeJVu3bxCLL/SURQvMZw6QumgCgYIKoZIzj0DAQehRANCAARuwGOLtHY99zLl
iyACJp6xmj6YfE8bOLxHTZGkoC/+yNgf/fBpwf5Nin2pzyM8FUOYXg1R1v2bQqJy
wHYtSkc1
-----END PRIVATE KEY-----
"""

MOCK_DEVICE_CHECK_DECORATOR_TOKEN = os.environ['MOCK_DEVICE_CHECK_DECORATOR_TOKEN']


class TestSigning(unittest.TestCase):
    def setUp(self) -> None:
        self.device_check = DeviceCheck(
            team_id="XX7AN23E0Z",
            bundle_id="com.akentev.app",
            key_id="JSAD983ENA",
            private_key=PRIVATE_KEY,
            dev_environment=True
        )

    def test_generate_token(self):
        token = self.device_check.generate_token()
        decoded_data = jwt.decode(token, get_private_key_string(PRIVATE_KEY), algorithms="ES256")
        headers = jwt.get_unverified_header(token)
        self.assertEqual(self.device_check.key_id, headers['kid'])
        self.assertEqual("ES256", headers['alg'])
        self.assertEqual("JWT", headers['typ'])
        self.assertEqual(self.device_check.team_id, decoded_data['iss'])
        self.assertEqual(self.device_check.token_valid_till, decoded_data['exp'])
        self.assertEqual(self.device_check.bundle_id, decoded_data['sub'])
        self.assertTrue(
            decoded_data['iat'] <= get_timestamp_milliseconds() <= self.device_check.token_valid_till * 1000
        )

    def test_force_generate_token(self):
        token_1 = self.device_check.generate_token()
        jwt.decode(token_1, get_private_key_string(PRIVATE_KEY), algorithms="ES256")

        token_2 = self.device_check.generate_token(force_refresh=True)
        jwt.decode(token_2, get_private_key_string(PRIVATE_KEY), algorithms="ES256")
        self.assertNotEqual(token_1, token_2)

    def test_fail_jwt_auth(self):
        result = self.device_check.validate_device_token(token="TEST")
        self.assertEqual(False, result.is_ok)
        self.assertEqual(401, result.status_code)


class TestSigningExceptions(unittest.TestCase):
    def setUp(self) -> None:
        self.device_check = DeviceCheck(
            team_id="XX7AN23E0Z",
            bundle_id="com.akentev.app",
            key_id="JSAD983ENA",
            private_key=PRIVATE_KEY,
            dev_environment=True,
            raise_on_error=True
        )

    def test_fail_jwt_auth(self):
        with self.assertRaises(AppleException) as context:
            self.device_check.validate_device_token(token="TEST")
        self.assertEqual(401, context.exception.status_code)


class TestMockedResponses(unittest.TestCase):
    def setUp(self) -> None:
        self.device_check = DeviceCheck(
            team_id="XX7AN23E0Z",
            bundle_id="com.akentev.app",
            key_id="JSAD983ENA",
            private_key=PRIVATE_KEY,
            dev_environment=True,
            retry_wrong_env_request=True
        )

    @requests_mock.Mocker()
    def test_validate_device_token(self, mock_server):
        pass
        # mock_server.register_uri(requests_mock.ANY, f'https://{DeviceCheck.DEVELOPMENT_URL}/v1/validate_device_token',
        #                          text='')
        #
        # self.device_check.validate_device_token(MOCK_DEVICE_CHECK_DECORATOR_TOKEN)


if __name__ == '__main__':
    unittest.main()
