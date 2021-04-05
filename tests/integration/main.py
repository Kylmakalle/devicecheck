import unittest

from tests.integration.fastapi_tests.testcases import TestFastApi
from tests.integration.flask_tests.testcases import TestFlaskApi
from tests.integration.sanic_tests.testcases import TestSanicApi

all_tests = unittest.TestSuite([
    unittest.TestLoader().loadTestsFromTestCase(TestFlaskApi),
    unittest.TestLoader().loadTestsFromTestCase(TestSanicApi),
    unittest.TestLoader().loadTestsFromTestCase(TestFastApi)
])
