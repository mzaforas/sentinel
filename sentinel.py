# -*- coding: utf-8 -*-

# all the imports
from httplib import HTTPConnection

import sys
import os
import os.path
import arrow
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash

# app instance
from tasks import make_celery

app = Flask(__name__)

# configuration
DEBUG = True
SECRET_KEY = 'development key'
PROPAGATE_EXCEPTIONS = True
app.config.from_object(__name__)

STOREX_PATH = '/media/STOREX'
DOWNLOADS_PATH = '/Descargas'
DESTINATION_CATEGORIES_PATHS = {'peliculas': 'Peliculas',
                                'series': 'Series',
                                'musica': 'Musica'}
XBMC_HOST = '192.168.1.10'
XBMC_PORT = '8080'
XBMC_SCAN_METHODS = {'peliculas': 'VideoLibrary.Scan',
                     'series': 'VideoLibrary.Scan',
                     'musica': 'AudioLibrary.Scan'}
app.config.update(
    CELERY_BROKER_URL='amqp://guest@localhost:5672//',
    CELERY_RESULT_BACKEND='amqp://guest@localhost:5672//',
)
celery = make_celery(app)


# controllers
@app.route("/")
def index():
    return render_template('index.html')


@app.route("/downloads")
def downloads():
    """
    Download list for classify
    """
    downloads_list = os.listdir(STOREX_PATH+'/'+DOWNLOADS_PATH)
    return render_template('downloads.html', downloads=downloads_list)


@app.route("/classify/<name>/<category>")
def classify(name, category):
    """
    Classify downloaded element
    """
    try:
        os.renames(os.path.normpath(STOREX_PATH+'/'+DOWNLOADS_PATH+'/'+name),
                   os.path.normpath(STOREX_PATH+'/'+DESTINATION_CATEGORIES_PATHS[category]+'/'+name))
        # call XBMC to update collection
        #xbmc_jsonrpc = 'jsonrpc?request={"jsonrpc": "2.0", "method": "{method}"}'.format(method=XBMC_SCAN_METHODS[category])
        #conn = HTTPConnection(host=XBMC_HOST, port=XBMC_PORT)
        #conn.request(method='GET', url=xbmc_jsonrpc)
        # working here
    except OSError as e:
        flash(u'Error mientras se movía "{name}" a "{category}": {error}'.format(name=name, category=category, error=e.strerror))
    else:
        flash(u'"{name}" movido correctamente a "{category}"'.format(name=name, category=category))

    return redirect(url_for('downloads'))


@app.route("/run_sentinel")
def run_sentinel():
    execfile('/home/pi/sentinel/scripts/transmission_sentinel.py')

    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host='0.0.0.0')
