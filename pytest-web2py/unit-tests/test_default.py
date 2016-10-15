# -*- coding: utf-8 -*-

import logging
import logging.config
import os
import re

import pytest

import conftest as w2p

logging.config.fileConfig(os.path.join(w2p.app_directory, "logging.conf"))
logger = logging.getLogger("web2py.test")
logger.setLevel(logging.DEBUG)


@pytest.fixture()
def controller():
    return 'default'


def describe_register():
    # Note that we use pytest-describe plugin to collect tests

    def is_working_by_db(w, fr, register_and_login):
        assert w.session.auth and w.auth.is_logged_in()
        assert w.recaptcha._validate.call_count == 1

    @pytest.mark.parametrize('gae_probability', [1])
    def is_working_by_api(w, fr, user_data):
        assert not w.session.auth and not w.auth.is_logged_in()
        w2p.form_post(w, 'user/register', user_data,
                      redirect_controller='default', redirect_url='index')
        assert w.session.flash == 'Logged in'

    @pytest.mark.parametrize('register_verification', [True])
    def login_fail_until_registration_verified(w, fr, register_and_login, gae,
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

    @pytest.mark.parametrize('register_verification', [True])
    def check_email_content(w, fr, register_and_login, user_data, gae):
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

    @pytest.mark.parametrize('recaptcha_validate', [False])
    def recaptcha_fail(w, fr, user_data):
        w2p.form_post(w, 'user/register', user_data)
        assert not w.session.auth and not w.auth.is_logged_in()
        assert w.recaptcha._validate.call_count == 1

    @pytest.mark.parametrize('password_two', ['erroneous'])
    def fail_when_erroneous_second_password(w, fr, user_data):
        r = w2p.form_post(w, 'user/register', user_data)
        assert r['form'].errors.password_two == "Password fields don't match"
        assert not w.session.auth


def describe_login():

    def ok_after_register(w, fr, user_data):
        assert not w.session.auth and not w.auth.is_logged_in()
        w2p.form_post(w, 'user/register', user_data,
                      redirect_controller='default', redirect_url='index')
        assert w.auth.is_logged_in()
        assert w.session.auth.user.last_name == user_data['last_name']
        assert w.session.auth.user.first_name == user_data['first_name']
        assert w.session.auth.user.email == user_data['email']

    def fail_if_bad_user(w, fr, register_and_login, logout, user_data):
        assert not w.session.auth
        user_data.update(email="a@b.com")
        w2p.form_post(w, 'user/login', user_data, redirect_url='user/login',
                      redirect_controller='user')
        assert not w.session.auth
        assert w.session.flash == 'Invalid login'

    def fail_if_bad_password(w, fr, register_and_login, logout, user_data):
        assert not w.session.auth
        user_data.update(password="blob")
        w2p.form_post(w, 'user/login', user_data, redirect_url='user/login',
                      redirect_controller='user')
        assert not w.session.auth
        assert w.session.flash == 'Invalid login'


def describe_index():
    def index_does_display(w, fr, db, controller):
        html = w2p.call(w, 'index', controller=controller, render=True).html
        assert '>Home</a>' in html
        assert 'button">Sign Up</a>' in html
        assert 'button">Log In</a>' in html

    def index_does_display_when_logged(w, fr, db, controller,
                                       register_and_login):
        html = w2p.call(w, 'index', controller=controller, render=True).html
        assert '>Home</a>' in html
        assert 'button">Sign Up</a>' not in html
        assert 'button">Log In</a>' not in html
