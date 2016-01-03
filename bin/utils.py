# -*- coding: utf-8 -*-

import requests
import logging


def do_request(server_url, name, data=None):
    files = None
    if 'photo' in data:
        files = {'photo': ('route.png', data['photo'], 'image/png')}
        del data['photo']
    r = requests.post('/'.join([server_url, name]), data=data, files=files)
    if r:
        logging.warning(r.text)
    return r.json() if r else None
