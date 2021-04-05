import flask

from devicecheck.decorators import validate_device, DCSupportedFrameworks
from tests.integration.devicecheck_mock import device_check

app = flask.Flask(__name__)
INVALID_TOKEN_RESPONSE = ('Invalid device_token', 403)


@app.route('/validate', methods=['POST'])
@validate_device(device_check, framework=DCSupportedFrameworks.flask, on_invalid_token=INVALID_TOKEN_RESPONSE)
def validate():
    return "device token valid"


if __name__ == "__main__":
    app.run(debug=True)
