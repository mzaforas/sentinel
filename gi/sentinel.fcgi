#!/usr/bin/python
import sys
sys.path.insert(0, '/home/pi/sentinel/')

from flup.server.fcgi import WSGIServer
from sentinel import app

if __name__ == '__main__':
    WSGIServer(app).run()
