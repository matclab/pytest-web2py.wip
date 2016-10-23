# -*- coding: utf-8 -*-
import logging
import os
import sys

import py
import pytest

import unit.fixtures
#import web
#import ui



def _appdir(config):
    w2pdir = os.path.abspath(config.option.w2p_root)
    appname = config.option.w2p_app
    return os.path.normpath(
        os.path.join(w2pdir, 'applications', appname))


@pytest.fixture(scope='session')
def appdir(request):
    return _appdir(request.config)


@pytest.fixture(scope='session')
def w2pdir(request):
    return request.config.option.w2p_root


@pytest.fixture(scope='session')
def w2pversion(w2pdir):
    try:
        version_info = open(os.path.join(w2pdir, 'VERSION'), 'r')
        raw_version_string = version_info.read().split()[-1].strip()
        version_info.close()
        return raw_version_string
    except:
      raise RuntimeError("Cannot determine web2py version")


@pytest.fixture(scope='session')
def appname(request):
    return request.config.option.w2p_app


@pytest.fixture(scope='session')
def url(request):
    return request.config.option.url.rstrip('/')


@pytest.fixture(scope='session')
def gae_sdk_path(request):
    return os.path.realpath(request.config.option.gae_sdk_path)


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

    import web2pytest
    web2pytest.create_testfile(appname)

    request.addfinalizer(web2pytest.delete_testfile)


def import_functions_from(package, module):
    """ Import all functions from the given package.module in the global scope

    >>> import_functions_from('unit', 'fixtures')
    >>> 'register_and_login' in globals()
    True
    """
    _tmp = __import__('%s.%s' % (package, module), globals(), locals(), [], -1)
    funcnames = [f for f,t in getattr(_tmp, module).__dict__.items()
                 if 'function' in str(type(t))]
    for f in funcnames:
        globals()[f] = getattr(_tmp, module).__dict__[f]

def pytest_configure(config):

    # allow imports from modules and site-packages
    w2pdir = os.path.abspath(config.option.w2p_root)
    config.option.w2p_root = w2pdir
    sys.path.insert(0, w2pdir)

    app_directory = _appdir(config)

    conffile = os.path.join(app_directory, "logging.conf")
    if os.path.isfile(conffile):
        logging.config.fileConfig()
    else:
        logging.basicConfig()
    logger = logging.getLogger("pytest_web2py")
    logger.addHandler(logging.NullHandler())
    logger.setLevel(logging.DEBUG)

    modules_path = os.path.normpath(os.path.join(app_directory, 'modules'))
    if modules_path not in sys.path:
        sys.path.insert(0, modules_path)  # imports from app modules folder
    site_path = os.path.normpath(os.path.join(app_directory, 'site-packages'))
    if site_path not in sys.path:
        sys.path.append(site_path)  # imports from site-packages


    # Configure paths for gae
    if config.option.gae:
        path = os.path.realpath(config.option.gae_sdk_path)
        if path not in sys.path:
            sys.path.insert(0, path)
        import dev_appserver
        dev_appserver.fix_sys_path(
        )  # add paths to libs specified in app.yaml, etc
        mute_noisy_tasklets()

    # activate autouse fixtures
    import_functions_from(config.option.w2p_test, 'fixtures')

    # Specific configuration
    if config.option.w2p_test == 'unit':
        os.chdir(config.option.w2p_root) # We want to be in web2py base repo
        if not config.option.gae:
            try:
                import gluon  # Needed for sqlite, but prevent web2py to connect to gae datastore testbed
            except ImportError:
                config.warn('WC1', "Unable to import gluon. Please set up --w2p-root.")


def pytest_addoption(parser):
    dirs = os.path.split(__file__)[0]
    appname = dirs.split(os.path.sep)[-1]
    parser.addoption(
        '--w2p-root', action='store', help="web2py root path (%(default)s)", metavar='DIR',
        default=os.path.realpath('../..'))
    parser.addoption(
        '--w2p-app',
        action='store',metavar='STR',
        help="web2py application name (%(default)s)",
        default=appname)
    parser.addoption(
        '--w2p-url',metavar='URL',
        action='store',
        help="Web2py server URL (%(default)s)",
        default='http://localhost:8000')
    parser.addoption(
        '--w2p-test',
        choices=['unit', 'web', 'ui'],
        default='unit',
        help="Type of testing wanted (%(default)s)")
    parser.addoption(
        '--gae',
        action='store_true',
        default=False,
        help="Shall a GAE environment be setup for unit testing")
    parser.addoption(
        '--gae-sdk-path',
        metavar='PATH',
        help="path for the pyhon GAE SDK (%(default)s)",
        action='store',
        default='/opt/google_appengine')


def mute_noisy_tasklets():
    from google.appengine.ext import ndb
    ndb.utils.DEBUG = False
    ndb.utils.__tracebackhide__ = True
    ndb.tasklets.__tracebackhide__ = True
    ndb.context.__tracebackhide__ = True
