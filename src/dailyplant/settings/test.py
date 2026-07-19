# ruff: noqa: F403, F405

from .base import *
import tempfile

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-aa&4vd$(h1t&-*y1t@i6_h$$!-1t!#@yj@-ufi2+ft8)hg)l=b"

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

MEDIA_ROOT = tempfile.gettempdir()

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "db.sqlite3",
        "TEST": {
            # Don't use in-memory sqlite database
            # So that possible to reuse the DB
            "NAME": "test_db.sqlite3",
        },
    }
}

INSTALLED_APPS += ["core.testapp"]

try:
    from .local import *
except ImportError:
    pass
