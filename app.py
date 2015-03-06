"""
Ubiplay, the happy Internet powered music player
"""

import subprocess, os
from flask import Flask, request, render_template, jsonify
import json
from logging import warn
from vlccontrol import VlcControl, VlcControlException
import queue
from threading import Thread
import redis

HOSTNAME = 'localhost'
PORT = 4212
# FIXME: deprecate this in favour of API arguments
PASSWORD = os.getenv('UBIPLAY_PASSWORD', 'music')

app = Flask(__name__)

def vlc():
    """Shortcut to get vlc control instance."""
    return VlcControl(HOSTNAME, PORT, PASSWORD)

# Work queue for youtube-dl
WORK_QUEUE = queue.Queue()

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
@app.errorhandler(ConnectionRefusedError)
def jsonrequest_errorhandler(ex):
    """Turn backend connection error into json response message."""
    warn(ex)
    resp = jsonify({'error':'VLC Service is unavailable'})
    resp.status_code = 500
    return resp
@app.errorhandler(VlcControlException)
def jsonrequest_errorhandler(ex):
    """Turn backend connection error into json response message."""
    warn(ex)
    resp = jsonify({'error':'Error calling VLC backend'})
    resp.status_code = 500
    return resp

@app.route('/ydl_addurl', methods=['POST'])
def ydl_addurl():
    if not request.json.get('url', None):
        raise APIException('Invalid Request, need URL', 400)

    try:
        WORK_QUEUE.put(request.json.get('url'), True, 0.5)
    except queue.Full as ex:
        raise ex
    except Exception as ex:
        raise APIException('Unable to queue Url', source=ex)

    return jsonify({})

@app.route('/playid', methods=['POST'])
def playid():
    """Play specific song."""
    if request.json.get('songid', None) == None:
        raise APIException('No songid was given', 400)
    vlc().goto(int(request.json.get('songid')))
    return status()

@app.route('/deleteid', methods=['POST'])
def deleteid():
    """Remove specific song."""
    if request.json.get('songid', None) == None:
        raise APIException('No songid was given', 400)
    vlc().delete(int(request.json.get('songid')))
    return status()

@app.route('/setvol', methods=['POST'])
def setvol():
    """Set the volume."""
    if request.json.get('volume', None) == None:
        raise APIException('No volume was given', 400)
    # Volume is [0-100], Vlc works in the [0-256] range
    val = int((request.json.get('volume')/100)*256)
    vlc().volume = val
    return status()

@app.route('/moveid', methods=['POST'])
def moveid():
    """Move a given song id to a given position."""
    # FIXME: not implemented
    return status()

def normalize_volume(val):
    """VLC volume range is 0-256 (or more), normalize to 0-100"""
    volume = int((val / 256)*100)
    return volume

@app.route('/status')
def status():
    """Get MPD status."""
    return jsonify({'volume':normalize_volume(vlc().volume)})

@app.route('/previous')
def prevsong():
    """Go to the previous song."""
    vlc().prev()
    return status()

@app.route('/play')
def play():
    """If stopped, start playback."""
    vlc().play()
    return status()

@app.route('/pause')
def pause():
    """Pause the playback."""
    vlc().pause()
    return status()

@app.route('/next')
def nextsong():
    """Go to the next song."""
    vlc().next()
    return status()

@app.route('/stop')
def stop():
    """Stop playback."""
    vlc().stop()
    return status()

@app.route('/clear')
def clear():
    """Clear the playlist."""
    vlc().clear()
    return status()

@app.route('/enqueue', methods=['POST'])
def enqueue():
    """Add URL on the playlist."""
    if not request.json.get('url', None):
        raise APIException('Invalid Request, need URL', 400)
    vlc().enqueue(request.json.get('url'), True, 0.5)
    return jsonify(result)

@app.route('/playlistinfo')
def playlistinfo():
    """Return current playlist."""
    result = {}
    for item in vlc().playlist():
        trackinfo = item.split('-', 1)
        if len(trackinfo) < 2:
            continue
        songid = trackinfo[0].strip()
        description = trackinfo[1].strip()
        title = description.split(' ')[0]
        if title in ('Media', 'Playlist'):
            continue

        try:
            r = redis.StrictRedis()
            metadata = r.get(title)
            if metadata:
                metadata = json.loads(metadata.decode('utf8'))
                title = metadata['title']
        except redis.exceptions.ConnectionError:
            # We can work without redis, but we cant store
            # metadata
            pass

        result[songid] = {'id':songid, 'title':title}
    return jsonify(result)


@app.route('/')
def index():
    """Front page."""
    return render_template('index.html')

@app.route('/history')
def history():
    try:
        r = redis.StrictRedis()
        result = r.lrange('history', 0, -1) or []
    except redis.exceptions.ConnectionError:
        return jsonify({'history':[]})

    return jsonify({'history':result})

# Background worker
def ydl_worker():
    """
    ydl worker reads URLs from the queue, calls youtube-dl to handle them,
    and queues the result into Vlc
    """
    while True:
        url = WORK_QUEUE.get(True)
        cmd = ["youtube-dl", "-j", "--prefer-insecure", \
                    "-f", "mp4/http_mp3_128_url", "-i", url]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        vlc_instance = vlc()

        while True:
            line = proc.stdout.readline()
            if not line:
                break
            song = json.loads(line.decode('utf8'))

            try:
                # Store reverse mapping in Redis
                r = redis.StrictRedis()
                # Expire entry after 24h
                r.setex(song['url'], 3600*24, line)
                r.lpush('history', url)
                r.ltrim('history', 0, 30)
            except redis.exceptions.ConnectionError:
                pass

            vlc_instance.enqueue(song['url'])

worker = Thread(target=ydl_worker)
worker.setDaemon(True)
worker.start()

if __name__ == '__main__':
    app.debug = os.getenv('DEBUG')
    app.run(host='0.0.0.0', port=8080)

