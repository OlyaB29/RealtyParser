import sentry_sdk
import logging
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

sentry_logging = LoggingIntegration(
    level=logging.INFO,
    event_level=logging.INFO
)

sentry_sdk.init(
    dsn="https://37e527ea531849dd84092732fbee6ab0@o4504847936192512.ingest.sentry.io/4504884139261952",
    integrations=[
        DjangoIntegration(),
        sentry_logging,
    ],
    traces_sample_rate=1.0,
    send_default_pii=True
)
