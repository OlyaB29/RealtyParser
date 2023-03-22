import sentry_sdk
import logging
from sentry_sdk.integrations.logging import LoggingIntegration
# from sentry_sdk import set_level


sentry_logging = LoggingIntegration(
    level=logging.INFO,
    event_level=logging.INFO
)

# set_level("info")

sentry_sdk.init(
    dsn="https://6a78033cc3b14597974cb4c7949bb595@o4504847936192512.ingest.sentry.io/4504870529335296",
    traces_sample_rate=0.85,
    integrations=[
        sentry_logging
    ]
)

# division_by_zero = 1 / 0
