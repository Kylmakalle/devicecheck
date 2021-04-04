import logging
import os
from functools import wraps

from . import DeviceCheck, AppleException

log = logging.getLogger('devicecheck:decorator')
logging.basicConfig()

if os.environ.get('SKIP_DEVICE_CHECK_DECORATOR') == 'True':
    SKIP_DEVICE_CHECK_DECORATOR = True
else:
    SKIP_DEVICE_CHECK_DECORATOR = False


def _is_valid_device(device_check_instance: DeviceCheck, token: str):
    try:
        return device_check_instance.validate_device_token(token).is_ok
    except AppleException:
        return False


def validate_device(device_check_instance: DeviceCheck, on_invalid_token=('Invalid device token', 403)):
    """
    Decorator that validates device token provided in `Device-Token` header
                            or `device_token`/`deviceToken` key in json body.
    :param device_check_instance: Instance of DeviceCheck module for validating
    :param on_invalid_token: Object that will be returned if validation was unsuccessful
    :return: on_invalid_token variable
    """

    def decorator(f):
        @wraps(f)
        async def decorated_function(request, *args, **kwargs):

            while True:
                if SKIP_DEVICE_CHECK_DECORATOR:
                    device_token = None
                    break

                device_token = request.headers.get('Device-Token')
                if device_token:
                    log.debug('Validating token from header')
                    break
                try:
                    json_body = request.json
                except Exception as e:
                    log.debug(f'Validation failed. Cant parse json body: {e}')
                    break

                device_token = json_body.get('device_token') or json_body.get('deviceToken') \
                               or json_body.get('devicetoken') or json_body.get('device-token')
                if device_token:
                    log.debug('Validating token from body')
                    break

                log.info('No device token found in request')
                break

            if device_token:
                try:
                    is_valid = _is_valid_device(device_check_instance, device_token)
                except Exception as e:
                    log.error(f'DeviceCheck request failed. {e}')
                    is_valid = False
            else:
                if SKIP_DEVICE_CHECK_DECORATOR:
                    is_valid = True
                else:
                    is_valid = False

            if is_valid:
                # request has valid device token
                response = await f(request, *args, **kwargs)
                return response
            else:
                # request is not legit
                log.info(f'Caught invalid device token: "{device_token}"')
                return on_invalid_token

        return decorated_function

    return decorator
