# ruff: noqa: F403, F405
from .base import *

DEBUG = False

# ManifestStaticFilesStorage is recommended in production, to prevent
# outdated JavaScript / CSS assets being served from cache
# (e.g. after a Wagtail upgrade).
# See https://docs.djangoproject.com/en/5.2/ref/contrib/staticfiles/#manifeststaticfilesstorage
STORAGES["staticfiles"]["BACKEND"] = "dailyplant.storage.ManifestStaticFilesStorage"
SECRET_KEY = ""

INSTALLED_APPS += [
    "django.contrib.postgres",
]

try:
    from .local import *
except ImportError:
    pass
