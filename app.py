"""
A Happy MPD web service
"""
import subprocess, os, mpd
from flask import Flask, g, abort, request
from functools import wraps
import json

HOSTNAME = os.getenv("MPD_HOSTNAME", "localhost")
PASSWORD = os.getenv('MPD_PASSWORD', None)

app = Flask(__name__)
app.debug = os.getenv('DEBUG')

def needsmpd(f):
    """
    Decorator to setup/teardown MPD connection.

    - MPDClient instance is available as g.client
    - If MPD is not available raise 503
    - If MPD authentication fails, raise 403
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            g.client = mpd.MPDClient()
            g.client.connect(HOSTNAME, 6600)
        except Exception as ex:
            abort(503)

        if PASSWORD:
            try:
                g.client.password(PASSWORD)
            except:
                abort(403)

        res = f(*args, **kwargs)
        g.client.disconnect()
        return res
    return wrapper

def version_tuple(s):
    return tuple(s.split('.'))

def queue_youtube(url, mpdcli):
    """
    Call youtube-dl to get track information and queue a song into MPD.
    If python-mpd2 supports it set track metadata

    Returns list of mpd song ids
    """
    out = subprocess.check_output(["youtube-dl", "-j", "--prefer-insecure", "-f", "140", "-i", url])

    songids = []
    for line in out.splitlines():
        song = json.loads(line)
        songid = mpdcli.addid(song['url'])

        if version_tuple(mpdcli.mpd_version) >= version_tuple('0.19.0'):
            mpdcli.addtagid(songid, 'Album', 'YouTube')
            mpdcli.addtagid(songid, 'Title', song['title'])

        songids.append(songid)

    return songids

@app.route('/addurl', methods=['POST'])
@needsmpd
def addurl():
    if not request.headers['Content-Type'] == 'application/json':
        abort(400)
    if not request.json.get('url', None):
        abort(400)

    try:
        songs = queue_youtube(request.json.get('url'), g.client)
    except:
        return 'ups'
    return 'yay'

@app.route('/add/<youtubeId>')
@needsmpd
def add(youtubeId):
    url="http://www.youtube.com/watch?v="+youtubeId
    try:
        songs = queue_youtube(url, g.client)
    except:
        return 'ups'
    return 'yay'

@app.route('/play')
@needsmpd
def play():
    g.client.play()
    return 'aye sir, full steam ahead!'

@app.route('/stop')
@needsmpd
def stop():
    g.client.stop()
    return 'aye sir, stopping the ship!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

