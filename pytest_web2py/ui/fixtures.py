# -*- coding: utf-8 -*-
import pytest
from lxml.html import fromstring
from splinter import Browser

browsers = ['phantomjs', 'chrome']  # 'firefox', 'zope.testbrowser', ]


def pytest_generate_tests(metafunc):
    """ Generate tests for one or all browsers """
    if metafunc.config.option.splinter_all:
        metafunc.parametrize("splinter_webdriver", browsers)
    else:
        opt = metafunc.config.option.splinter_webdriver
        metafunc.parametrize("splinter_webdriver", [opt])


@pytest.fixture(scope='session')
def splinter_window_size():
    return None


@pytest.fixture(scope='session')
def splinter_firefox_profile_preferences():
    return {'intl.accept_languages': 'en-us'}


@pytest.fixture(autouse=True)
def dumb(splinter_webdriver):
    """ Necessary to make visible usage of splinter_webdriver fixture """
    pass


@pytest.fixture()
def b(X, request, browser_instance_getter, url):
    browser = browser_instance_getter(request, b)
    return improve_browser(browser, url)


@pytest.fixture(scope='session')
def bs(X, request, browser_instance_getter, url):
    """Session scoped browser fixture."""

    browser = browser_instance_getter(request, b)
    return improve_browser(browser, url)


def improve_browser(browser, url):
    def lxml(self):
        return fromstring(self.html)

    def xpath(self, query):
        return self.lxml.xpath(query)

    def go(self, path):
        if path.startswith('/'):
            return self.visit('%s%s' % (url, path))
        else:
            return self.visit(path)

    def is_visible_by_text(self, text, wait=None, _class=None):
        if _class:
            classmatch = " and contains(concat(' ',normalize-space(@class),' '),' %s ')" % _class
        else:
            classmatch = ""
        return self.is_element_visible(
            self.find_by_xpath,
            "//*[contains(text(), \"%s\")%s]" % (text, classmatch),
            wait_time=wait)

    def is_not_visible_by_text(self, text, wait=None, _class=None):
        if _class:
            classmatch = " and contains(concat(' ',normalize-space(@class),' '),' %s ')" % _class
        else:
            classmatch = ""
        return self.is_element_not_visible(
            self.find_by_xpath,
            "//*[contains(text(), \"%s\")%s]" % (text, classmatch),
            wait_time=wait)

    browser.__class__.lxml = property(lxml)
    browser.__class__.xpath = xpath
    browser.__class__.go = go
    browser.__class__.is_visible_by_text = is_visible_by_text
    browser.__class__.is_not_visible_by_text = is_not_visible_by_text

    return browser


def pytest_addoption(parser):
    parser.addoption('--splinter-all', action='store_true', default=False)
    parser.addoption(
        '--headless',
        action='store_true',
        help="Run web client in headless mode (default)",
        default=True)
    parser.addoption('--no-headless', action='store_false', dest='headless')


@pytest.fixture(scope='session')
def X(request, splinter_window_size):
    """ setup the virtual X environment for headless clients"""
    if request.config.option.headless:
        from xvfbwrapper import Xvfb
        xvfb = Xvfb(
            # Commented out because of bug on chrome driver
            # width=splinter_window_size[0],
            # height=splinter_window_size[1]
        )
        xvfb.start()

        def fin():
            xvfb.stop()

        request.addfinalizer(fin)


@pytest.fixture(autouse=True)
def emptydb(b, url):
    b.go('/tests/empty_db')
