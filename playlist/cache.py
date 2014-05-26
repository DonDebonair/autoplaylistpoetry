__author__ = 'Daan Debie'

from abc import ABCMeta
from abc import abstractmethod
from datetime import datetime


def datetime_from_http_datestring(datestring):
    """
    Converts a datestring as present in HTTP headers to a python datetime object
    """
    return datetime.strptime(datestring, '%a, %d %b %Y %H:%M:%S %Z')


def http_datestring_from_datetime(dt):
    # HTTP datetimes are always in TZ GMT
    return dt.strftime('%a, %d %b %Y %H:%M:%S GMT')


class PlaylistCache(object):
    """
    Abstract Base Class representing the cache for PlaylistItems
    This must be subclassed to implement a caching method. The subclass
    is responisble for serializing and deserializing PlaylistItem objects.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def get(self, key):
        """ Get a PlaylistItem from the cache """
        pass

    @abstractmethod
    def put(self, key, value):
        """ Put a PlaylistItem in the cache """
        pass

    @abstractmethod
    def remove(self, key):
        """ Remove a PlaylistItem from cache """
        pass


class PlaylistItem:

    def __init__(self, name, uri, last_modified, expires):
        self.name = name
        self.uri = uri
        self.last_modified = last_modified
        self.expires = expires

    def is_expired(self):
        return datetime.utcnow() > self.expires

    def __str__(self):
        return self.name


class MemPlaylistCache(PlaylistCache):
    """
    Naive caching implementation for in-memory caching, using a simple dictionary for storing PlaylistItems
    """

    def __init__(self):
        self.cache = {}

    def get(self, key):
        if key in self.cache:
            return self.cache[key]
        else:
            return None

    def put(self, key, value):
        self.cache[key] = value

    def remove(self, key):
        del self.cache[key]

    def __str__(self):
        output = ""
        for key in self.cache.iterkeys():
            output += "* {} / {} \n".format(key, self.cache[key].uri)
        return output