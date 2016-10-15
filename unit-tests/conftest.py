# -*- coding: utf-8 -*-
'''
py.test configuration and fixtures file.

This file is lightly adapted from the one by viniciusban;
Part of the web2py.test model app (https://github.com/viniciusban/web2py.test)

This file
- Tells application it's running in a test environment.
- Creates a complete web2py environment, similar to web2py shell.
- Creates a WebClient instance to browse your application, similar to a real
web browser.
- Propagates some application data to test cases via fixtures, like baseurl
and automatic appname discovery.

To write to db in test:

web2py.db.table.insert(**data)
web2py.db.commit()

To run tests:

cd web2py (you must be in the application root directory to run tests)
python web2py.py -a my_password --nogui &
py.test -x [-l] [-q|-v] -s unit-tests

'''

import logging
import os
import sys
from copy import copy

import hypothesis.strategies as st
import pytest
from faker import Factory
from hypothesis import find
from hypothesis.extra.fakefactory import fake_factory

logger = logging.getLogger("web2py.test")
logger.setLevel(logging.DEBUG)

fake = Factory.create()

# allow imports from modules and site-packages
dirs = os.path.split(__file__)[0]
appname = dirs.split(os.path.sep)[-2]
app_directory = os.path.join('/', *dirs.split(os.path.sep)[:-1])
sys.path.insert(0, os.path.join(app_directory, 'modules'))
sys.path.insert(0, '../..')



@pytest.fixture
def is_https():
    return True


@pytest.fixture
def appdir():
    return app_directory





@pytest.fixture()
def prepare_db(w):
    """ May be overwritte in tests to prepare the DB specifically after DB clean
    up """
    def _prepare_db():
        pass

    return _prepare_db


@pytest.fixture(autouse=True)
def fixture_cleanup_db(db, do_not_clean, prepare_db):
    '''Truncate all database tables except do_not_clean one before every single
    test case.

    This can really slow down your tests. So, keep your test data small and try
    to allocate your database in memory.

    Automatically called by test.py due to decorator.
    '''
    logger.debug("—— fixture_cleanup_db")

    for tab in db.tables:
        if tab not in do_not_clean:
            db[tab].truncate("CASCADE")
    prepare_db()
    db.commit()


@pytest.fixture()
def gae_probability():
    """ probability for consistency of datastore
    0 ensure that application will be functionnal on GAE, even in case of
    inconsistency
    """
    return 0


@pytest.fixture
def recaptcha_validate():
    """ The response of the mock captcha when asked to validate"""
    return True


@pytest.fixture
def register_verification():
    return False


@pytest.fixture
def password_change_verification():
    return False


@pytest.fixture
def gaebed(gae, gae_sdk_path, gae_probability, mocker):
    """ Prepare GAE testbed environment if necessary """
    if gae:
        if gae_sdk_path not in sys.path:
            sys.path.insert(0, gae_sdk_path)
        try:
            import appengine_config
        except ImportError:
            pass

        mocker.patch('google.appengine.api.mail.send_mail', autospec=True)
        APP_ID = 'GAE.APP.ID'
        os.environ['APPLICATION_ID'] = APP_ID
        from google.appengine.api import apiproxy_stub_map, datastore_file_stub
        from google.appengine.datastore import datastore_stub_util
        from google.appengine.api.memcache import memcache_stub
        from google.appengine.api import urlfetch_stub

        policy = datastore_stub_util.PseudoRandomHRConsistencyPolicy(
            probability=gae_probability)
        apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()
        stub = datastore_file_stub.DatastoreFileStub(APP_ID,
                                                     datastore_file=None,
                                                     consistency_policy=policy)
        apiproxy_stub_map.apiproxy.RegisterStub('datastore_v3', stub)
        apiproxy_stub_map.apiproxy.RegisterStub(
            'memcache', memcache_stub.MemcacheServiceStub())
        apiproxy_stub_map.apiproxy.RegisterStub('urlfetch',
                                                urlfetch_stub.URLFetchServiceStub())

        import google.appengine.tools.os_compat
        from google.appengine.ext import testbed
        from google.appengine.api import memcache
        from google.appengine.ext import ndb
        bed = testbed.Testbed()
        bed.activate()
        bed.init_datastore_v3_stub()
        bed.init_taskqueue_stub(True)
        bed.init_memcache_stub()
        bed.init_user_stub()
        bed.init_urlfetch_stub()
        bed.init_app_identity_stub(enable=True)
        ndb.get_context().clear_cache()
        from google.appengine.tools.devappserver2 import application_configuration
        # get the app id out of your app.yaml and stuff
        configuration = application_configuration.ApplicationConfiguration([
            '.'
        ])
        return bed
    else:
        return None


@pytest.fixture
def taskqueue_stub(gaebed, gae):
    if gae:
        from google.appengine.ext import testbed
        return gaebed.get_stub(testbed.TASKQUEUE_SERVICE_NAME)
    else:
        return None


@pytest.fixture
def w(appname, appdir, controller, request, gae, gaebed,
      mocker, recaptcha_validate, register_verification,
      password_change_verification, is_https):
    '''
    Create a Web2py environment similar to that achieved by Web2py shell.

    It allows you to use global Web2py objects like db, request, response,
    session, etc.

    Concerning tests, it is usually used to check if your database is an
    expected state, avoiding creating controllers and functions to help
    tests.
    '''
    logger.debug("—— w %s", {True: 'GAE', False: 'sqlite'}[gae])

    # We do not want to really send mail or ask for captcha while unit testing
    mocker.patch('smtplib.SMTP')
    mocker.patch('gluon.tools.Recaptcha2._validate',
                 autospec=True).return_value = recaptcha_validate

    from gluon.shell import env
    from gluon.settings import global_settings
    global_settings.web2py_runtime_gae = gae
    # can not be included before because need sys.path to be updated when GAE on use
    from gluon.globals import Storage, Request, Response, current

    web2py_env = env(
        appname,
        c=controller,
        import_models=True,
        dir=appdir,
        extra_request={'TEST_APP': 'd2c8e025-5e33-442d-ab12-97a361250e2d'})

    execfile(os.path.join(appdir, 'controllers', controller + '.py'),
             web2py_env)
    if 'auth' in web2py_env:
        web2py_env['auth'].settings.registration_requires_verification = register_verification
        web2py_env['auth'].settings.reset_password_requires_verification = password_change_verification

    def run(f, c=controller):
        """Injects request.controller and request.function into
        web2py environment.
        :type f: str
        :type c: str
        """
        from gluon.compileapp import run_controller_in
        from gluon.restricted import RestrictedError

        web2py_env['request'].controller = c
        web2py_env['request'].function = f
        web2py_env['request'].is_https = is_https
        r = None
        try:
            r = run_controller_in(c, f, web2py_env)
        except web2py_env['HTTP'] as e:
            if str(e.status).startswith("2") or str(e.status).startswith("3"):
                web2py_env['db'].commit()
            raise
        except RestrictedError as e:
            sys.stderr.write(e.traceback + '\n')
            raise e
        else:
            web2py_env['db'].commit()
        finally:
            web2py_env['db'].rollback()
        return r

    web2py_env['run'] = run

    if hasattr(web2py_env, '__file__'):
        del web2py_env['__file__']  # avoid py.test import error

    def fin():
        """ Close connection to allow openning another one later """
        if gae:
            gaebed.deactivate()
        else:
            web2py_env['db']._adapter.connection.close()

    request.addfinalizer(fin)

    return Storage(web2py_env)


@pytest.fixture()
def db(w):
    logger.debug("—— db")
    return w.db


@pytest.fixture()
def logout(w, register_controller):
    logger.debug("—— logout")
    call(w, '%/logout' % w.auth.controller or 'default',
         controller=register_controller, redirect_url=True,
         redirect_controller='default')
    assert not w.session.auth or w.session.auth.is_logged_in()


@pytest.fixture()
def and_logout(w, request):
    """ Fixture to logout at the end of test """

    def _logout():
        logout(w)

    request.addfinalizer(_logout)


def call(w, function_name,
         status=None,
         redirect_url=None,
         next=None,
         controller=None,
         redirect_controller=None,
         next_controller=None,
         render=False,
         view=None):
    """ Call controller function with the necessary request information.
        It expects `function` to raise a HTTP exception, or return a form, or
        return the dictionary returned by the controller function.

        The dictionnary is rendered with response.render except if render is set
        to None.

        If `render` is True,  the function returns a `Storage` with the fieds
        `response` and `html`, the first one being the the dictionary returned
        by the controller functions and the second one being the html as
        rendered.

        If `view` is None, the file used to render HTML id computed from
        controller and function. `view` mays also be a function accepting
        `w` as parameter. For example :
            ```
            call(w, f, render=True, view=lambda: w.response.view)
            ```


        If `redirect_url` url is defined, the call is expected to raise a
        redirection to this URL.
        If redirect_url is set to True, default redirection to `index` is
        expected.
        If `status` is defined it is checked against the redirection status.

        """
    #TODO update doc

    from gluon.globals import List
    args = function_name.split('/')
    function = args[0]
    w.request.function = function
    w.request.args = List(args[1:])
    logger.debug("args = %s", w.request.args)
    url = redirect_url
    controller = controller or w.request.controller
    redirect_controller = redirect_controller or controller

    if url:
        if url is True:
            url = '/%s/%s/index' % (w.request.application, redirect_controller or controller)
        elif not w.request.application in redirect_url:
            url = '/%s/%s/%s' % (w.request.application, redirect_controller or controller,
                                 redirect_url)
    else:
        url = ''

    if next:
        if next == True:
            url += '?_next=/%s/%s/%s' % (w.request.application,
                                           next_controller or controller,
                                           function)
            r = [url]
            r.extend(args[1:])
            url = '/'.join(r)
        else:
            url += '?_next=%s' % next

    try:
        logger.debug("→ Calling %s in %s", function_name, controller)
        from gluon.compileapp import run_controller_in
        resp = w.run(function, controller)
        logger.debug("Flash s:%s r:%s", w.session.flash, w.response.flash)
        assert url == '', ('Expected redirection to %s didn\'t occurred' % url)
        res = resp

        if render is not None:
            env = copy(w)
            env.update(resp)
            if not view:
                    view = '%s/%s.html' % (controller, function )
            elif callable(view):
                    view = view(w)
            logging.debug("Render with %s", view)
            html = w.response.render(view, env)
            if render:
                from gluon.globals import Storage
                res = Storage()
                res.response = resp
                res.html = html
        return res

    except w.HTTP as e:
        logger.debug("Flash s:%s r:%s", w.session.flash, w.response.flash)
        logger.debug("Exception: %s", e)
        if url:
            status = status or 303
        location = e.headers.get('Location', None) \
            or e.headers.get('web2py-redirect-location', None)\
            or e.headers.get('web2py-component-command', None) or None
        if location != url:
            logger.debug("redirect to: %s\nUser '%s'. Logged:%s", location,
                         w.auth.user, w.auth.is_logged_in())
        assert e.status == status, "status %s expected (%s found) for url '%s'" % (
            status, e.status, url
        )

        assert location == url, ("Wrong redirection url on %s() : %s "
                                 "(%s expected)" %
                                 (function, location, url or None))
        if not url:
            raise e
        else:
            return e


def form_post(w, function, data,
              args=None,
              status=None,
              redirect_url=None,
              next=None,
              crud_db=None,
              crud_record_id=None,
              controller=None,
              redirect_controller=None,
              next_controller=None,
              formname=None,
              formkey=None):
    """ Fill the form returned by `callable` with `data` dictionary and post it
    For crud form there are two supplementary parameters
    `crud_action` shall be one of the CRUD action ('create', 'read', 'update',…),
    `crud_record_id` if the id of the record concerned by the action if any.
    """
    logger.debug("→ form_post data: %s", data)
    if crud_db:
        _formname = "%s/%s" % (crud_db, crud_record_id)
    else:
        _formname = formname or function.split('/')[-1]

    _formkey = _formname
    hidden = dict(_formkey=_formname, _formname=_formname)
    logger.debug("formname: %s formkey: %s", _formname, _formkey)
    w.request.post_vars.clear()

    if data:
        w.request.post_vars.update(data)

    w.request.post_vars.update(hidden)

    for k in [k for k in w.session if "_formkey[" in k]:
        del w.session[k]

    w.session["_formkey[%s]" % _formname] = [_formkey]
    res = call(w, function,
               redirect_url=redirect_url,
               status=status,
               next=next,
               controller=controller,
               redirect_controller=redirect_controller,
               next_controller=next_controller)
    return res


def call_notlogged_check_redirect(w, function,
                                  redirect_url="default/login",
                                  status=303,
                                  controller=None,
                                  redirect_controller=None
                                  ):
    """
    Call controller function `callable` in the web2py environment `w` and
    ensure that the proper redirection for a non logged-in user is done.
    """
    return call(w, function, status, redirect_url=redirect_url,
                controller=controller,redirect_controller=redirect_controller,
                next=True)


@pytest.fixture()
def login(w, user_data):
    logger.debug("—— login")
    login_data = {k: user_data[k] for k in ['email', 'password']}
    form_post(w, 'user/login', login_data, redirect_controller='object',
                  controller=w.auth.controller, redirect_url='objects')
    assert w.auth.is_logged_in()
    assert w.session.auth.user.last_name == user_data['last_name']
    assert w.session.auth.user.first_name == user_data['first_name']
    assert w.session.auth.user.email == user_data['email']


@pytest.fixture()
def register_controller(w):
    return w.auth.settings.controller


@pytest.fixture()
def auth_user(register_and_login):
    logger.debug("—— auth_user")
    return register_and_login


@pytest.fixture()
def register_and_login(w, db, user_data, max_obj, end_date, register_controller):
    """ Register with `user_data` dict and ensure that user is logged in """
    logger.debug("—— register_and_login")
    form_post(w, 'user/register', user_data, redirect_url=True,
              controller=register_controller, redirect_controller='default')
    user_query = db((db.auth_user.first_name == user_data['first_name']) &
                    (db.auth_user.last_name == user_data['last_name']) &
                    (db.auth_user.email == user_data['email']))
    user_record = user_query.select().first()
    if user_record:
        db.auth_user.update_or_insert(db.auth_user.id == user_record.id,
                                       max_obj=max_obj,
                                       end_date=end_date)
        w.auth.user = db.auth_user(user_record.id)
        if w.session.auth:
            w.session.auth.user = w.auth.user
        logger.debug("registred user.id = %s", user_record.id)
    return w.auth.user


#### Configuration fixtures that may be overwritted in subsequent scenario or
##### parametrize for a test with something like
##### @pytest.mark.parametrize('email', ['homer@simpson.com'])


@pytest.fixture(scope='module')
def controller():
    return 'default'


@pytest.fixture()
def email():
    return "hs@example.com"


@pytest.fixture()
def first_name():
    return "Homer"


@pytest.fixture()
def last_name():
    return "Simpson"


@pytest.fixture()
def password():
    return "passblob"


@pytest.fixture()
def password_two(password):
    return password


@pytest.fixture('session')
def max_obj():
    return 5


@pytest.fixture()
def end_date():
    date = fake.date_time_between(start_date="+1d", end_date="+1y").date()
    logger.debug("—— end_date %s", date)
    return date


@pytest.fixture()
def user_data(email, first_name, last_name, password, password_two, end_date,
              max_obj):
    return {
        'email': email,
        'first_name': first_name,
        'last_name': last_name,
        'password': password,
        'password_two': password_two,
        'language': 'en-us',
    }


def pytest_configure(config):
    os.chdir('../..') # We want to be in web2py base repo
    if not config.option.gae:
        import gluon  # Needed for sqlite, but prevent web2py to connect to gae datastore testbed
