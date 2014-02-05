# -*- coding: utf-8 -*-

import transmissionrpc
import shutil
import smtplib  
import os.path
import sys
from fabric.api import env
from fabric.operations import run, put
import traceback

from credentials import *

server = smtplib.SMTP('smtp.gmail.com:587')  
server.starttls()  
server.login(mail_username, mail_password)  

client = transmissionrpc.Client(address=transmission_host, user=transmission_username, password=transmission_password)

def scp_torrent(torrent):
    src_path = os.path.normpath(torrent.downloadDir + '/' + torrent.name)
    dst_path = os.path.normpath(u"/media/STOREX/Descargas/")

    env.host_string = 'xbmc'
    try:
        res = put(src_path, dst_path, use_glob=False)
        if res.failed:
            raise Exception
    except:
        msg = 'Subject: Transmission sentinel error\n\nError when trying move torrent finished: {name}\n\n{exception}\n\n{traceback}'.format(name=torrent.name, exception=sys.exc_info(), traceback=traceback.format_exc())
        server.sendmail(fromaddr, toaddrs, msg)
        return False

    return True

for torrent in client.get_torrents():
    if torrent.progress == 100.0 and torrent.status == 'seeding':

        torrent.stop()

        copied = scp_torrent(torrent)

        if copied:
            client.remove_torrent(torrent.id, delete_data=True)

            msg = u'Subject: Transmission sentinel notification\n\nTorrent finished: %s' % torrent.name
            server.sendmail(fromaddr, toaddrs, msg)
            

server.quit()  
