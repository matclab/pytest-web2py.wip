# -*- coding: utf-8 -*-
import logging
import sys
import os.path
import time

import pytest
import subprocess
from bs4 import BeautifulSoup

from gluon.contrib.webclient import WebClient


logger = logging.getLogger("web2py.test")
logger.addHandler(logging.NullHandler())
logger.setLevel(logging.DEBUG)

@pytest.fixture(scope='session', autouse=True)
def webserver(request, w2pdir, url):
    web2py_exec = os.path.join(w2pdir, 'web2py.py')
    proc = subprocess.Popen([sys.executable, web2py_exec, '-a', 'testpass'],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    logger.info('Waiting for web2py to start')
    for a in range(1, 11):
        time.sleep(1)
        try:
            c = WebClient(url)
            c.get('/')
            break
        except:
            continue

    def fin():
        logger.info('Killing web2py server')
        proc.terminate()
        (out, err) = proc.communicate()
        logger.debug("Web2py stdout :\n%s" % out)
        logger.debug("Web2py stderr :\n%s" % err)

    request.addfinalizer(fin)



def _client(url, request):
    """
        Return a WebClient for given url, with added BeautifulSoup dom property
    """
    client = WebClient(url, postbacks=True)
    def dom(self):
        return BeautifulSoup(client.text, "lxml")

    WebClient.dom = property(dom)

    return client

@pytest.fixture
def client(url, request):
    logger.debug("-- client")
    return _client(url, request)

@pytest.fixture(scope='module')
def module_client(url, request):
    logger.debug("-- module_client")
    return _client(url, request)

@pytest.fixture(autouse=True)
def emptydb(client, appname):
    logger.debug("-- emptydb")
    try:
        client.get('/%s/tests/empty_db' % appname)
    except:
        logger.warn('No "tests" controller in %s application' % appname)
