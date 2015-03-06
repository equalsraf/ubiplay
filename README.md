Minimal web based music player, with some tricks up its sleeve.
Written in Python3/Flask. Available under the New BSD license.

The following should suffice to get you started

    pip install -r requirements.txt
    python app.py

You also need a VLC instance running and a Redis server (optional). My usual
vlc command, for a headless setup, looks like this

    vlc --no-video --intf telnet --telnet-password music


[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/equalsraf/ubiplay/badges/quality-score.png?b=master)](https://scrutinizer-ci.com/g/equalsraf/ubiplay/?branch=tb-travis)
[![Build Status](https://travis-ci.org/equalsraf/ubiplay.svg?branch=master)](https://travis-ci.org/equalsraf/ubiplay)
[![Coverage Status](https://coveralls.io/repos/equalsraf/ubiplay/badge.png)](https://coveralls.io/r/equalsraf/ubiplay)

