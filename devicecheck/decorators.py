import inspect
import json
import logging
import os
from functools import wraps

from . import DeviceCheck, AppleException
from .asyncio import AsyncioDeviceCheck

log = logging.getLogger('devicecheck:decorator')
logging.basicConfig()

if os.environ.get('DEBUG') == 'True':
    log.setLevel(logging.DEBUG)  # pragma: no cover


class DCSupportedFrameworks:
    flask = 'flask'
    drf = 'rest_framework'
    django = 'django'


SUPPORTED_FRAMEWORKS_LIST = list(
    filter(lambda a: not (a.startswith('__') and a.endswith('__')), dir(DCSupportedFrameworks)))


class DCSupportedAsyncFrameworks:
    sanic = 'sanic'
    fastapi = 'fastapi'


SUPPORTED_ASYNC_FRAMEWORKS_LIST = list(
    filter(lambda a: not (a.startswith('__') and a.endswith('__')), dir(DCSupportedAsyncFrameworks)))

DEVICE_TOKEN_HEADER_KEYS = (
    'Device-Token',
    'Device-token',
    'DEVICE_TOKEN',
    'HTTP_DEVICE_TOKEN'
    'DEVICETOKEN',
    'HTTP_DEVICETOKEN',
    'device-token',
    'devicetoken'
)
DEVICE_TOKEN_BODY_KEYS = ('device_token', 'deviceToken', 'devicetoken', 'device-token')

if os.environ.get('SKIP_DEVICE_CHECK_DECORATOR') == 'True':
    SKIP_DEVICE_CHECK_DECORATOR = True  # pragma: no cover
else:
    SKIP_DEVICE_CHECK_DECORATOR = False

if os.environ.get('MOCK_DEVICE_CHECK_DECORATOR_TOKEN'):
    MOCK_DEVICE_CHECK_DECORATOR_TOKEN = os.environ.get('MOCK_DEVICE_CHECK_DECORATOR_TOKEN')
else:
    MOCK_DEVICE_CHECK_DECORATOR_TOKEN = None  # pragma: no cover


def _is_valid_device(device_check_instance: DeviceCheck, token: str):
    if MOCK_DEVICE_CHECK_DECORATOR_TOKEN:
        return token == MOCK_DEVICE_CHECK_DECORATOR_TOKEN
    try:  # pragma: no cover
        return device_check_instance.validate_device_token(token).is_ok  # pragma: no cover
    except AppleException:  # pragma: no cover
        return False  # pragma: no cover


async def _is_valid_device_async(device_check_instance: AsyncioDeviceCheck, token: str):
    if MOCK_DEVICE_CHECK_DECORATOR_TOKEN:
        return token == MOCK_DEVICE_CHECK_DECORATOR_TOKEN
    try:  # pragma: no cover
        return await device_check_instance.validate_device_token(token).is_ok  # pragma: no cover
    except AppleException:  # pragma: no cover
        return False  # pragma: no cover


def async_validate_device(device_check_instance: AsyncioDeviceCheck,
                          framework: [DCSupportedAsyncFrameworks, str] = None,
                          on_invalid_token=('Invalid device token', 403)):
    """
    Async Decorator that validates device token provided in `Device-Token` header
                            or `device_token`/`deviceToken` key in json body.
    :param device_check_instance: Instance of AsyncioDeviceCheck module for validating
    :param framework: Name of used async framework for automated data extraction. Leave `None` to rely on a universal parser.
    :param on_invalid_token: Object that will be returned if validation was unsuccessful
    :return: on_invalid_token variable
    """

    def decorator(f):
        @wraps(f)
        async def decorated_function(*args, **kwargs):
            if SKIP_DEVICE_CHECK_DECORATOR:
                log.debug('Skipping device check decorator')  # pragma: no cover
                response = await f(*args, **kwargs)  # pragma: no cover
                return response  # pragma: no cover

            if framework == DCSupportedAsyncFrameworks.sanic:
                from sanic.request import Request as Sanic_request
                for argument in list(args) + list(kwargs.values()):
                    if isinstance(argument, Sanic_request):
                        request = argument
                        break
            elif framework == DCSupportedAsyncFrameworks.fastapi:
                from fastapi.requests import Request as Fastapi_request
                for argument in list(args) + list(kwargs.values()):
                    if isinstance(argument, Fastapi_request):
                        request = argument
                        break
            else:  # universal
                for argument in list(args) + list(kwargs.values()):
                    if hasattr(argument, 'body') or hasattr(argument, 'headers'):
                        request = argument

            is_valid = False
            device_token = await async_extract_device_token(request, framework)
            if device_token:
                try:
                    is_valid = await _is_valid_device_async(device_check_instance, device_token)
                except Exception as e:  # pragma: no cover
                    log.error(f'DeviceCheck request failed. {e}')  # pragma: no cover
            if is_valid:
                # request has valid device token
                response = await f(*args, **kwargs)
                return response
            else:
                # request is not legit
                log.info(f'Caught invalid device token: "{device_token}"')
                return on_invalid_token

        return decorated_function

    return decorator


def validate_device(device_check_instance: DeviceCheck,
                    framework: [DCSupportedAsyncFrameworks, str] = None,
                    on_invalid_token=('Invalid device token', 403)):
    """
    Decorator that validates device token provided in `Device-Token` header
                            or `device_token`/`deviceToken` key in json body.
    :param device_check_instance: Instance of DeviceCheck module for validating
    :param framework: Name of used framework for automated data extraction. Leave `None` to rely on a universal parser.
    :param on_invalid_token: Object that will be returned if validation was unsuccessful
    :return: on_invalid_token variable
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if SKIP_DEVICE_CHECK_DECORATOR:
                log.debug('Skipping device check decorator')  # pragma: no cover
                response = f(*args, **kwargs)  # pragma: no cover
                return response  # pragma: no cover

            request = None

            if framework == DCSupportedFrameworks.flask:
                from flask import request as Flask_request
                request = Flask_request
            elif framework == DCSupportedFrameworks.drf:
                from rest_framework.request import Request as DRF_request
                for argument in list(args) + list(kwargs.values()):
                    if isinstance(argument, DRF_request):
                        request = argument
                        break
            elif framework == DCSupportedFrameworks.django:
                from django.http.request import HttpRequest as Django_request
                for argument in list(args) + list(kwargs.values()):
                    if isinstance(argument, Django_request):
                        request = argument
                        break
            else:  # universal
                for argument in list(args) + list(kwargs.values()):
                    if hasattr(argument, 'body') or hasattr(argument, 'headers'):
                        request = argument

            if not request:  # pragma: no cover
                raise ValueError('Unable to extract request object. Try to specify "framework" option')

            is_valid = False
            device_token = extract_device_token(request, framework)
            if device_token:
                try:
                    is_valid = _is_valid_device(device_check_instance, device_token)
                except Exception as e:  # pragma: no cover
                    log.error(f'DeviceCheck request failed. {e}')  # pragma: no cover
            if is_valid:
                # request has valid device token
                response = f(*args, **kwargs)
                return response
            else:
                # request is not legit
                log.info(f'Caught invalid device token: "{device_token}"')
                return on_invalid_token

        return decorated_function

    return decorator


def extract_device_token(request, framework: [DCSupportedFrameworks, str]):
    headers_dict = {}
    json_body_dict = {}
    try:
        if framework == DCSupportedFrameworks.flask:
            headers_dict = request.headers
            json_body_dict = request.get_json()
        elif framework == DCSupportedFrameworks.drf:
            headers_dict = request.META
            json_body_dict = json.loads(request.data)
        elif framework == DCSupportedFrameworks.django:
            headers_dict = request.META
            body = request.body
            if isinstance(body, bytes):
                body = body.decode('utf-8', 'replace')
            json_body_dict = json.loads(body)
        else:
            headers_dict = dict(request.headers)
            if hasattr(request, 'json'):
                maybe_callable_json = getattr(request, 'json')

                if hasattr(maybe_callable_json, '__call__'):
                    json_body_dict = maybe_callable_json()
                else:
                    json_body_dict = maybe_callable_json

            elif hasattr(request, 'data'):
                bytes_or_string_data = getattr(request, 'data')
                if bytes_or_string_data:
                    json_body_dict = json.loads(bytes_or_string_data)

            elif hasattr(request, 'body'):
                bytes_or_string_body = getattr(request, 'body')
                if bytes_or_string_body:
                    json_body_dict = json.loads(bytes_or_string_body)
    except Exception as e:
        log.debug(f"Error extracting device token from {framework} request of type {type(request)}. {e}")

    device_token = find_token_in_headers_dict(headers_dict or {}, framework)
    if device_token:
        return device_token

    device_token = find_token_in_json_body_dict(json_body_dict or {}, framework)
    if device_token:
        return device_token

    log.debug(f'No device tokens found in parsed {framework} request of type {type(request)}')
    log.info('No device token found in request')


async def async_extract_device_token(request, framework: [DCSupportedFrameworks, str]):
    headers_dict = {}
    json_body_dict = {}
    try:
        if framework == DCSupportedAsyncFrameworks.sanic:
            headers_dict = request.headers
            json_body_dict = request.json
        elif framework == DCSupportedAsyncFrameworks.fastapi:
            headers_dict = request.headers
            if await request.body():
                json_body_dict = await request.json()
        else:
            headers_dict = dict(request.headers)
            if hasattr(request, 'json'):
                maybe_callable_json = getattr(request, 'json')

                if hasattr(maybe_callable_json, '__call__'):
                    maybe_awaitable_json = maybe_callable_json()

                    if inspect.isawaitable(maybe_awaitable_json):
                        json_body_dict = await maybe_awaitable_json
                    else:
                        json_body_dict = maybe_awaitable_json
                else:
                    json_body_dict = maybe_callable_json

            elif hasattr(request, 'data'):
                bytes_or_string_data = getattr(request, 'data')
                if bytes_or_string_data:
                    json_body_dict = json.loads(bytes_or_string_data)

            elif hasattr(request, 'body'):
                weak_body = getattr(request, 'body')
                json_body_dict = json.loads(weak_body)
    except Exception as e:
        log.debug(f"Error extracting device token from {framework} request of type {type(request)}. {e}")

    device_token = find_token_in_headers_dict(headers_dict or {}, framework)
    if device_token:
        return device_token

    device_token = find_token_in_json_body_dict(json_body_dict or {}, framework)
    if device_token:
        return device_token
    log.debug(f'No device tokens found in parsed {framework} request of type {type(request)}')

    log.info('No device token found in request')


def find_token_in_headers_dict(headers_dict: dict, framework: str) -> [str, None]:
    for device_token_header_key in DEVICE_TOKEN_HEADER_KEYS:
        if headers_dict.get(device_token_header_key):
            log.debug(f'Found device token in header {device_token_header_key} for {framework} request')
            return headers_dict[device_token_header_key]


def find_token_in_json_body_dict(json_body_dict: dict, framework: str) -> [str, None]:
    for device_token_key in DEVICE_TOKEN_BODY_KEYS:
        if json_body_dict.get(device_token_key):
            log.debug(f'Found device token in json body key {device_token_key} for {framework} request')
            return json_body_dict[device_token_key]
