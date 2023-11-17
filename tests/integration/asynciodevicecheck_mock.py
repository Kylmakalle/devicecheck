from devicecheck.asyncio import AsyncioDeviceCheck

PRIVATE_KEY = """
-----BEGIN PRIVATE KEY-----
TEST
-----END PRIVATE KEY-----
"""

device_check = AsyncioDeviceCheck(
    team_id="XX7AN23E0Z",
    bundle_id="com.akentev.app",
    key_id="JSAD983ENA",
    private_key=PRIVATE_KEY,
    dev_environment=True
)
