# -*- coding: utf-8 -*-
import logging

logger = logging.getLogger("web2py.test")
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
    reglink = client.dom.find("a", class_="btn", text="Sign Up")['href']
    logger.debug("GET register %s", reglink)
    client.get(reglink)
    dump_html(client)
    data = dict(
        first_name='Homer',
        last_name='Simpson',
        email='homer@web2py.com',
        password='test',
        password_two='test',
        _formname='register',
        language='en-us')
    logger.debug("POST register")
    client.post(reglink, data=data)
    dump_html(client, 1)
    debug(client)
    logoutlink = '/user_/logout'
    logger.debug("GET logout %s", logoutlink)
    client.get(logoutlink)
    loginlink = client.dom.find("a", class_="btn", text="Log In")['href']
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
