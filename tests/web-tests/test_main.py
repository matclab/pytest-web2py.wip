# -*- coding: utf-8 -*-
import logging

import pytest

from pytest_web2py.web import *

logger = logging.getLogger("web2py.test")
logger.addHandler(logging.NullHandler())
logger.setLevel(logging.DEBUG)


def dump_html(b, n=''):
    with open('/tmp/test%s.html' % n, 'w') as f:
        f.write(b.text)


def text_in_tag(tag, text, tagtype='a'):
    return tag.name == tagtype and tag.children and text in tag.children


def lost_password_in_a(tag):
    return text_in_tag(tag, " Lost password?")


def logout_in_a(tag):
    return text_in_tag(tag, " Log Out")


def debug(client):
    logger.debug("S:%s", client.sessions)
    logger.debug("C:%s", client.cookies)
    logger.debug("H:%s", client.headers)


def test_register(client):
    client.get('/')
    # register
    reglink = client.dom.find(text=" Sign Up").parent['href']
    assert reglink == '/welcome/default/user/register?_next=/welcome/default/index'
    logger.debug("GET register %s", reglink)
    client.get(reglink)
    assert 'Confirm Password' in client.text
    dump_html(client)
    data = dict(
        first_name='Homer',
        last_name='Simpson',
        email='homer@web2py.com',
        password='test',
        password_two='test',
        _formname='register')
    logger.debug("POST register")
    client.post(reglink, data=data)
    dump_html(client, 1)
    debug(client)
    assert ('Welcome Homer' in client.text)
    logoutlink = client.dom.find(logout_in_a)['href']
    assert logoutlink == '/welcome/default/user/logout?_next=/welcome/default/index'
    logger.debug("GET logout %s", logoutlink)
    client.get(logoutlink)
    loginlink = client.dom.find(text=" Log In").parent['href']
    debug(client)

    data = dict(email='homer@web2py.com', password='test', _formname='login')
    logger.debug("POST login %s", loginlink)
    client.post(loginlink, data=data)
    debug(client)

    # check registration and login were successful
    logger.debug("GET /")
    client.get('/')
    debug(client)
    assert ('Welcome Homer' in client.text)
