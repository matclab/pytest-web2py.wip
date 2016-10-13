# Pytest Plugin for Web2py

This repo is a work in progress for building a pytest plugin for web2py.

## State and Goal

For now, pytest works, but one shall put the conftest files in the
application directory.

The goal is to produce a fully independent pytest plugin.


## Usage

Install requirements (preferably in a virtualenv):
```
pip install -r requirements.txt
```

For now, Copy all files in your web2py application directory, and run tests with one of
the following command:

```
py.test unit-tests
py.test --gae unit-tests

# Launch a web2py instance and then
py.test web-tests
py.test --splinter-all ui-tests
```

## Writing Tests

`TODO`

## Thanks

Some code taken and inspiration taken from https://github.com/viniciusban/web2py.test


## Licence

To be defined, but probably something like MIT… 
