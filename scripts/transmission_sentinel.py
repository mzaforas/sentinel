# -*- coding: utf-8 -*-

import transmissionrpc
import shutil
import smtplib  
import os.path
import paramiko

from credentials import *

server = smtplib.SMTP('smtp.gmail.com:587')  
server.starttls()  
server.login(mail_username, mail_password)  

client = transmissionrpc.Client(address=transmission_host, user=transmission_username, password=transmission_password)

def scp_torrent(torrent):
    msg = u'Subject: Transmission sentinel notification\n\nTorrent finished: %s' % torrent.name
    
    src_path = os.path.normpath(unicode(torrent.downloadDir) + u'/' + unicode(torrent.name))
    dst_path = os.path.normpath(u"/media/STOREX/Descargas/" + unicode(torrent.name))

    try:
        transport = paramiko.Transport(('xbmc', 22))
        rsa_key = paramiko.RSAKey.from_private_key_file('/home/pi/.ssh/id_rsa')
        transport.connect(username='pi', pkey=rsa_key)

        sftp = paramiko.SFTPClient.from_transport(transport)

        sftp.put(src_path, dst_path)
    except:
        msg = 'Subject: Transmission sentinel error\n\nError when trying move torrent finished: {name}'.format(name=torrent.name)
        server.sendmail(fromaddr, toaddrs, msg)

    sftp.close()
    transport.close()

for torrent in client.get_torrents():
    if torrent.progress == 100.0:

        torrent.stop()

        scp_torrent(torrent)

        client.remove_torrent(torrent.id, delete_data=True)
        server.sendmail(fromaddr, toaddrs, msg)
            

server.quit()  
