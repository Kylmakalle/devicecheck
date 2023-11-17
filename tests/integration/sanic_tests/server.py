from sanic import Sanic
from sanic.response import text

from devicecheck.decorators import async_validate_device, DCSupportedAsyncFrameworks
from tests.integration.asynciodevicecheck_mock import device_check

app = Sanic(__name__)
INVALID_TOKEN_RESPONSE = text('Invalid device_token', 403)


@app.route('/validate', methods=['POST'])
@async_validate_device(device_check, framework=DCSupportedAsyncFrameworks.sanic,
                       on_invalid_token=INVALID_TOKEN_RESPONSE)
async def validate(request):
    return text("device token valid", 200)


if __name__ == '__main__':
    app.run(debug=True)
