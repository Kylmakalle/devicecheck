import aiohttp
import certifi
import ssl
from . import DeviceCheck, get_timestamp_milliseconds, get_transaction_id, parse_apple_response, HttpAppleResponse, log, DataAppleResponse


class AsyncioDeviceCheck(DeviceCheck):

    @staticmethod
    def _make_session() -> aiohttp.ClientSession:
        return aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(
                ssl=ssl.create_default_context(cafile=certifi.where())
            ),
        )
  
    async def validate_device_token(self, token: str, *args, **kwargs) -> HttpAppleResponse:
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

        result = await self._request(self.get_request_url(), endpoint, payload, *args, **kwargs)
        return parse_apple_response(result, self.raise_on_error)

    async def query_two_bits(self, token: str, *args, **kwargs) -> DataAppleResponse:
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
        result = await self._request(self.get_request_url(), endpoint, payload, *args, **kwargs)
        return parse_apple_response(result, self.raise_on_error)

    async def update_two_bits(self, token: str, bit_0: [bool, int] = None, bit_1: [bool, int] = None, *args,
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

        result = await self._request(self.get_request_url(), endpoint, payload, *args, **kwargs)
        return parse_apple_response(result, self.raise_on_error)

    async def _request(self, url, endpoint, payload, retrying_env=False, *args, **kwargs):
        log.debug(f'Sending request to {url}/{endpoint} with data {payload}')

        async with self._session.post(f"{url}/{endpoint}", json=payload, headers={"authorization": f"Bearer {self.generate_token()}"}) as response:
            result_text = await response.text()
            log.debug(f"Response: {response.status} {result_text}")

            if not retrying_env and self.retry_wrong_env_request and response.status != 200:
                log.info(f"Retrying request on {'production' if not self.dev_environment else 'development'} server")
                return await self._request(self.get_request_url(not self.dev_environment), endpoint, payload, retrying_env=True, *args, **kwargs)

            return response.status, result_text
