# -*- coding: utf-8 -*-

import logging
import os
import sys

import pytest

import helper

import faker

logger = logging.getLogger("pytest_web2py")
logger.addHandler(logging.NullHandler())
logger.setLevel(logging.DEBUG)


@pytest.fixture(autouse=True, scope='session')
def _0_configure_unit(appdir):
    modules_path = os.path.normpath(os.path.join(appdir, 'modules'))
    if modules_path not in sys.path:
        sys.path.insert(0, modules_path)  # imports from app modules folder
    site_path = os.path.normpath(os.path.join(appdir, 'site-packages'))
    if site_path not in sys.path:
        sys.path.append(site_path)  # imports from site-packages

    # Configure paths for gae
    if config.option.gae:
        path = os.path.realpath(config.option.gae_sdk_path)
        if path not in sys.path:
            sys.path.insert(0, path)
        import dev_appserver
        dev_appserver.fix_sys_path()  # add paths to libs specified in app.yaml, etc
        mute_noisy_tasklets()

    os.chdir(config.option.w2p_root)  # We want to be in web2py base repo
    if not config.option.gae:
        try:
            import gluon  # Needed for sqlite, but prevent web2py to connect to gae datastore testbed
        except ImportError:
            config.warn('WC1',
                        "Unable to import gluon. Please set up --w2p-root.")


@pytest.fixture(scope='session')
def fake():
    """ Return a fake factory to be use to create fake data :

    Example :
    fake.date_time_between(start_date="+1d", end_date="+1y").date()
    """
    return faker.Factory.create()


@pytest.fixture
def is_https():
    """ Used to set request.is_https """
    return True


@pytest.fixture
def is_local():
    """ Used to set request.is_local """
    return False


@pytest.fixture
def is_shell():
    """ Used to set request.is_shell """
    return False


@pytest.fixture
def is_scheduler():
    """ Used to set request.is_scheduler """
    return False


@pytest.fixture()
def prepare_db(w):
    """ May be overwritten in tests to prepare the DB specifically after DB clean
    up """

    def _prepare_db():
        pass

    return _prepare_db


@pytest.fixture()
def do_not_clean():
    """ list of table names that shall not be erased before every tests """
    return []


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
        APP_ID = 'lostre-test-1637'
        os.environ['APPLICATION_ID'] = APP_ID
        from google.appengine.api import apiproxy_stub_map, datastore_file_stub
        from google.appengine.datastore import datastore_stub_util
        from google.appengine.api.memcache import memcache_stub
        from google.appengine.api import urlfetch_stub

        policy = datastore_stub_util.PseudoRandomHRConsistencyPolicy(
            probability=gae_probability)
        apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()
        stub = datastore_file_stub.DatastoreFileStub(
            APP_ID, datastore_file=None, consistency_policy=policy)
        apiproxy_stub_map.apiproxy.RegisterStub('datastore_v3', stub)
        apiproxy_stub_map.apiproxy.RegisterStub(
            'memcache', memcache_stub.MemcacheServiceStub())
        apiproxy_stub_map.apiproxy.RegisterStub(
            'urlfetch', urlfetch_stub.URLFetchServiceStub())

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
        configuration = application_configuration.ApplicationConfiguration(
            ['.'])
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


@pytest.fixture()
def test_app_uuid():
    '''UUID passed as an extra request argument, used to identify on the app
    side that we are running in test mode.

    That UUID shall be overwritten and specific to your app.
    '''
    return 'd2c84025-5e33-442d-db12-9da661250e2d'


@pytest.fixture()
def w(web2py_env):
    '''A storageified web2py environment
    Be careful that modification to w shall not be shared with the initial
    environment. If you need to modify it afterway, better use the web2py_env
    dict '''
    from gluon.globals import Storage
    return Storage(web2py_env)


@pytest.fixture
def web2py_env(appname, appdir, controller, request, gae, gaebed, mocker,
               recaptcha_validate, register_verification,
               password_change_verification, is_https, is_local, is_shell,
               is_scheduler, w2pdir, w2pversion, language, test_app_uuid):
    '''
    Create a Web2py environment similar to that achieved by Web2py shell.

    It allows you to use global Web2py objects like db, request, response,
    session, etc.

    Concerning tests, it is usually used to check if your database is an
    expected state, avoiding creating controllers and functions to help
    tests.
    '''
    logger.debug("—— w db:%s", {True: 'GAE', False: 'sqlite'}[gae])

    # We do not want to really send mail or ask for captcha while unit testing
    mocker.patch('smtplib.SMTP')
    mocker.patch(
        'gluon.tools.Recaptcha2._validate',
        autospec=True).return_value = recaptcha_validate

    from gluon.shell import env
    from gluon.settings import global_settings
    _update_global_settings(global_settings, w2pversion, w2pdir, gae)
    # can not be included before because need sys.path to be updated when GAE on use
    from gluon.globals import Storage, Request, Response, current

    # create databases dir if needed
    dbdir = os.path.join(appdir, 'databases')
    if not gae and not os.path.isdir(dbdir):
        os.mkdir(dbdir)

    web2py_env = env(appname,
                     c=controller,
                     import_models=True,
                     dir=appdir,
                     extra_request=dict(
                         TEST_APP=test_app_uuid,
                         is_local=is_local,
                         is_https=is_https,
                         is_scheduler=is_scheduler,
                         is_shell=is_shell,
                         folder=appdir + os.sep))

    web2py_env['T'].force(language)
    execfile(
        os.path.join(appdir, 'controllers', controller + '.py'), web2py_env)
    if 'auth' in web2py_env:
        web2py_env[
            'auth'].settings.registration_requires_verification = register_verification
        web2py_env[
            'auth'].settings.reset_password_requires_verification = password_change_verification

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
    current.cache.ram.clear()
    current.cache.disk.clear()

    if hasattr(web2py_env, '__file__'):
        del web2py_env['__file__']  # avoid py.test import error

    def fin():
        """ Close connection to allow openning another one later """
        if gae:
            gaebed.deactivate()
        else:
            web2py_env['db']._adapter.connection.close()

    request.addfinalizer(fin)

    return web2py_env


def _update_global_settings(gs, w2pversion, w2pdir, gae):
    """ Update gs, in order to simulate the call of
    main.py """
    gs.web2py_runtime_gae = gae
    gs.web2py_version = w2pversion
    if not gs.local_hosts:
        gs.local_hosts = ['127.0.0.1', '::ffff:127.0.0.1', '::1']
    gs.applications_parent = w2pdir


@pytest.fixture()
def db(w):
    logger.debug("—— db")
    return w.db


@pytest.fixture()
def logout(w):
    logger.debug("—— logout")
    helper.call(
        w,
        '%s/logout' % w.auth.settings.function,
        controller=w.auth.settings.controller,
        redirect_url=True,
        redirect_controller='default')
    assert not w.session.auth or w.session.auth.is_logged_in()


@pytest.fixture()
def and_logout(w, request):
    """ Fixture to logout at the end of test """

    def _logout():
        logout(w)

    request.addfinalizer(_logout)


@pytest.fixture()
def login(w, user_data):
    logger.debug("—— login")
    login_data = {k: user_data[k] for k in ['email', 'password']}
    helper.form_post(
        w,
        '%s/login' % w.auth.settings.function,
        login_data,
        redirect_controller='object',
        controller=w.auth.settings.controller,
        redirect_url='objects')
    assert w.auth.is_logged_in()
    assert w.session.auth.user.last_name == user_data['last_name']
    assert w.session.auth.user.first_name == user_data['first_name']
    assert w.session.auth.user.email == user_data['email']


@pytest.fixture()
def auth_user(register_and_login):
    logger.debug("—— auth_user")
    return register_and_login


@pytest.fixture()
def register_and_login(w, db, user_data):
    """ Register with `user_data` dict and ensure that user is logged in """
    logger.debug("—— register_and_login")
    helper.form_post(
        w,
        'user/register',
        user_data,
        redirect_url=True,
        controller=w.auth.settings.controller,
        redirect_controller='default')
    user_query = db((db.auth_user.first_name == user_data['first_name']) & (
        db.auth_user.last_name == user_data['last_name']) & (
            db.auth_user.email == user_data['email']))
    user_record = user_query.select().first()
    if user_record:
        db.auth_user.update_or_insert(db.auth_user.id == user_record.id)
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


@pytest.fixture()
def language():
    return 'en-us'


@pytest.fixture()
def user_data(email, first_name, last_name, password, password_two, language):
    return {
        'email': email,
        'first_name': first_name,
        'last_name': last_name,
        'password': password,
        'password_two': password_two,
        'language': language,
    }
