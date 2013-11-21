# -*- coding: utf-8 -*-

import transmissionrpc
import shutil
import smtplib  
import os.path

from credentials import *

server = smtplib.SMTP('smtp.gmail.com:587')  
server.starttls()  
server.login(mail_username, mail_password)  

client = transmissionrpc.Client(address=transmission_host, user=transmission_username, password=transmission_password)

for torrent in client.get_torrents():
    if torrent.progress == 100.0:
        msg = u'Subject: Transmission sentinel notification\n\nTorrent finished: %s' % torrent.name
        torrent.stop()

        src_path = os.path.normpath(unicode(torrent.downloadDir) + u'/' + unicode(torrent.name))
        dst_path = os.path.normpath(u"/media/STOREX/Descargas/" + unicode(torrent.name))

        try:
            if os.path.isdir(src_path):
                shutil.copytree(src_path, dst_path)
            else:
                shutil.copy(src_path, dst_path)
        except IOError as e:
            msg = 'Subject: Transmission sentinel error\n\nError when trying move torrent finished: {name}'.format(name=torrent.name)
            server.sendmail(fromaddr, toaddrs, msg)
            continue

        client.remove_torrent(torrent.id, delete_data=True)
        server.sendmail(fromaddr, toaddrs, msg)
            

server.quit()  
