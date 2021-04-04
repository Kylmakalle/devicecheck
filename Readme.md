# Apple DeviceCheck <!-- omit in toc -->

[Accessing and Modifying Per-Device Data](https://developer.apple.com/documentation/devicecheck/accessing_and_modifying_per-device_data)

Use a token from your app to validate requests, query and modify two per-device binary digits stored on Apple servers.

- [Features](#features)
- [Prepare](#prepare)
- [Install](#install)
- [Usage (Python)](#usage-python)
    - [Setup](#setup)
    - [Validate device](#validate-device)
    - [Update bits data](#update-bits-data)
    - [Query bits data](#query-bits-data)
- [Web server decorators](#web-server-decorators)
    - [Flask](#flask)
    - [Sanic](#sanic)
    - [FastAPI](#fastapi)
    - [Django Rest Framework (DRF)](#django-rest-framework-drf)
- [Tests](#tests)
- [Exceptions](#exceptions)
- [Usage (Swift)](#usage-swift)
    - [Generate device token](#generate-device-token)
    - [Pass device token in HTTP request](#pass-device-token-in-http-request)
- [License](#license)


# Features
- Prevent API & Content abuse with validating requests via Apple device token
- Query and modify two bits of data to achieve up to **four remote states** saved on Apple servers
- Easy to use configuration
- Examples
- Integrations with modern web frameworks


# Prepare
Visit https://developer.apple.com/account/resources/authkeys/list and create new **Key** with **DeviceCheck** permission

# Install

```
pip install devicecheck
```

# Usage (Python)

### Setup

```python
from devicecheck import DeviceCheck

device_check = DeviceCheck(
    team_id="XX7AN23E0Z",  # https://developer.apple.com/account/#/membership/
    bundle_id="com.akentev.app",
    key_id="JSAD983ENA",  # Generated at https://developer.apple.com/account/resources/authkeys/list
    private_key="/path/to/AuthKey_JSAD983ENA.p8",
    # Generated file at https://developer.apple.com/account/resources/authkeys/list
    dev_environment=True,  # True if using development Apple environment, False if using in production.
    # Remember to set dev_environment=False in production!
)
```

### Validate device

```python
result = device_check.validate_device_token(device_token)

if result.is_ok:
    print('OK! Device is valid')
else:
    print('Bad news. Unable to validate device')
```

### Update bits data

```python
# Can use both integers, strings and booleans. Will be converted with bool(value)
result = device_check.update_two_bits(device_token, bit_0=1, bit_1=False)

# Can update bits separately
result = device_check.update_two_bits(device_token, bit_0=True)

if result.is_ok:
    print('Bits updated')
else:
    print(f'Something went wrong. {result}')
```

### Query bits data

```python
# Can use both integers, strings and booleans
result = device_check.query_two_bits(device_token)

if result.is_ok:
    print(f'First bit {result.bit_0}')  # True
    print(f'Second bit {result.bit_1}')  # False
    print(f'Last update time {result.bits_last_update_time}')  # 2020-04
else:
    print(f'Something went wrong. {result}')
```

# Web server decorators

You can easily integrate devicecheck to your webserver using a decorator. The only thing there depends on a framework is a response that will be preventivelly returned if device check failed.

```python
from devicecheck.decorators import validate_device
from devicecheck import DeviceCheck

device_check = DeviceCheck(...)

# Set response that will be returned on invalid token
INVALID_TOKEN_RESPONSE = ('Invalid device_token', 403)

@app.route('/validate')
@validate_device(device_check, on_invalid_token=INVALID_TOKEN_RESPONSE)
def endpoint():
    return 'Content'
```

### Flask
```python
INVALID_TOKEN_RESPONSE = ('Invalid device_token', 403)
```
### Sanic
```python
from sanic.response import text

INVALID_TOKEN_RESPONSE = text('Invalid device_token', status=403)
```

### FastAPI
```python
INVALID_TOKEN_RESPONSE = ('Invalid device_token', 403)
```

### Django Rest Framework (DRF)
```python
from rest_framework.response import Response
from rest_framework import status

INVALID_TOKEN_RESPONSE = Response(serializer.errors, status=status.HTTP_403_FORBIDDEN)
```

# Tests
Well, it's kinda hard to automate testing, because Devicecheck requires real device (Simulators won't work).
In case you need to mock/disable decorators, pass `SKIP_DEVICE_CHECK_DECORATOR=True` environment variable.

For Debug logs, including requests body, pass a `DEBUG` environment variable.

# Exceptions

Library represents an `AppleException` class with attributes `status_code` and `description`
Requires `raise_on_error=True` parameter for `DeviceCheck` instance.

# Usage (Swift)

### Generate device token

```swift
import DeviceCheck

public func getDeviceToken(completion: @escaping (String?) -> ()) {
    if #available(iOS 11.0, *) {
        let currentDevice = DCDevice.current
        if currentDevice.isSupported
        {
            currentDevice.generateToken(completionHandler: { (data, error) in
                if let tokenData = data {
                    let tokenString = tokenData.base64EncodedString()
                    print("Received device token")
                    completion(tokenString)
                } else{
                    print("Error generating token: \(error!.localizedDescription)")
                }
            })
        } else {
            print("Device is not supported") // Simulators or etc.
        }
    } else {
        print("Device OS is lower than iOS 11")
    }
}

```

### Pass device token in HTTP request

Header or Body

```swift
getDeviceToken { deviceToken in
    var request = URLRequest(url: "...")
    request.httpMethod = "POST"
    
    // Header
    request.setValue(deviceToken, forHTTPHeaderField: "Device-Token")
    
    // Body
    request.setValue("application/json; charset=utf-8", forHTTPHeaderField: "Content-Type")
    let json = ["device_token": deviceToken] as [String : Any]
    let jsonData = try! JSONSerialization.data(withJSONObject: json)
    request.httpBody = jsonData as Data
    
    // Send it to server
    let downloadTask = URLSession.shared.dataTask(with: request, completionHandler: { data, response, error in
        ...
    })
}
```


# License
MIT

