# Pytest Plugin for Web2py

This repo is a work in progress for building a pytest plugin for web2py.

## State and Goal

For now, pytest works, but one shall put the conftest files in the
application directory.

The goal is to produce a fully independent pytest plugin.


## Usage

### Installation

Install requirements (preferably in a virtualenv):
```
pip install -r requirements.txt
```

### Application configuration
Equip your application with the needed interfaces:
- a specific database setup for tests,
- a *test* controller to help setup and teardown database before each test
  (necessary for *web* and *ui* tests, as we only have acess to the
  application by the http protocol),

#### DB setup
We may want to tweak the database setup to improve the speed of unit tests. A
typical setup in `models/db.py` may for example looks like :

```python
UNIT_TESTING = False
if request.TEST_APP == 'd2c84025-5e33-442d-db12-9da661250e2d':
   TESTING = True
   UNIT_TESTING = True
else:
   import os.path
   TESTING = os.path.exists("/dev/shm/web2py_test/welcome/web2py_test_indicator")
if TESTING:
   if UNIT_TESTING:
      # fast in memory SQL for unit test
      db = DAL('sqlite:memory:', lazy_tables=True
	       )  #
   else:
      db = DAL('sqlite://storage.sqlite'
	       , migrate_enabled=True
	       , lazy_tables=True)  # sqlite for minimal persistence
else:
   db = DAL(myconf.get('db.uri'),
	    pool_size=myconf.get('db.pool_size'),
	    migrate_enabled=myconf.get('db.migrate'),
	    check_reserved=['all'])
```

#### tests controller
A controller is needed, whose name is defined by the `test_controller`
fixture (default to `tests`), and shall contains a function `empty_db` which
may looks like:

```python
def empty_db():
   if TESTING:
      for t in db.tables:
	 db[t].truncate('CASCADE')
```


### Running tests
- unit tests
   ```sh
   py.test --w2p-app=welcome --w2p-root=tests/web2py tests/unit-tests
   ```
- webclient tests
   ```sh
   py.test --w2p-app=welcome --w2p-root=tests/web2py tests/web-tests/
   ```
- UI tests
  *TODO*

- all tests
  ```sh
  py.test --w2p-app=welcome --w2p-root=tests/web2py tests/
  ```


## Writing Tests

### Unit Tests
*TODO*
### Webclient Tests
*TODO*
### UI Tests (selenium)
*TODO*

## Thanks

Some code taken and inspiration taken from https://github.com/viniciusban/web2py.test


## Licence

To be defined, but probably something like MIT… 

## TODO

- make the API cleaner
- separate things in a clean independent pytest plugin (obiously with some
  more configuration w.r.t. web2py and applicatins paths),
- write tests for the pytest-plugin,
- document pytest usage,
- document test writing (with pitfalls of unittest, use of mocks, …),
- writing more web2py default tests,
- improve code quality (break long functions,…)
- …
