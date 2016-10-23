# -*- coding: utf-8 -*-

import logging
import logging.config
import os
import re

import pytest

import pytest_web2py.unit.helper as w2p



logger = logging.getLogger("test_default")
logger.addHandler(logging.NullHandler())
logger.setLevel(logging.DEBUG)


@pytest.fixture()
def controller():
    return 'default'

@pytest.fixture()
def is_local():
    return True

def describe_register():
    # Note that we use pytest-describe plugin to collect tests


    def is_working_by_db(w, register_and_login):
        assert w.session.auth and w.auth.is_logged_in()

    @pytest.mark.parametrize('gae_probability', [1])
    def is_working_by_api(w, user_data):
        assert not w.session.auth and not w.auth.is_logged_in()
        w2p.form_post(w, 'user/register', user_data,
                      redirect_controller='default', redirect_url='index')
        assert w.session.flash == 'Logged in'

    @pytest.mark.skip("Do not work on welcome app, as no mailer is set up")
    @pytest.mark.parametrize('register_verification,is_local', [(True,False)])
    def login_fail_until_registration_verified(w, register_and_login, gae,
                                               user_data, appname, controller):
        assert w.session.flash == 'Email sent'

        login_data = {k: user_data[k] for k in ['email', 'password']}
        r = w2p.form_post(w, 'user/login', login_data)
        assert w.response.flash == 'Registration needs verification'

        # Get content of mail sent
        if gae and w.mail.settings.server[0] == 'gae':
            import google.appengine.api.mail
            assert google.appengine.api.mail.send_mail.call_count == 1
            mail = google.appengine.api.mail.send_mail.call_args[1]['body']
        else:
            import smtplib
            assert smtplib.SMTP.return_value.sendmail.call_count == 1
            mail = smtplib.SMTP.return_value.sendmail.call_args[0][2]
            mail = mail.replace('=\n', '')  # minimalist unencode
        url_re = re.compile('http://[^ ]*foundit/user/([^ ]*)')
        r = url_re.search(mail)
        assert r
        link = r.group(1)
        # Click on link to verify
        w2p.call(w, link, redirect_url='user/login', controller='user',
                 redirect_controller='user')
        assert w.session.flash == 'Email verified'

        # Login
        r = w2p.form_post(w, 'user/login', login_data,
                          redirect_controller='object', redirect_url='objects')
        assert w.session.auth and w.auth.is_logged_in()


    @pytest.mark.skip("Do not work on welcome app, as no mailer is set up")
    @pytest.mark.parametrize('register_verification', [True])
    def check_email_content(w, register_and_login, user_data, gae):
        if gae and w.mail.settings.server[0] == 'gae':
            import google.appengine.api.mail
            assert google.appengine.api.mail.send_mail.call_count == 1
            dest = google.appengine.api.mail.send_mail.call_args[1]['to']
            mail = google.appengine.api.mail.send_mail.call_args[1]['body']
            assert user_data['email'] in dest
        else:
            import smtplib
            assert smtplib.SMTP.return_value.sendmail.call_count == 1
            mail = smtplib.SMTP.return_value.sendmail.call_args[0][2]
            assert 'To: %s' % user_data['email'] in mail
        assert 'Click on the link http' in mail


    @pytest.mark.parametrize('password_two', ['erroneous'])
    def fail_when_erroneous_second_password(w, user_data):
        r = w2p.form_post(w, 'user/register', user_data)
        assert r['form'].errors.password_two == "Password fields don't match"
        assert not w.session.auth


def describe_login():

    def ok_after_register(w, user_data):
        assert not w.session.auth and not w.auth.is_logged_in()
        w2p.form_post(w, 'user/register', user_data,
                      redirect_controller='default', redirect_url='index')
        assert w.auth.is_logged_in()
        assert w.session.auth.user.last_name == user_data['last_name']
        assert w.session.auth.user.first_name == user_data['first_name']
        assert w.session.auth.user.email == user_data['email']

    def fail_if_bad_user(w, register_and_login, logout, user_data):
        assert not w.session.auth
        user_data.update(email="a@b.com")
        w2p.form_post(w, 'user/login', user_data, redirect_url='user/login',
                      redirect_controller='default')
        assert not w.session.auth
        assert w.session.flash == 'Invalid login'

    def fail_if_bad_password(w, register_and_login, logout, user_data):
        assert not w.session.auth
        user_data.update(password="blob")
        w2p.form_post(w, 'user/login', user_data, redirect_url='user/login',
                      redirect_controller='default')
        assert not w.session.auth
        assert w.session.flash == 'Invalid login'


def describe_index():
    def index_does_display(w, db, controller):
        html = w2p.call(w, 'index', controller=controller, render=True).html
        assert '>Home</a>' in html
        assert 'Sign Up' in html
        assert 'Log In' in html

    def index_does_display_when_logged(w, db, controller,
                                       register_and_login):
        html = w2p.call(w, 'index', controller=controller, render=True).html
        assert '>Home</a>' in html
        assert 'Sign Up' not in html
        assert 'Log In' not in html
