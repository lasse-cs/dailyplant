# ruff: noqa: F403, F405
from pathlib import Path
import os

from django.core.exceptions import ImproperlyConfigured

from .base import *

DEBUG = False

# ManifestStaticFilesStorage is recommended in production, to prevent
# outdated JavaScript / CSS assets being served from cache
# (e.g. after a Wagtail upgrade).
# See https://docs.djangoproject.com/en/6.0/ref/contrib/staticfiles/#manifeststaticfilesstorage
STORAGES["staticfiles"]["BACKEND"] = (
    "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
)

ALLOWED_HOSTS = os.environ["DJANGO_ALLOWED_HOSTS"].split(",")
if "DJANGO_SECRET_KEY_FILE" in os.environ:
    SECRET_KEY = Path(os.environ["DJANGO_SECRET_KEY_FILE"]).read_text().split()
elif "DJANGO_SECRET_KEY" in os.environ:
    SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
else:
    raise ImproperlyConfigured(
        "Must specify Django Secret Key in the environment as a file with 'DJANGO_SECRET_KEY_FILE' or as 'DJANGO_SECRET_KEY'"
    )

try:
    from .local import *
except ImportError:
    pass
