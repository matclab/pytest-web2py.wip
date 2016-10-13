# -*- coding: utf-8 -*-
import pytest
import time
from helper import register, email

def dump_html(b, n=''):
    with open('/tmp/test%s.html'%n, 'w') as f:
        f.write(b.html.encode('utf8'))

def test_standard_content(b):
    b.go('/')
    assert set(b.xpath("//a[contains(text(), 'Log In')]/@href")) == set(["#", "/user_/login"])
    assert set(b.xpath("//a[contains(text(), 'Sign Up')]/@href")) == set(["/user_/register"])
    assert set(b.xpath("//a[contains(text(), 'Lost password')]/@href")) == set(["/user_/request_reset_password"])


def test_register(b, register):

    # log out and  log in again
    logoutlink = b.xpath("//a[contains(text(), 'Log Out')]/@href")[0]
    b.go(logoutlink)

    b.find_link_by_text("Log In").last.click()

    data = dict(email='homer@web2py.com', password='test')
    b.fill_form(data)
    b.find_by_value("Log In").first.click()

    # check registration and login were successful
    b.go('/')
    hamburger_button = b.find_by_css("button.navbar-toggle")
    if hamburger_button and hamburger_button.last.visible:
        hamburger_button.last.click()
    assert b.is_visible_by_text('Welcome Homer')


