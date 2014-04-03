#!/usr/bin/env python

"""
A simple Command Line utility to generate Spotify playlists based on a passed message.
Can be used for one-off invocations or as an interactive shell script.
Also allows the use of Redis as a caching mechanism.

"""

__author__ = 'Daan Debie'

import argparse
import sys
import re
from playlist.generator import PlaylistGenerator
from playlist.generator import spotify_uri_to_url
from playlist.cache import MemPlaylistCache
from playlist.rediscache import RedisPlaylistCache
from playlist.generator import ApiException
from playlist.plthreading import generate_multiple_playlists_threaded


def main():
    parser = argparse.ArgumentParser(description="Generate a Spotify playlist from the provided message")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-m", "--message", help="The message you want turned into a playlist")
    group.add_argument("-i", "--interactive", help="Run this script in interactive mode",  action='store_true')
    parser.add_argument("-v", "--verbose", help="increase output verbosity",  action='store_true')
    parser.add_argument("-u", "--url", help="use Spotify web url instead of uri",  action='store_true')
    parser.add_argument("-r", "--redis", help="use Redis for caching",  action='store_true')
    parser.add_argument("-s", "--server", help="Hostname of Redis instance", default='localhost')
    parser.add_argument("-p", "--port", help="Port of Redis instance", type=int, default=6379)
    parser.add_argument("-d", "--database", help="Redis db to use", type=int, default=0)
    parser.add_argument("-w", "--password", help="Redis password to use")
    args = parser.parse_args()

    if args.redis:
        cache = RedisPlaylistCache(args.server, args.port, args.database, args.password)
    elif args.interactive:
        cache = MemPlaylistCache()
    else:
        # If user doesn't want Redis cache, and uses the script for processing one message, in-memory caching is useless
        cache = None

    if not args.interactive:
        try:
            # Split sentences into separate messages
            messages = [message for message in re.split(r'[.?!/\n]', args.message) if len(message) > 0]
            if len(messages) > 1:
                # If we have multiple messages, process them concurrently
                playlist = []
                incomplete = False
                results = generate_multiple_playlists_threaded(messages, cache)
                for result in results:
                    if result[1]:
                        incomplete = True
                    playlist.extend(result[0])
            else:
                pl_gen = PlaylistGenerator(cache)
                playlist, incomplete = pl_gen.generate_playlist(messages[0])
            if playlist:
                if incomplete and args.verbose:
                    print "Only partial playlist available:"
                for item in playlist:
                    if args.url:
                        url = spotify_uri_to_url(item.uri)
                    else:
                        url = item.uri

                    if args.verbose:
                        print item.name + ": " + url
                    else:
                        print url
            else:
                print "Not able to generate playlist!"
        except ApiException as e:
            sys.exit("An API error occured({})! Exiting...".format(str(e.status)))
    else:
        print "Welcome to PlaylistPoetry interactive mode."
        print "Enter a message to generate a playlist."
        print "Type :exit to quit."
        pl_gen = PlaylistGenerator(cache)
        while True:
            message = raw_input('> ')

            if message.lower() == ':exit':
                break

            try:
                print "Processing..."
                # Split sentences into separate messages
                messages = [message for message in re.split(r'[.?!/\n]', message) if len(message) > 0]
                if len(messages) > 1:
                    # If we have multiple messages, process them concurrently
                    playlist = []
                    incomplete = False
                    results = generate_multiple_playlists_threaded(messages, cache)
                    for result in results:
                        if result[1]:
                            incomplete = True
                        playlist.extend(result[0])
                else:
                    pl_gen = PlaylistGenerator(cache)
                    playlist, incomplete = pl_gen.generate_playlist(messages[0])
                if playlist:
                    if incomplete and args.verbose:
                        print "Only partial playlist available:"
                    for item in playlist:
                        if args.url:
                            url = spotify_uri_to_url(item.uri)
                        else:
                            url = item.uri

                        print item.name + ": " + url

                else:
                    print "Not able to generate playlist!"
            except ApiException as e:
                sys.exit("An API error occured({})! Exiting...".format(str(e.status)))



if __name__ == '__main__':
    main()