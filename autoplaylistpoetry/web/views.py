import logging.config
import os
import re

from flask import Blueprint, send_from_directory, render_template, request

from playlist.generator import PlaylistGenerator, spotify_uri_to_url, ApiException
from playlist.plthreading import generate_multiple_playlists_threaded
from playlist.rediscache import RedisPlaylistCache


web = Blueprint('web', __name__)
logger = logging.getLogger(__name__)

@web.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(web.root_path, 'static'), 'ico/favicon.ico')


@web.errorhandler(404)
def page_not_found(e):
    return render_template('web/404.html'), 404


@web.route('/')
def index():
    return render_template('web/index.html')


@web.route('/create')
def create():
    return render_template('web/create.html')


@web.route('/generate', methods=['POST'])
def generate():
    host = 'localhost'
    port = 6379
    database = 0
    password = None
    cache = RedisPlaylistCache(host, port, database, password)
    message = request.form['source-text']
    logger.info("Generating playlist from message: %s", message)
    try:
        if message:
            messages = [sentence for sentence in re.split(r'[.?!/\n]', message) if len(sentence) > 0]
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
                heading = "This is your playlist"
                if incomplete:
                    subheading = "Only partial playlist available"
                else:
                    subheading = None
                generated_playlist = [(item.name, item.uri, spotify_uri_to_url(item.uri)) for item in playlist]
            else:
                heading = "Not able to generate playlist!"
                subheading = "Please try another phrase"
                generated_playlist = None
        else:
            heading = "Empty message provided!"
            subheading = "Please try a real phrase"
            generated_playlist = None
    except ApiException as e:
        heading = "Something's wrong with the Spotify API"
        subheading = "Statuscode returned: {}".format(str(e.status))
        logger.warn("An error occured with the Spotify API. Statuscode: %s", e.status)
        generated_playlist = None

    return render_template('web/generate.html', message=message, heading=heading, subheading=subheading,
                           playlist=generated_playlist)