# -*- coding: utf-8 -*-
import logging
import os
import sys

import pytest

logger = logging.getLogger("web2py.test")
logger.setLevel(logging.DEBUG)

# allow imports from modules and site-packages
dirs = os.path.split(__file__)[0]
_appname = dirs.split(os.path.sep)[-1]
app_directory = os.path.join('/', *dirs.split(os.path.sep))
modules_path = 'modules'  #os.path.join('applications', appname, 'modules')
if modules_path not in sys.path:
    sys.path.append(modules_path)  # imports from app modules folder
if '../../site-packages' not in sys.path:
    sys.path.append('../../site-packages')  # imports from site-packages


@pytest.fixture(scope='session')
def appname():
    '''Discover application name.

    This conftest file must be in your application directory
    '''
    return _appname


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
    path = os.path.realpath(config.option.gae_sdk_path)
    gae = config.option.gae
    if gae:
        if path not in sys.path:
            sys.path.insert(0, path)
        import dev_appserver
        dev_appserver.fix_sys_path()  # add paths to libs specified in app.yaml, etc
        mute_noisy_tasklets()


def pytest_addoption(parser):
    parser.addoption('--url', action='store',
                     help="Web server URL", default='http://localhost:8000')
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
