#!/usr/bin/env python

"""Infrastructure to run an Web2py application under test environment.

We create a temporary file to indicate the application she's running
under test.

By default this file is created in ramdisk (/dev/shm) to speed up
execution.
"""

import glob
import os

#default_path = "/tmp"
default_path = "/dev/shm/web2py_test" # Ubuntu native ramdisk is faster
default_filename = "web2py_test_indicator"

_test_filename = None


def testfile_name(appname=None):
    global _test_filename
    if _test_filename:
        return _test_filename

    path = os.path.join(default_path, appname)
    _test_filename = os.path.join(path, default_filename)

    return _test_filename


def create_testfile(appname):
    """Creates a temp file to tell application she's running under a
    test environment.
    """

    fname = testfile_name(appname)

    try:
        # remove previous test data
        import shutil
        shutil.rmtree(os.path.dirname(fname))
    except OSError as e:
        pass

    try:
        os.makedirs(os.path.dirname(fname))
    except OSError as e:
        pass

    try:
        with open(fname, "w+") as f:
            f.write("web2py running in test mode.")
        return True
    except:
        return False


def delete_testfile():
    import shutil

    fname = testfile_name()
    shutil.rmtree(os.path.dirname(fname), ignore_errors=True)
    return True


