# -*- coding: utf-8 -*-
import logging
import os
import sys

import pytest

logger = logging.getLogger("web2py.test")
logger.setLevel(logging.DEBUG)

from w2p_unit import *

def _appdir():
    w2pdir = os.path.abspath(config.option.w2p_dir)
    appname = config.option.w2p_app
    return os.path.normpath(os.path.join('/', [w2pdir, 'applications',
                                               appname]))

@pytest.fixture(scope='session')
def appdir():
    return _appdir()

@pytest.fixture(scope='session')
def appname(request):
    return request.config.option.w2p_app


@pytest.fixture(scope='session')
def url(request):
    return request.config.option.url.rstrip('/')


@pytest.fixture(scope='session')
def gae_sdk_path(request):
    path = os.path.realpath(request.config.option.gae_sdk_path)


@pytest.fixture(scope='session')
def gae(request):
    return request.config.option.gae


@pytest.fixture(scope='session', autouse=True)
def create_testfile_to_application(request, appname):
    '''Creates a temp file to tell application she's running under a
    test environment.

    Usually you will want to create your database in memory to speed up
    your tests and not change your development database.

    '''

    logger.debug("-- create_testfile_to_application")
    import web2pytest
    web2pytest.create_testfile(appname)

    request.addfinalizer(web2pytest.delete_testfile)



def pytest_configure(config):
    # allow imports from modules and site-packages
    app_directory = _appdir()
    modules_path = os.path.normpath(os.path.join(app_directory, 'modules'))
    if modules_path not in sys.path:
        sys.path.insert(0, modules_path)  # imports from app modules folder
    site_path = os.path.normpath(os.path.join(w2pdir, 'site-packages'))
    if site_path not in sys.path:
        sys.path.append(site_path)  # imports from site-packages

    w2pdir = os.path.abspath(config.option.w2p_dir)
    sys.path.insert(0, w2pdir)

    # Configure paths for gae
    if config.option.gae:
        path = os.path.realpath(config.option.gae_sdk_path)
        if path not in sys.path:
            sys.path.insert(0, path)
        import dev_appserver
        dev_appserver.fix_sys_path()  # add paths to libs specified in app.yaml, etc
        mute_noisy_tasklets()

    # activate autouse fixtures
    if config.option.w2p_test == 'unit':
        pass # TODO
    elif config.option.w2p_test == 'web':
        pass # TODO
    elif config.option.w2p_test == 'ui':
        pass # TODO
    else:
        logger.error("Unknown valur '%s' for option --w2p-test" %
                     config.option.w2p_test)





def pytest_addoption(parser):
    dirs = os.path.split(__file__)[0]
    appname = dirs.split(os.path.sep)[-1]
    parser.addoption('--w2p-root', action='store',
                     help="web2py root path", default='../..')
    parser.addoption('--w2p-app', action='store',
                     help="web2py application name", default=appname)
    parser.addoption('--w2p-url', action='store',
                     help="Web2py server URL", default='http://localhost:8000')
    parser.addoption('--w2p-test', choices=['unit', 'web', 'ui'], default='unit',
                     help="Type of testing wanted")
    parser.addoption('--gae', action='store_true', default=False,
                     help="Shall a GAE environment be setup for unit testing")
    parser.addoption('--gae-sdk-path', metavar='PATH',
                     help="path for the pyhon GAE SDK",
                     action='store',
                     default='/opt/google_appengine')


def mute_noisy_tasklets():
    from google.appengine.ext import ndb
    ndb.utils.DEBUG = False
    ndb.utils.__tracebackhide__ = True
    ndb.tasklets.__tracebackhide__ = True
    ndb.context.__tracebackhide__ = True
