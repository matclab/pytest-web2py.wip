# -*- coding: utf-8 -*-
import pytest


@pytest.fixture
def email():
    return 'homer@web2py.com'


@pytest.fixture
def register(b, email):
    b.go('/')
    reglink = b.xpath("//a[contains(text(), 'Sign Up') and contains(@class, 'btn')]/@href")[0]
    b.go(reglink)
    data = dict(first_name='Homer',
                last_name='Simpson',
                email=email,
                password='test',
                password_two='test',
                language='en-us')
    b.fill_form(data)
    b.find_by_value("Sign Up").last.click()
    hamburger_button = b.find_by_css("button.navbar-toggle")
    if hamburger_button and hamburger_button.last.visible:
        hamburger_button.last.click()
    assert b.is_visible_by_text('Welcome Homer', 4)

