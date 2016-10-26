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
    return os.path.normpath(os.path.join(w2pdir, 'applications', appname))


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
    return request.config.option.w2p_url.rstrip('/')


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



def pytest_addoption(parser):
    # TODO : use own section for help
    dirs = os.path.split(__file__)[0]
    appname = dirs.split(os.path.sep)[-1]
    parser.addoption(
        '--w2p-root',
        action='store',
        help="web2py root path (%(default)s)",
        metavar='DIR',
        default=os.path.realpath('../..'))
    parser.addoption(
        '--w2p-app',
        action='store',
        metavar='STR',
        help="web2py application name (%(default)s)",
        default=appname)
    parser.addoption(
        '--w2p-url',
        metavar='URL',
        action='store',
        help="Web2py server URL (%(default)s)",
        default='http://localhost:8000')
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


def print_teardown_sections(self, rep):
    """ Monkey patched into TerminalReporter """
    for secname, content in rep.sections:
        if 'teardown' in secname:
            self._tw.sep('-', secname)
            if content[-1:] == "\n":
                content = content[:-1]
            self._tw.line(content)


def summary_failures_with_teardonw(self):
    """ To monkey patch TerminalReporter.summary_failure, in order to display
    teardown stdout and stderr sections """
    if self.config.option.tbstyle != "no":
        reports = self.getreports('failed')
        if not reports:
            return
        self.write_sep("=", "FAILURES")
        for rep in reports:
            if self.config.option.tbstyle == "line":
                line = self._getcrashline(rep)
                self.write_line(line)
            else:
                msg = self._getfailureheadline(rep)
                markup = {'red': True, 'bold': True}
                self.write_sep("_", msg, **markup)
                self._outrep_summary(rep)
                for report in self.getreports(''):
                    if report.nodeid == rep.nodeid and report.when == 'teardown':
                        #self._outrep_summary(report)
                        self.print_teardown_sections(report)


@pytest.hookimpl(tryfirst=True)
#@pytest.mark.hookwrapper
def pytest_terminal_summary(terminalreporter, exitstatus):
    terminalreporter.__class__.print_teardown_sections = print_teardown_sections
    terminalreporter.__class__.summary_failures = summary_failures_with_teardonw
    return


