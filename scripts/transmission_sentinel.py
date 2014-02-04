# -*- coding: utf-8 -*-

import transmissionrpc
import shutil
import smtplib  
import os.path
import sys
from fabric.api import env
from fabric.operations import run, put

from credentials import *

server = smtplib.SMTP('smtp.gmail.com:587')  
server.starttls()  
server.login(mail_username, mail_password)  

client = transmissionrpc.Client(address=transmission_host, user=transmission_username, password=transmission_password)

def scp_torrent(torrent):
    src_path = os.path.normpath(unicode(torrent.downloadDir) + u'/' + unicode(torrent.name))
    dst_path = os.path.normpath(u"/media/STOREX/Descargas/")

    env.host_string = 'xbmc'
    try:
        res = put(src_path, dst_path)
        if res.failed:
            raise Exception
    except:
        msg = 'Subject: Transmission sentinel error\n\nError when trying move torrent finished: {name}\n\n{exception}'.format(name=torrent.name, exception=sys.exc_info()[0])
        server.sendmail(fromaddr, toaddrs, msg)
        return False

    return True

for torrent in client.get_torrents():
    if torrent.progress == 100.0:

        torrent.stop()

        copied = scp_torrent(torrent)

        if copied:
            client.remove_torrent(torrent.id, delete_data=True)

            msg = u'Subject: Transmission sentinel notification\n\nTorrent finished: %s' % torrent.name
            server.sendmail(fromaddr, toaddrs, msg)
            

server.quit()  
