import uvicorn
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import PlainTextResponse

from devicecheck.decorators import async_validate_device, DCSupportedAsyncFrameworks
from tests.integration.devicecheck_mock import device_check

app = FastAPI()
INVALID_TOKEN_RESPONSE = PlainTextResponse('Invalid device_token', status_code=403)


@app.post('/validate')
@async_validate_device(device_check, framework=DCSupportedAsyncFrameworks.fastapi,
                       on_invalid_token=INVALID_TOKEN_RESPONSE)
async def validate(request: Request):  # requires request object to be specified
    return "device token valid", 200


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
