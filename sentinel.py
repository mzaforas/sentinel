# -*- coding: utf-8 -*-

import sys
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

STOREX_PATH = '/media/STOREX'
DOWNLOADS_PATH = '/Descargas'
DESTINATION_CATEGORIES_PATHS = {'peliculas': 'Peliculas',
                                'series': 'Series',
                                'musica': 'Musica'}
XBMC_HOST = 'xbmc'
XBMC_PORT = '8080'
XBMC_USER = 'xbmc'
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
        downloads_list = run("ls -1 %s" % STOREX_PATH + DOWNLOADS_PATH).split('\r\n')
        if '' in downloads_list:
            downloads_list.remove('')
    except OSError:
        flash(u'No es posible acceder al directorio de descargas. ¿está STOREX montado?')
        downloads_list = []
    except Exception as e:
        flash(u'Error desconocido: {} {}'.format(type(e), e.message))
        downloads_list = []

    return render_template('downloads.html', downloads=downloads_list)


@app.route("/classify/<name>/<category>")
def classify(name, category):
    """
    Classify downloaded element
    """
    if category == 'eliminar':
        _remove(name)
    elif category == 'series':
        destination_path = _get_serie_destination_path(name, category)
        _move_to_destination(name, category, destination_path)
    else:
        destination_path = DESTINATION_CATEGORIES_PATHS[category]
        _move_to_destination(name, category, destination_path)

    return redirect(url_for('downloads'))


def _remove(name):
    try:
        origin = os.path.normpath(STOREX_PATH + '/' + DOWNLOADS_PATH + '/' + name)
        run('rm -r "%s"' % origin)
    except Exception as e:
        flash(u'Error mientras se eliminaba "{name}": {error}'.format(name=name, error=e.strerror))
    else:
        flash(u'"{name}" eliminado correctamente'.format(name=name))


def _get_serie_destination_path(name, category):
    # si se detecta el patron de una serie en el nombre se modifica el directorio destino
    destination_serie = ''
    series_names = run("ls -1 %s" % STOREX_PATH + '/' + DESTINATION_CATEGORIES_PATHS[category]).split('\r\n')
    for serie_name in series_names:
        if serie_name.lower().replace(' ', '') in re.sub('[._\- ]', '', name.lower()):
            destination_serie = '/' + serie_name
    destination_path = DESTINATION_CATEGORIES_PATHS[category] + destination_serie
    return destination_path


def _move_to_destination(name, category, destination_path):
    try:
        # mover a directorio destino
        origin = os.path.normpath(STOREX_PATH + '/' + DOWNLOADS_PATH + '/' + name)
        destination = os.path.normpath(STOREX_PATH + '/' + destination_path + '/' + name)
        run('mv "%s" "%s"' % (origin, destination))
    except Exception as e:
        flash(u'Error mientras se movía "{name}" a "{category}": {error}'.format(name=name, category=category, error=e.strerror))
    else:
        # call XBMC to update collection
        xbmc_jsonrpc = 'jsonrpc?request={"jsonrpc": "2.0", "method": "%s"}' % XBMC_SCAN_METHODS[category]
        requests.get('http://{host}:{port}/{url}'.format(host=XBMC_HOST, port=XBMC_PORT, url=xbmc_jsonrpc), auth=(XBMC_USER, XBMC_PASSWD))

        flash(u'"{name}" movido correctamente a "{category} ({destination})"'.format(name=name, category=category, destination=destination_path))


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
