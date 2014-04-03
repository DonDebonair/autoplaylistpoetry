__author__ = 'Daan Debie'

from flask import Flask, render_template, send_from_directory, request
import os
import json
import re
from playlist.rediscache import RedisPlaylistCache
from playlist.plthreading import generate_multiple_playlists_threaded
from playlist.generator import PlaylistGenerator
from playlist.generator import spotify_uri_to_url
from playlist.generator import ApiException

application = app = Flask(__name__)
redis_env = os.getenv('VCAP_SERVICES')
if redis_env:
    redis_conf = json.loads(redis_env)
else:
    redis_conf = None


def get_credentials_from_env(redis_env):
    redis_key = [key for key in redis_env if key.startswith('redis')][0]
    redis = redis_env[redis_key][0]['credentials']
    return {'hostname': redis['hostname'], 'port': redis['port'], 'password': redis['password']}

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'ico/favicon.ico')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create')
def create():
    return render_template('create.html')

@app.route('/generate', methods=['POST'])
def generate():
    if redis_conf:
        conf = get_credentials_from_env(redis_conf)
        host = conf['hostname']
        port = conf['port']
        database = 0
        password = conf['password']
    else:
        host = 'localhost'
        port = 6379
        database = 0
        password = None
    cache = RedisPlaylistCache(host, port, database, password)
    message = request.form['source-text']
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
        generated_playlist = None

    return render_template('generate.html', message=message, heading=heading, subheading=subheading, playlist=generated_playlist)

@app.route('/api/playlist', methods=['GET'])
def api_playlist():
    if redis_conf:
        conf = get_credentials_from_env(redis_conf)
        host = conf['hostname']
        port = conf['port']
        database = 0
        password = conf['password']
    else:
        host = 'localhost'
        port = 6379
        database = 0
        password = None
    cache = RedisPlaylistCache(host, port, database, password)
    message = request.args.get('message')
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
                generated_playlist = [{'name': item.name, 'uri': item.uri, 'url': spotify_uri_to_url(item.uri)} for item in playlist]
                payload = {'success': True, 'partial': incomplete, 'playlist': generated_playlist}
            else:
                payload = {'error': True, 'message': "Not able to generate playlist!"}
        else:
            payload = {'error': True, 'message': "No message provided!"}
    except ApiException as e:
        payload = {'error': True, 'message': "The Spotify API returned an error({})".format(str(e.status))}

    return json.dumps(payload)

if __name__ == '__main__':
    app.run()