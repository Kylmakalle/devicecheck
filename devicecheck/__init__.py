"""
Python Implementation of Apple DeviceCheck API
https://developer.apple.com/documentation/devicecheck/accessing_and_modifying_per-device_data

https://github.com/Kylmakalle/devicecheck
"""
__version__ = "1.3.3"
__author__ = 'Sergey Akentev (@Kylmakalle)'
__license__ = 'MIT'
__copyright__ = 'Copyright 2024 Sergey Akentev'

import logging
import os
import sys
import typing
import uuid
import json
from time import time

import jwt
import requests

log = logging.getLogger('devicecheck')
logging.basicConfig()

if os.environ.get('DEBUG'):
    log.setLevel(logging.DEBUG)  # pragma: no cover


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers["authorization"] = f"Bearer {self.token}"
        return r


class AppleException(Exception):
    def __init__(self, status_code, description):
        super().__init__(description)
        self.status_code = status_code
        self.description = description

    def __str__(self) -> str:
        """
        String representation of an error
        :return: str
        """
        return f"{self.status_code}" + f" {self.description}" if self.description else ""


class HttpAppleResponse:
    """
    Simple class for Apple server responses
    https://developer.apple.com/documentation/devicecheck/accessing_and_modifying_per-device_data#2910408
    """

    def __init__(self, status_code: int, description: str, raise_on_error: bool):
        """
        :param status_code (int): HTTP Status code
        :param description (str): Response description
        :param raise_on_error (bool): Raise AppleException on errors
        """
        self.status_code = status_code
        self.description = description
        self.is_ok = self._is_ok()

        if raise_on_error:
            if not self.is_ok:
                raise AppleException(self.status_code, self.description)

    def _is_ok(self) -> bool:
        """
        Returns True if response has code 200 and there're no errors.
        :return: bool
        """
        if self.description not in ("Bit State Not Found", "Failed to find bit state"):
            return self.status_code == 200
        else:
            return False

    def __str__(self) -> str:
        """
        String representation of a response
        :return: str
        """
        return f"{self.status_code}" + f" {self.description}" if self.description else ""

    def __dict__(self) -> dict:
        """
        Dict representation of a response
        :return: dict
        """
        return {
            "status_code": self.status_code,
            "description": self.description
        }


class DataAppleResponse:
    """
    Representation of Apple response with data
    https://developer.apple.com/documentation/devicecheck/accessing_and_modifying_per-device_data
    """

    def __init__(self, status_code: int, json_response: dict, raise_on_error: bool):
        """
        :param status_code (int): HTTP Status code
        :param json_response (dict): Response body
        :param is_ok (bool): Was the request successful
        :param bit_0 (bool): The value of the first bit
        :param bit_1 (bool): The value of the second bit
        :param bits_last_update_time (str): The date of the last modification, in YYYY-MM format
        :param raise_on_error (bool): Raise AppleException on errors
        """
        self.status_code = status_code
        self.json_response = json_response
        self.is_ok = self._is_ok()
        self.bit_0 = json_response.get('bit0', None)
        self.bit_1 = json_response.get('bit1', None)
        self.bits_last_update_time = json_response.get('last_update_time', None)

        if raise_on_error:
            if not self.is_ok:
                raise AppleException(self.status_code, self.json_response)

    def _is_ok(self) -> bool:
        """
        Returns True if response has code 200 and there're no errors.
        :return: bool
        """
        if "Bit State Not Found" not in str(self.json_response):
            return self.status_code == 200
        else:
            return False

    def __str__(self) -> str:
        """
        String representation of a response
        :return: str
        """
        result_str = f"{self.status_code}"
        if self.json_response:
            result_str += f" {self.json_response}"
        if self.bit_0 is not None or self.bit_1 is not None:
            result_str += f"Bits: {self.bit_0} {self.bit_1}."
        if self.bits_last_update_time:
            result_str += f" Last update time: {self.bits_last_update_time}"
        return result_str

    def __dict__(self) -> dict:
        """
        Dict representation of a response
        :return: dict
        """
        return {
            "status_code": self.status_code,
            "json_response": self.json_response,
            "bit_0": self.bit_0,
            "bit_1": self.bit_1,
            "bits_last_update_time": self.bits_last_update_time
        }


def parse_apple_response(response_text: str, response_status_code: int, raise_on_error: bool):
    if response_text:
        try:
            response_json = json.loads(response_text)
            return DataAppleResponse(response_status_code, response_json, raise_on_error)
        except:
            pass
    return HttpAppleResponse(response_status_code, response_text, raise_on_error)


class DeviceCheck:
    PRODUCTION_URL = "https://api.devicecheck.apple.com"
    DEVELOPMENT_URL = "https://api.development.devicecheck.apple.com"

    def __init__(self, team_id: str, bundle_id: str, key_id: str, private_key: [str, typing.IO],
                 dev_environment: bool = False, retry_wrong_env_request: bool = False, raise_on_error: bool = False):
        """
        Accessing and Modifying Per-Device Data
        Use a token from your app to query and modify two per-device binary digits stored on an Apple server.
        https://developer.apple.com/documentation/devicecheck/accessing_and_modifying_per-device_data

        :param team_id: (str) Alpha-numeric string. Get it via url https://developer.apple.com/account/#/membership/
        :param bundle_id: (str) Bundle ID of your application. Example: `com.akentev.app`
        :param key_id: (str) Alpha-numeric string.
                       Key ID generated at https://developer.apple.com/account/resources/authkeys/list
        :param private_key: (str, IO) Contents or Path of `AuthKey_XXXXXXXX.p8` Private Key file generated at
                            https://developer.apple.com/account/resources/authkeys/list
        :param dev_environment: (bool) `True` if using development Apple environment (for testing and simulators).
                                       `False` if using production. Defaults to `False` (using production)
        :param retry_wrong_env_request: (bool) Retry request on another environment
                                        if Apple returns error for current environment
        :param raise_on_error: (bool) Raise `AppleException` on error from Apple services
        """
        self.team_id = team_id
        self.bundle_id = bundle_id
        self.key_id = key_id
        self.private_key = get_private_key_string(private_key)
        self.token_valid_till = None
        self.jwt_token = None
        self.dev_environment = dev_environment
        if dev_environment:
            log.warning("Using Development environment. Remember to set dev_environment=False in production!")
        self.retry_wrong_env_request = retry_wrong_env_request
        self.raise_on_error = raise_on_error
        self._session = self._make_session()

    @staticmethod
    def _make_session() -> requests.Session:
        return requests.Session()

    def generate_token(self, valid_time: int = 500, force_refresh=False):
        """
        Generate JWT token to communicate with Apple
        https://help.apple.com/developer-account/#/deva05921840
        :param valid_time: Set a time window in seconds for token to be valid. MAX 1200 seconds (20 minutes).
                                                                                            Defaults to 500.
        :param force_refresh: `True` to refresh token on every request. `False` to use cached token. Defaults to `False`
        :return:
        """
        now = int(time())
        if not force_refresh and self.token_valid_till and self.token_valid_till > now:
            log.debug(f'Token still valid for {self.token_valid_till - now} seconds')
            return self.jwt_token

        if valid_time > 20 * 60:
            raise ValueError('Token valid time is limited to 20 minutes (1200 seconds)')

        timestamp_now = int(time())
        timestamp_expires = timestamp_now + valid_time
        self.token_valid_till = timestamp_expires

        data = {
            "iss": self.team_id,
            "iat": timestamp_now,
            "exp": timestamp_expires,
            "sub": self.bundle_id
        }

        headers = {
            "kid": self.key_id
        }

        self.jwt_token = jwt.encode(
            payload=data,
            key=self.private_key,
            algorithm="ES256",
            headers=headers
        )
        log.debug(f'Generated JWT: {self.jwt_token}')
        return self.jwt_token

    def validate_device_token(self, token: str, *args, **kwargs) -> HttpAppleResponse:
        """
        Validate a device with it's token
        https://developer.apple.com/documentation/devicecheck/accessing_and_modifying_per-device_data#2929855
        :param token: Base 64–encoded representation of encrypted device information
        :param args: Additional args for requests module
        :param kwargs: Additional kwargs for requests module
        :return:
        """
        endpoint = 'v1/validate_device_token'
        payload = {
            'timestamp': get_timestamp_milliseconds(),
            'transaction_id': get_transaction_id(),
            'device_token': token
        }

        result = self._request(self.get_request_url(), endpoint, payload, *args, **kwargs)
        return parse_apple_response(result.text, result.status_code, self.raise_on_error)

    def query_two_bits(self, token: str, *args, **kwargs) -> DataAppleResponse:
        """
        Query two bits of device data
        https://developer.apple.com/documentation/devicecheck/accessing_and_modifying_per-device_data#2910405
        :param token: Base 64–encoded representation of encrypted device information
        :param args: Additional args for requests module
        :param kwargs: Additional kwargs for requests module
        :return:
        """
        endpoint = 'v1/query_two_bits'
        payload = {
            'timestamp': get_timestamp_milliseconds(),
            'transaction_id': get_transaction_id(),
            'device_token': token
        }
        result = self._request(self.get_request_url(), endpoint, payload, *args, **kwargs)
        return parse_apple_response(result.text, result.status_code, self.raise_on_error)

    def update_two_bits(self, token: str, bit_0: [bool, int] = None, bit_1: [bool, int] = None, *args,
                        **kwargs) -> HttpAppleResponse:
        """
        Update bit(s) of a device data
        https://developer.apple.com/documentation/devicecheck/accessing_and_modifying_per-device_data#2910405
        :param token: Base 64–encoded representation of encrypted device information
        :param bit_0: (Optional) First bit of data `bool`
        :param bit_1: (Optional) Second bit of data `bool`
        :param args: Additional args for requests module
        :param kwargs: Additional kwargs for requests module
        :return:
        """
        endpoint = 'v1/update_two_bits'
        payload = {
            'timestamp': get_timestamp_milliseconds(),
            'transaction_id': get_transaction_id(),
            'device_token': token,
        }

        if bit_0 is not None:
            payload['bit0'] = bool(bit_0)

        if bit_1 is not None:
            payload['bit1'] = bool(bit_1)

        result = self._request(self.get_request_url(), endpoint, payload, *args, **kwargs)
        return parse_apple_response(result.text, result.status_code, self.raise_on_error)

    def get_request_url(self, is_dev_env: bool = None):
        """
        Set proper url for development or production.
        :param is_dev_env: Development environment flag
        :return:
        """
        if is_dev_env is None:
            is_dev_env = self.dev_environment
        return self.DEVELOPMENT_URL if is_dev_env else self.PRODUCTION_URL

    def _request(self, url, endpoint, payload, retrying_env=False, *args, **kwargs):
        log.debug(f'Sending request to {url}/{endpoint} with data {payload}')

        result = self._session.post(f"{url}/{endpoint}", json=payload, auth=BearerAuth(self.generate_token()))
        log.debug(f"Response: {result.status_code} {result.text}")
        if not retrying_env and self.retry_wrong_env_request and result.status_code != 200:
            log.info(f"Retrying request on {'production' if not self.dev_environment else 'development'} server")
            return self._request(self.get_request_url(not self.dev_environment), endpoint, payload, retrying_env=True,
                                 *args, **kwargs)

        return result


def get_timestamp_milliseconds() -> int:
    return int(time() * 1000)


def get_transaction_id() -> str:
    return str(uuid.uuid4())


def get_script_directory() -> str:
    """
    Search for the original invoke script directory
    :return:
    """
    path = os.path.realpath(sys.argv[0])
    if os.path.isdir(path):
        return path
    else:
        return os.path.dirname(path)


def get_private_key_string(private_key_or_path: [str, typing.IO]) -> str:
    """
    Try to fetch private key string file.
    Supports:
      - Local path `AuthKey.p8`
      - Full path `/path/to/AuthKey.p8`
      - Private Key string `-----BEGIN PRIVATE KEY----- ...`
      - Privat Key file object `open('AuthKey.p8)`
    :param private_key_or_path: Path to private key or File object
    :return: private key contents (str)
    """
    if isinstance(private_key_or_path, str):
        if private_key_or_path.endswith('.p8'):
            if os.path.isfile(private_key_or_path):
                pk_fullpath = private_key_or_path
                log.debug('Provided full path to .p8 key')
            else:
                pk_fullpath = os.path.join(get_script_directory(), private_key_or_path)
                if not os.path.isfile(pk_fullpath):
                    pk_fullpath = os.path.join(os.getcwd(), private_key_or_path)
                    if not os.path.isfile(pk_fullpath):
                        print(pk_fullpath)
                        pk_fullpath = os.path.join(os.curdir, private_key_or_path)
                        if not os.path.isfile(pk_fullpath):
                            raise ValueError('Please specify full path to .p8 file')
                log.debug('Provided relative path to .p8 key')
            with open(pk_fullpath) as pk_file:
                private_key = pk_file.read()
            return private_key
        else:
            log.debug('Provided private key')
            return private_key_or_path
    elif isinstance(private_key_or_path, typing.IO):
        private_key = private_key_or_path.read()
        try:
            private_key_or_path.close()
        except IOError as e:
            log.warning(f'Unable to close the file stream {e}')
        log.debug('Provided filestream key')
        return private_key
    else:
        raise ValueError('Please provide a valid private key or path to .p8 file')
