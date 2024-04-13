import os
import sentry_sdk
import logging
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from sentry_sdk.integrations.logging import LoggingIntegration

# All of this is already happening by default!
sentry_logging = LoggingIntegration(
    level=logging.ERROR,        # Capture info and above as breadcrumbs
    event_level=logging.ERROR  # Send errors as events
)

# pylint: disable=abstract-class-instantiated
sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DNS"),
    integrations=[DjangoIntegration(), RedisIntegration(), LoggingIntegration()],

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # We recommend adjusting this value in production.
    traces_sample_rate=0.5,

    # If you wish to associate users to errors (assuming you are using
    # django.contrib.auth) you may enable sending PII data.
    send_default_pii=True,

    _experiments={
    "profiles_sample_rate": 0.5,
  }
)