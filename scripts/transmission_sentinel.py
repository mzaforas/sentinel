# -*- coding: utf-8 -*-

import transmissionrpc
import shutil
import smtplib  
import os.path
import paramiko
import sys

from credentials import *

server = smtplib.SMTP('smtp.gmail.com:587')  
server.starttls()  
server.login(mail_username, mail_password)  

client = transmissionrpc.Client(address=transmission_host, user=transmission_username, password=transmission_password)

def scp_torrent(torrent):
    src_path = os.path.normpath(unicode(torrent.downloadDir) + u'/' + unicode(torrent.name))
    dst_path = os.path.normpath(u"/media/STOREX/Descargas/" + unicode(torrent.name))

    try:
        transport = paramiko.Transport(('xbmc', 22))
        rsa_key = paramiko.RSAKey.from_private_key_file('/home/pi/.ssh/id_rsa')
        transport.connect(username='pi', pkey=rsa_key)

        sftp = paramiko.SFTPClient.from_transport(transport)

        sftp.put(src_path, dst_path)
    except:
        msg = 'Subject: Transmission sentinel error\n\nError when trying move torrent finished: {name}\n\n{exception}'.format(name=torrent.name, exception=sys.exc_info()[0])
        server.sendmail(fromaddr, toaddrs, msg)
        return False
    else:
        sftp.close()
        transport.close()
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
