import os
import json
import functools
import redis

TTL = 3600  # 1 hour

try:
    _redis = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379)),
        decode_responses=True,
        socket_connect_timeout=1,
    )
    _redis.ping()
    REDIS_AVAILABLE = True
except Exception:
    _redis = None
    REDIS_AVAILABLE = False


def cached(key_fn):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if not REDIS_AVAILABLE:
                return fn(*args, **kwargs)
            key = key_fn(*args, **kwargs)
            hit = _redis.get(key)
            if hit:
                return json.loads(hit)
            result = fn(*args, **kwargs)
            _redis.setex(key, TTL, json.dumps(result))
            return result
        return wrapper
    return decorator
