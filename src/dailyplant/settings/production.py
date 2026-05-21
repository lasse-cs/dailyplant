# ruff: noqa: F403, F405
from pathlib import Path
import os

import sentry_sdk

from .base import *

DEBUG = False

# ManifestStaticFilesStorage is recommended in production, to prevent
# outdated JavaScript / CSS assets being served from cache
# (e.g. after a Wagtail upgrade).
# See https://docs.djangoproject.com/en/6.0/ref/contrib/staticfiles/#manifeststaticfilesstorage
STORAGES["staticfiles"]["BACKEND"] = "dailyplant.storage.ManifestStaticFilesStorage"

ALLOWED_HOSTS = os.environ["DJANGO_ALLOWED_HOSTS"].split(",")
SECRET_KEY = Path(os.environ["DJANGO_SECRET_KEY_FILE"]).read_text().strip()

WAGTAILADMIN_BASE_URL = os.environ["WAGTAILADMIN_BASE_URL"]

# Deployment settings
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
CSRF_COOKIE_SECURE = True

INSTALLED_APPS += [
    "django.contrib.postgres",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["POSTGRES_DB"],
        "USER": os.environ["POSTGRES_USER"],
        "HOST": os.environ["POSTGRES_HOST"],
        "PASSWORD": Path(os.environ["POSTGRES_PASSWORD_FILE"]).read_text().strip(),
        "PORT": 5432,
    }
}

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
DEFAULT_FROM_EMAIL = os.environ.get("DJANGO_DEFAULT_FROM_EMAIL")
EMAIL_HOST = os.environ.get("DJANGO_EMAIL_HOST")
EMAIL_HOST_USER = os.environ.get("DJANGO_EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("DJANGO_EMAIL_HOST_PASSWORD")
EMAIL_PORT = 587
EMAIL_USE_TLS = True

if os.environ.get("SENTRY_DSN_FILE"):
    sentry_sdk.init(
        dsn=Path(os.environ["SENTRY_DSN_FILE"]).read_text().strip(),
        send_default_pii=False,
    )

if os.environ.get("WAGTAIL_SITE_NAME"):
    WAGTAIL_SITE_NAME = os.environ["WAGTAIL_SITE_NAME"]

try:
    from .local import *
except ImportError:
    pass
