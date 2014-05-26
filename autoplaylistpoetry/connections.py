from flask import g, current_app
from playlist.rediscache import RedisPlaylistCache


def get_redis_cache():
    host = current_app.config['REDIS_HOST']
    port = current_app.config['REDIS_PORT']
    database = current_app.config['REDIS_DB']
    password = current_app.config['REDIS_PASSWORD']
    redis_cache = getattr(g, '_redis_cache', None)
    if redis_cache is None:
        redis_cache = g._redis_cache = RedisPlaylistCache(host, port, database, password)

    return redis_cache