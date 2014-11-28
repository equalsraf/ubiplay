"""
A Happy MPD web service
"""
import subprocess, os, mpd
from flask import Flask, g, abort, request, render_template, jsonify
from functools import wraps
import json
from logging import warn

HOSTNAME = os.getenv("MPD_HOSTNAME", "localhost")
# FIXME: deprecate this in favour of API arguments
PASSWORD = os.getenv('MPD_PASSWORD', None)

app = Flask(__name__)

class APIException(Exception):
    """Raise this exception in API views to return a json error object."""
    def __init__(self, message, status_code=500, source=None):
        super(APIException, self).__init__(message)
        self.message = message
        self.status_code = status_code
        self.source = source

@app.errorhandler(APIException)
def jsonrequest_errorhandler(ex):
    """Turn APIException into json response message."""
    warn('%s: %s' % (ex.message, ex.source))
    resp = jsonify({'error':ex.message})
    resp.status_code = ex.status_code
    return resp

class MPDWrapper:
    """MPDClient wrapper, to delay connection."""

    def __init__(self, hostname, password=None, port=6600):
        self._hostname = hostname
        self._port = port
        self._password = password
        self._client = mpd.MPDClient()
        self._connected = False

    def __getattr__(self, attrname):
        """Only connect to server when getting an instance attribute."""
        attr = getattr(self._client, attrname)
        if not self._connected:
            self._connected = True

            try:
                self._client.connect(self._hostname, self._port)
            except Exception as ex:
                raise APIException('Unable to reach MPD server', 503, source=ex)

            if self._password:
                try:
                    self._client.password(self._password)
                except Exception as ex:
                    raise APIException('Authentication failed', 403, source=ex)

        return attr

def needsmpd(func):
    """Create MPDClient as g.client."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        g.client = MPDWrapper(HOSTNAME, password=PASSWORD, port=6600)
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

    cmd = ["youtube-dl", "-j", "--prefer-insecure", \
                "-f", "140/http_mp3_128_url", "-i", url]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)

    songids = []
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        song = json.loads(line.decode('utf8'))
        songid = mpdcli.addid(song['url'])

        if version_tuple(mpdcli.mpd_version) >= version_tuple('0.19.0'):
            mpdcli.addtagid(songid, 'Album', 'youtube-dl')
            mpdcli.addtagid(songid, 'Title', song['title'])

        songids.append(songid)

    return songids

@app.route('/addurl', methods=['POST'])
@needsmpd
def addurl():
    """Add URL on the playlist."""
    if not request.json.get('url', None):
        raise APIException('Invalid Request, need URL', 400)

    try:
        queue_youtube(request.json.get('url'), g.client)
    except APIException as ex:
        raise ex
    except Exception as ex:
        raise APIException('Unable to queue Url', source=ex)

    return jsonify({})

@app.route('/status')
@needsmpd
def status():
    """Get MPD status."""
    return jsonify(g.client.status())

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
    return jsonify(g.client.status())

@app.route('/stop')
@needsmpd
def stop():
    """Stop playback."""
    g.client.stop()
    return jsonify(g.client.status())

@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.debug = os.getenv('DEBUG')
    app.run(host='0.0.0.0', port=8080)

