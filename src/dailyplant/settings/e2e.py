from .test import *

CACHES["default"]["BACKEND"] = "django.core.cache.backends.locmem.LocMemCache"

# Use a different database for e2e tests
DATABASES["default"]["TEST"]["NAME"] = "test_e2e_db.sqlite3"
