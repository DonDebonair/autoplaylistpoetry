import redis
from cache import PlaylistCache
from cache import PlaylistItem
import cache


class RedisPlaylistCache(PlaylistCache):
    """
    Caching implementation based on Redis. It uses Redis hashes to store multiple values present in a PlaylistItem
    on one key
    """

    def __init__(self, host='localhost', port=6379, database=0, password=None):
        self.database = redis.StrictRedis(host=host, port=port, db=database, password=password)

    def get(self, key):
        if self.database.exists(key):
            last_modified = cache.datetime_from_http_datestring(self.database.hget(key, 'last_modified'))
            expires = cache.datetime_from_http_datestring(self.database.hget(key, 'expires'))
            item = PlaylistItem(self.database.hget(key, 'name'), self.database.hget(key, 'uri'), last_modified, expires)
            return item
        else:
            return None

    def put(self, key, value):
        self.database.hset(key, 'name', value.name)
        self.database.hset(key, 'uri', value.uri)
        self.database.hset(key, 'last_modified', cache.http_datestring_from_datetime(value.last_modified))
        self.database.hset(key, 'expires', cache.http_datestring_from_datetime(value.expires))

    def remove(self, key):
        self.database.delete(key)