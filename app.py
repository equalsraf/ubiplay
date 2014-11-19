"""
A Happy MPD web service
"""
import subprocess, os, mpd
from flask import Flask, g

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

def youtube_dl(url):
    out = subprocess.check_output(["youtube-dl", "--prefer-insecure", "-f", "140", "-i", "-g", url])
    return out.splitlines()

@app.route('/add/<youtubeId>')
def add(youtubeId):
    url="http://www.youtube.com/watch?v="+youtubeId
    try:
        g.client.add(*youtube_dl(url))
        g.client.play()
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

