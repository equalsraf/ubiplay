"""Remote VLC telnet control."""
from telnetlib import Telnet

class VlcControlException(Exception):
    pass

class VlcControl(Telnet):
    """Control VLC through the telnet interface."""
    def __init__(self, host, port, password):
        self.password = password.encode('ascii')
        self.__timeout = 0.5
        Telnet.__init__(self, host, port)

    def open(self, host, port=4212, timeout=0.5):
        Telnet.open(self, host, port, timeout)
        idx, _, text = self.expect([b'Password: '])
        if idx == -1:
            raise VlcControlException('Authentication failed: %s' % text)
        self.write(self.password+b'\n')
        self.wait_for_prompt()

    def wait_for_prompt(self):
        """Wait for VLC prompt (>)

        Returns the text received before the prompt, or raises
        VlcControlException if the prompt is not received
        """
        idx, match, text = self.expect([b'> '], self.__timeout)
        if idx == -1:
            self.msg(text)
            self.close()
            raise VlcControlException('Did not receive prompt')
        return text[:match.start()].strip()

    def push_cmd(self, cmd, *args):
        """Send VLC command with the given arguments."""
        if args:
            params = b' ' + ' '.join([str(arg) for arg in args]).encode('ascii')
        else:
            params = b''
        self.write(cmd.encode('ascii') + params + b'\n')
        answer = self.wait_for_prompt()
        return answer

    # VLC commands as properties
    @property
    def volume(self):
        """The volume should be in range [0-256] (256 is 100%) but can be larger."""
        val = self.push_cmd('volume')
        return int(val)
    @volume.setter
    def volume(self, val):
        self.push_cmd('volume', val)

    @property
    def is_playing(self):
        val = self.push_cmd('volume')
        return bool(val)

    @property
    def time(self):
        val = self.push_cmd('get_time')
        return int(val)

    @property
    def length(self):
        val = self.push_cmd('get_length')
        return int(val)

    # VLC command functions
    def seek(self, time):
        self.push_cmd('seek', time)

    def enqueue(self, url):
        self.push_cmd('enqueue', url)

    def goto(self, item):
        self.push_cmd('goto', item)
    def delete(self, item):
        self.push_cmd('delete', item)
    def move(self, item, afteritem):
        self.push_cmd('move', item, afteritem)

    def playlist(self):
        """Return list of entries from the playlist."""
        result = self.push_cmd('playlist')
        plist = [entry.decode('utf8').lstrip('|').strip() for entry in result.splitlines() if entry.startswith(b'|')]
        return plist

    def play(self):
        self.push_cmd('play')
    def pause(self):
        self.push_cmd('pause')
    def stop(self):
        self.push_cmd('stop')
    def next(self):
        self.push_cmd('next')
    def prev(self):
        self.push_cmd('prev')
    def clear(self):
        self.push_cmd('clear')


