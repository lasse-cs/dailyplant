# Derived from django-ratelimit:
# https://github.com/jsocol/django-ratelimit
#
# Copyright (c) 2022 James Socol
# Licensed under the Apache License, Version 2.0.

import hashlib
import socket
import time
import zlib

from django.conf import settings
from django.core.cache import caches

EXPIRATION_FUDGE = 5


def _get_window(value, period):
    """
    Given a value, and time period return when the end of the current time
    period for rate evaluation is.
    """
    ts = int(time.time())
    if period == 1:
        return ts
    if not isinstance(value, bytes):
        value = value.encode("utf-8")
    # This logic determines either the last or current end of a time period.
    # Subtracting (ts % period) gives us the a consistent edge from the epoch.
    # We use (zlib.crc32(value) % period) to add a consistent jitter so that
    # all time periods don't end at the same time.
    w = ts - (ts % period) + (zlib.crc32(value) % period)
    if w < ts:
        return w + period
    return w


def _make_cache_key(view_key, window, per_period, period, item_key):
    return (
        "rl:"
        + hashlib.sha256(
            "".join([view_key, f"{per_period}/{period}", item_key, str(window)]).encode(
                "utf-8"
            )
        ).hexdigest()
    )


def is_ratelimited(view_key, item_key, per_period, period):
    window = _get_window(item_key, period)

    cache_key = _make_cache_key(view_key, window, per_period, period, item_key)
    count = None
    cache = caches[getattr(settings, "RATELIMIT_CACHE", "default")]
    try:
        added = cache.add(cache_key, 1, period + EXPIRATION_FUDGE)
    except socket.gaierror:
        added = False
    if added:
        count = 1
    else:
        try:
            count = cache.incr(cache_key)
        except ValueError:
            pass
    return count > per_period if count is not None else False
