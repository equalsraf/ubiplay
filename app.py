"""
A Happy MPD web service
"""
import subprocess, os, mpd
from flask import Flask, g
import json

HOSTNAME = os.getenv("MPD_HOSTNAME", "localhost")
PASSWORD = os.getenv('MPD_PASSWORD', None)

app = Flask(__name__)
app.debug = os.getenv('DEBUG')

@app.before_request
def before_request():
    """Connect to MPD with each request"""
    g.client = mpd.MPDClient()
    g.client.connect(HOSTNAME, 6600)
    if PASSWORD:
        g.client.password(PASSWORD)

@app.teardown_request
def teardown_request(exception):
    """Disconnect from MPD after each request"""
    try:
        g.client.disconnect()
    except:
        pass

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
        if hasattr(mpdcli, 'addtagid'):
            mpdcli.addtagid(songid, 'Album', 'YouTube')
            mpdcli.addtagid(songid, 'Title', song['title'])
        songids.append(songid)

    return songids

@app.route('/add/<youtubeId>')
def add(youtubeId):
    url="http://www.youtube.com/watch?v="+youtubeId
    try:
        songs = queue_youtube(url, g.client)
    except:
        return 'ups'
    return 'yay'

@app.route('/play')
def play():
    g.client.play()
    return 'aye sir, full steam ahead!'

@app.route('/stop')
def stop():
    g.client.stop()
    return 'aye sir, stopping the ship!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

