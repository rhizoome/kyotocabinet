"""
==================
kyotocabinet.utils
==================
"""
import time


def green_iter(iterable, sleep_every=100):
    """Return control to gevent hub every sleep_every iterations."""
    for index, item in enumerate(iterable, 1):
        yield item
        if index % sleep_every == 0:
            green_sleep(0)


def smart_str(value, encoding='utf-8', errors='strict'):
    """Convert Python object to string."""
    if isinstance(value, dict):
        return str(
            {
                smart_str(dict_key): smart_str(dict_value)
                for dict_key, dict_value in value.items()
            }
        )
    if isinstance(value, (list, tuple)):
        return str(tuple(map(smart_str, value)))
    if isinstance(value, bytes):
        return value.decode(encoding, errors)
    return str(value)


try:
    import gevent.monkey
except ImportError:
    _gevent_enabled = False
else:
    _gevent_enabled = gevent.monkey.saved

if _gevent_enabled:
    green_sleep = time.sleep
else:

    def green_sleep(seconds):
        pass


del _gevent_enabled
