# -*- coding: utf-8 -*-
import logging
import sys

import pytest
from bs4 import BeautifulSoup

from gluon.contrib.webclient import WebClient

sys.path.append('../..')

logger = logging.getLogger("web2py.test")
logger.setLevel(logging.DEBUG)


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
def emptydb(client):
    logger.debug("-- emptydb")
    client.get('/tests/empty_db')
