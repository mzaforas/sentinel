# -*- coding: utf-8 -*-

import transmissionrpc
import smtplib
import os.path
import sys
from fabric.api import env
from fabric.operations import run, put
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from credentials import *


def notify(msg):
    server = smtplib.SMTP('smtp.gmail.com:587')  
    server.starttls()  
    server.login(mail_username, mail_password)  

    email = MIMEMultipart('alternative')
    email['Subject'] = "Sentinel"
    email['From'] = fromaddr
    email['To'] = toaddrs
    text = MIMEText(msg, 'plain')
    html = MIMEText('<html><body>{}</body></html>'.format(msg), 'html')
    email.attach(text)
    email.attach(html)
    server.sendmail(fromaddr, toaddrs, email.as_string())
    server.quit()


def scp_torrent(torrent):
    src_path = os.path.normpath(torrent.downloadDir + '/' + torrent.name)
    dst_path = os.path.normpath(u"/media/elements/Descargas/")

    env.host_string = 'xbmc'
    try:
        res = put(src_path, dst_path, use_glob=False)
        if res.failed:
            raise ValueError(res.failed)
    except:
        msg = 'Subject: Transmission sentinel error\n\nError when trying move torrent finished: {name}\n\n{exception}\n\n{traceback}'.format(name=torrent.name, exception=sys.exc_info(), traceback=traceback.format_exc())
        notify(msg)
        return False

    return True

client = transmissionrpc.Client(address=transmission_host, user=transmission_username, password=transmission_password)

for torrent in client.get_torrents():
    if torrent.progress == 100.0 and torrent.status == 'seeding':
        torrent.stop()
        copied = scp_torrent(torrent)

        if copied:
            client.remove_torrent(torrent.id, delete_data=True)
            notify(u'Subject: Transmission sentinel notification\n\nTorrent finished: %s\n<a href="http://mzaforas.redirectme.net/sentinel/downloads">Classify it!</a>' % torrent.name)
            


