# -*- coding: utf-8 -*-

# all the imports
import sys
import os
import os.path

import arrow
import requests
import git

from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash

# app instance
from tasks import make_celery

app = Flask(__name__)

# configuration
DEBUG = True
SECRET_KEY = 'development key'
PROPAGATE_EXCEPTIONS = True
app.config.from_object(__name__)
PROJECT_ROOT = '/home/pi/sentinel'

STOREX_PATH = '/media/STOREX'
DOWNLOADS_PATH = '/Descargas'
DESTINATION_CATEGORIES_PATHS = {'peliculas': 'Peliculas',
                                'series': 'Series',
                                'musica': 'Musica'}
XBMC_HOST = '192.168.1.10'
XBMC_PORT = '8080'
XBMC_USER = 'xbmc'
XBMC_PASSWD = 'xbmc'
XBMC_SCAN_METHODS = {'peliculas': 'VideoLibrary.Scan',
                     'series': 'VideoLibrary.Scan',
                     'musica': 'AudioLibrary.Scan'}

# app.config.update(
#     CELERY_BROKER_URL='amqp://guest@localhost:5672//',
#     CELERY_RESULT_BACKEND='amqp://guest@localhost:5672//',
# )
# celery = make_celery(app)


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
        xbmc_jsonrpc = 'jsonrpc?request={"jsonrpc": "2.0", "method": "%s"}' % XBMC_SCAN_METHODS[category]
        requests.get('http://{host}:{port}/{url}'.format(host=XBMC_HOST, port=XBMC_PORT, url=xbmc_port, auth=(XBMC_USER, XBMC_PASSWD)))
    except OSError as e:
        flash(u'Error mientras se movía "{name}" a "{category}": {error}'.format(name=name, category=category, error=e.strerror))
    else:
        flash(u'"{name}" movido correctamente a "{category}"'.format(name=name, category=category))

    return redirect(url_for('downloads'))


@app.route("/run-sentinel")
def run_sentinel():
    execfile('%s/scripts/transmission_sentinel.py' % PROJECT_ROOT)

    return redirect(url_for('index'))

@app.route("/git-hook")
def git_hook():
    g = git.cmd.Git(PROJECT_ROOT)                 
    g.pull()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host='0.0.0.0')
