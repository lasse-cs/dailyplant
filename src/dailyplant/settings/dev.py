# ruff: noqa: F403, F405

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-aa&4vd$(h1t&-*y1t@i6_h$$!-1t!#@yj@-ufi2+ft8)hg)l=b"

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INSTALLED_APPS += [
    # Django Pattern Library
    "pattern_overrides",
    "pattern_library",
    # Django Browser Reload
    "django_browser_reload",
    # Django Debug Toolbar
    "debug_toolbar",
    "wagtail.contrib.styleguide",
]

# Debug Toolbar should be as early as possible in the middleware list
# However, it must come after middleware which encodes responses.
# In our case - that is one by default
MIDDLEWARE = [
    # Debug Toolbar should be early in the middleware list
    *MIDDLEWARE[:1],
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    *MIDDLEWARE[1:],
    # Browser Reload can be at the end
    "django_browser_reload.middleware.BrowserReloadMiddleware",
]

# Pattern Library Setup
TEMPLATES[0]["OPTIONS"]["builtins"] = [
    "pattern_library.loader_tags",
]

X_FRAME_OPTIONS = "SAMEORIGIN"

PATTERN_LIBRARY = {
    "SECTIONS": (
        ("components", ["patterns/components"]),
        ("pages", ["patterns/pages"]),
    ),
    "TEMPLATE_SUFFIX": ".html",
    "PATTERN_BASE_TEMPLATE_NAME": "patterns/base_pattern.html",
    "BASE_TEMPLATE_NAMES": ["patterns/base.html", "patterns/pages/error/500.html"],
}

# Required for the Debug Toolbar
INTERNAL_IPS = [
    "127.0.0.1",
]

DJANGO_VITE_SERVER_URL = "http://localhost:5173/static"

try:
    from .local import *
except ImportError:
    pass
