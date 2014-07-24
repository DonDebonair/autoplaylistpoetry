import logging
import re
from datetime import timedelta
from datetime import datetime

import requests

from message_tools import MessageChunker
from cache import PlaylistCache
from cache import PlaylistItem
from cache import datetime_from_http_datestring
from cache import http_datestring_from_datetime

SPOTIFY_BASE_TRACK_URL = 'http://open.spotify.com/track/'
SPOTIFY_API_SEARCH_TRACK_URL = 'https://api.spotify.com/v1/search'
VALID_API_STATUSCODES = [200, 304, 404]

logger = logging.getLogger(__name__)


def spotify_uri_to_url(uri):
    uri_match = re.match(r'spotify:track:(?P<id>\w{22})', uri)
    if uri_match:
        return SPOTIFY_BASE_TRACK_URL + uri_match.group('id')
    return None


class PlaylistGenerator(object):
    """
    Class for generating Spotify playlists using the Spotify Metadata API.
    It optionally caches the queries using a PlaylistCache object that is passed to the constructor

    """

    def __init__(self, cache=None):
        self.cache = cache
        # I know we're all consenting adults here, but still, we really need a PlaylistCache instance here...
        if self.cache and not isinstance(self.cache, PlaylistCache):
            raise AttributeError

    def generate_playlist(self, message, use_max_chunk_length=False):
        """
        Generates a Spotify playlist based on a passed message.

        returns a list containing PlaylistItem(s)
        """

        # Filter non-alphanumeric, non-space characters
        message = re.sub(r'[^a-zA-Z0-9\s\']', '', message)
        # We want our playlist to contain at least two songs, so max_chunk_length must be less than total sentence length
        # can be overridden with the use_max_chunk_length
        if use_max_chunk_length:
            max_chunk_length = len(message.split())
        else:
            max_chunk_length = len(message.split()) - 1
        chunker = MessageChunker(message, max_chunk_length)
        playlist = []
        discarded_playlists = []
        index = 0
        words_covered = 0
        for chunk in chunker:
            if not chunk:
                # The current list of (remaining) groups is depleted, so we're backtracking
                discarded_playlists.append([item for item in playlist])
                words_covered -= len(playlist.pop().name.split())
                index -= 1
                continue

            title = " ".join(chunk[index]).strip().lower()

            if self.cache:
                try:
                    item = self._fetch_item_from_cache(title)
                except ApiException:
                    raise
                if item:
                    playlist.append(item)
                    words_covered += len(chunk[index])
                    index += 1
                    chunker.progress()
                    continue

            try:
                item = self._fetch_item_from_api(title)
            except ApiException:
                raise
            if item:
                if self.cache:
                    self.cache.put(title, item)
                playlist.append(item)
                # Keep track of how many words are covered by our current playlist
                words_covered += len(chunk[index])
                index += 1
                chunker.progress()
        if not playlist or words_covered < len(message.split()):
            # Apperently no complete playlist could be constructed, so we're taking the best effort
            incomplete = True
            sorted_playlists = sorted(discarded_playlists, key=len, reverse=True)
            playlist = sorted_playlists[0] if sorted_playlists else playlist
        else:
            incomplete = False
        return playlist, incomplete

    @staticmethod
    def _fetch_item_from_api(title):
        """
        Does a Spotify Metadata search and returns the first valid result
        """
        params = {'q': title, 'type': 'track'}
        r = requests.get(SPOTIFY_API_SEARCH_TRACK_URL, params=params)

        # Something bad happened with the API that we can't recover from
        if r.status_code not in VALID_API_STATUSCODES:
            raise ApiException(r.status_code)
        elif r.status_code == 404:
            return None

        last_modified = datetime_from_http_datestring(r.headers['Date'])
        max_age_match = re.match(r'.*max-age=(?P<age>\d+)', r.headers['Cache-Control'])
        if max_age_match:
            max_age = int(max_age_match.group('age'))
        else:
            max_age = None
        expires = datetime.utcnow() + timedelta(seconds=max_age)
        decoded_result = r.json()
        track_listing = decoded_result['tracks']['items']

        # Valid track is any track whose name resembles the title we're looking for
        # Spotify Metadata API also returns tracks whose ALBUM name resembles the query...
        valid_tracks = [track for track in track_listing if title == track['name'].lower().strip()]
        if valid_tracks:
            return PlaylistItem(valid_tracks[0]['name'], valid_tracks[0]['uri'], last_modified, expires)
        else:
            return None

    def _fetch_item_from_cache(self, title):
        """
        Looks up the title in cache, validates it and returns it if valid
        """

        # Get item from cache
        cached_item = self.cache.get(title)
        # If it's not expired, go with it
        if cached_item and not cached_item.is_expired():
            logger.debug("Cache hit for '%s'", title)
            return cached_item
        # If it's expired, query the API using if-modified-since to see if cache is still valid
        elif cached_item:
            logger.debug("Cache expired for '%s'", title)
            modified_since = http_datestring_from_datetime(cached_item.last_modified)
            params = {'q': title, 'type': 'track'}
            headers = {'If-Modified-Since': modified_since}
            r = requests.get(SPOTIFY_API_SEARCH_TRACK_URL, params=params, headers=headers)

            # Something bad happened with the API that we can't recover from
            if r.status_code not in VALID_API_STATUSCODES:
                raise ApiException(r.status_code)
            # If we get statuscode 304, we can still use the cached item
            if r.status_code == 304:
                logger.debug("Cache still valid for '%s'", title)
                return cached_item
            else:
                logger.debug("Cache invalidated for '%s'", title)
                self.cache.remove(title)
                return None


class ApiException(Exception):
    def __init__(self, status):
        self.status = status

