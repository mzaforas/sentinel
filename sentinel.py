# -*- coding: utf-8 -*-

import sys
#reload(sys)
#sys.setdefaultencoding('utf-8')

import os
import os.path
import re

import arrow
import requests
import git
import logging
from logging.handlers import SMTPHandler

from fabric.operations import run
from fabric.api import env

from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from credentials import *

from tasks import make_celery

app = Flask(__name__)

# configuration
DEBUG = True
SECRET_KEY = 'development key'
PROPAGATE_EXCEPTIONS = True
app.config.from_object(__name__)
PROJECT_ROOT = '/home/pi/sentinel'

ADMINS = ['mzaforas@gmail.com']
mail_handler = SMTPHandler('smtp.gmail.com', fromaddr,
                           ADMINS, 'Sentinel Error',
                           credentials=(mail_username, mail_password))
mail_handler.setLevel(logging.ERROR)
app.logger.addHandler(mail_handler)

HDD_PATH = '/media/elements'
DOWNLOADS_PATH = '/Descargas'
DESTINATION_CATEGORIES_PATHS = {'peliculas': 'Peliculas',
                                'series': 'Series',
                                'musica': 'Musica'}
XBMC_HOST = 'kodi'
XBMC_PORT = '8080'
XBMC_USER = 'kodi'
XBMC_PASSWD = ''
XBMC_SCAN_METHODS = {'peliculas': 'VideoLibrary.Scan',
                     'series': 'VideoLibrary.Scan',
                     'musica': 'AudioLibrary.Scan'}

env.host_string = XBMC_HOST
env.user = "pi"

# app.config.update(
#     CELERY_BROKER_URL='amqp://guest@localhost:5672//',
#     CELERY_RESULT_BACKEND='amqp://guest@localhost:5672//',
# )
# celery = make_celery(app)

import transmissionrpc
client = transmissionrpc.Client(address='localhost', user='pi', password='pi')


# controllers
@app.route("/")
def index():
    return render_template('index.html')


@app.route("/downloads")
def downloads():
    """
    Download list for classify
    """
    try:
        #downloads_list = [file.encode('ascii', 'ignore') for file in run("ls -1 %s" % HDD_PATH + DOWNLOADS_PATH).split('\r\n')]
        #downloads_list = [elem.encode('ascii', 'ignore') for elem in os.listdir('/media/elements/Descargas/')]
        #downloads_list = os.listdir('/media/elements/Descargas/')
        downloads_list = [torrent for torrent in client.get_torrents() if torrent.progress == 100.0 and torrent.downloadDir == '/media/elements/Descargas']
    except OSError as e:
        flash(u'No es posible acceder al directorio de descargas. ¿está HDD montado? {}'.format(e))
        downloads_list = []
    except BaseException as e:
        flash(u'Error desconocido: {} {}'.format(type(e), e.message))
        downloads_list = []

    return render_template('downloads.html', downloads=downloads_list)


@app.route("/classify/<id>/<category>")
def classify(id, category):
    """
    Classify downloaded element
    """
    torrent = client.get_torrent(id)

    try:
        if category == 'eliminar':
            pass
            #_remove(name)
        elif category == 'series':
            destination_path = _get_serie_destination_path(id, category)
            _move_to_destination(torrent, category, destination_path)
        else:
            destination_path = DESTINATION_CATEGORIES_PATHS[category]
            _move_to_destination(torrent, category, destination_path)
    except BaseException as e:
        flash(u'Error desconocido: {} {}. category: {}'.format(type(e), e.message, category))

    return redirect(url_for('downloads'))


def _remove(name):
    try:
        origin = os.path.normpath(HDD_PATH + '/' + DOWNLOADS_PATH + '/' + name)
        run('rm -r "%s"' % origin)
    except BaseException as e:
        flash(u'Error mientras se eliminaba "{name}": {error}'.format(name=name, error=e.strerror))
    else:
        flash(u'"{name}" eliminado correctamente'.format(name=name))


def _get_serie_destination_path(name, category):
    # si se detecta el patron de una serie en el nombre se modifica el directorio destino
    destination_serie = ''
    #series_names = run("ls -1 %s" % HDD_PATH + '/' + DESTINATION_CATEGORIES_PATHS[category]).split('\r\n')
    series_names = os.listdir(os.path.normpath(HDD_PATH + '/' + DESTINATION_CATEGORIES_PATHS[category]))
    for serie_name in series_names:
        if serie_name.lower().replace(' ', '') in re.sub('[._\- ]', '', name.lower()):
            destination_serie = '/' + serie_name
    destination_path = DESTINATION_CATEGORIES_PATHS[category] + destination_serie
    return destination_path


def _move_to_destination(torrent, category, destination_path):
    try:
        # mover a directorio destino
        origin = os.path.normpath(HDD_PATH + '/' + DOWNLOADS_PATH + '/' + torrent.name)
        destination = os.path.normpath(HDD_PATH + '/' + destination_path + '/' + torrent.name)
        
        torrent.move_data(destination)
        #run('mv "%s" "%s"' % (origin, destination))
    except BaseException as e:
        flash(u'Error mientras se movía "{name}" a "{category}": {error}'.format(name=torrent.name,
                                                                                 category=category,
                                                                                 error=e.strerror))
    else:
        # call XBMC to update collection
        #xbmc_jsonrpc = 'jsonrpc?request={"jsonrpc": "2.0", "method": "%s"}' % XBMC_SCAN_METHODS[category]
        #requests.get('http://{host}:{port}/{url}'.format(host=XBMC_HOST, port=XBMC_PORT, url=xbmc_jsonrpc), auth=(XBMC_USER, XBMC_PASSWD))

        flash(u'"{name}" movido correctamente a "{category} ({destination})"'.format(name=torrent.name,
                                                                                     category=category,
                                                                                     destination=destination_path))


@app.route("/run-sentinel")
def run_sentinel():
    execfile('%s/scripts/transmission_sentinel.py' % PROJECT_ROOT)

    return redirect(url_for('index'))


@app.route("/git-hook")
def git_hook():
    repository = git.cmd.Git(PROJECT_ROOT)
    pull_response = repository.pull()
    flash(pull_response)
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host='0.0.0.0')
