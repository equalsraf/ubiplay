"""
A Happy MPD web service
"""
import subprocess, os, mpd
from flask import Flask, g, abort, request, render_template, jsonify
from functools import wraps
import json

# TODO: All mpd views should take a json request

HOSTNAME = os.getenv("MPD_HOSTNAME", "localhost")
# FIXME: deprecate this in favour of API arguments
PASSWORD = os.getenv('MPD_PASSWORD', None)

app = Flask(__name__)

def needsmpd(func):
    """
    Decorator to setup/teardown MPD connection.

    - MPDClient instance is available as g.client
    - If MPD is not available raise 503
    - If MPD authentication fails, raise 403
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            g.client = mpd.MPDClient()
            g.client.connect(HOSTNAME, 6600)
        except Exception:
            abort(503)

        if PASSWORD:
            try:
                g.client.password(PASSWORD)
            except:
                abort(403)

        res = func(*args, **kwargs)
        g.client.disconnect()
        return res
    return wrapper

def jsonrequest(func):
    """
    Decorator to handle JSON requests

    - If content-type is not application/json raise 400
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if request.json == None:
            abort(400)

        return func(*args, **kwargs)
    return wrapper


def version_tuple(version):
    """Split version string into tuple of strings."""
    return tuple(version.split('.'))

def queue_youtube(url, mpdcli):
    """
    Call youtube-dl to get track information and queue a song into MPD.
    If python-mpd2 supports it set track metadata

    Returns list of mpd song ids
    """
    out = subprocess.check_output(["youtube-dl", "-j", "--prefer-insecure", \
                "-f", "140/http_mp3_128_url", "-i", url])

    songids = []
    for line in out.splitlines():
        song = json.loads(line.decode('utf8'))
        songid = mpdcli.addid(song['url'])

        if version_tuple(mpdcli.mpd_version) >= version_tuple('0.19.0'):
            mpdcli.addtagid(songid, 'Album', 'YouTube')
            mpdcli.addtagid(songid, 'Title', song['title'])

        songids.append(songid)

    return songids

def json_error(errmsg, status_code=500):
    resp = jsonify({'error':errmsg})
    resp.status_code = status_code
    return resp

@app.route('/addurl', methods=['POST'])
@jsonrequest
@needsmpd
def addurl():
    """Add URL on the playlist."""
    if not request.json.get('url', None):
        return json_error('Invalid Request, need URL', 400)

    try:
        queue_youtube(request.json.get('url'), g.client)
    except:
        return json_error('Unable to queue Url')

    return jsonify({})

@app.route('/add/<youtubeId>')
@needsmpd
def add(ytid):
    url = "http://www.youtube.com/watch?v="+ytid
    try:
        queue_youtube(url, g.client)
    except:
        return 'ups'
    return 'yay'

@app.route('/play')
@needsmpd
def play():
    """If stopped, start playback."""
    g.client.play()
    return 'aye sir, full steam ahead!'

@app.route('/stop')
@needsmpd
def stop():
    """Stop playback."""
    g.client.stop()
    return 'aye sir, stopping the ship!'

@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.debug = os.getenv('DEBUG')
    app.run(host='0.0.0.0', port=8080)

