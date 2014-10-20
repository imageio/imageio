
import os
import sys
import inspect

import pytest
from _pytest import runner
runner.pytest_runtest_call_orig = runner.pytest_runtest_call

# Get root dir
THIS_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = THIS_DIR
for i in range(9):
    ROOT_DIR = os.path.dirname(ROOT_DIR)
    if os.path.isfile(os.path.join(ROOT_DIR, '.gitignore')):
        break


def pytest_runtest_call(item):
    """ Variant of pytest_runtest_call() that stores traceback info for
    postmortem debugging.
    """
    try:
        runner.pytest_runtest_call_orig(item)
    except Exception:
        type, value, tb = sys.exc_info()
        tb = tb.tb_next  # Skip *this* frame
        sys.last_type = type
        sys.last_value = value
        sys.last_traceback = tb
        del tb  # Get rid of it in this namespace
        raise

# Monkey-patch pytest
runner.pytest_runtest_call = pytest_runtest_call


def run_tests_if_main():
    """ Run tests in a given file if it is run as a script
    """
    local_vars = inspect.currentframe().f_back.f_locals
    if not local_vars.get('__name__', '') == '__main__':
        return
    # we are in a "__main__"
    fname = local_vars['__file__']
    pytest.main('-v -x --color=yes %s' % fname)


def test_unit():
    """ Run all unit tests
    """
    orig_dir = os.getcwd()
    os.chdir(ROOT_DIR)
    try:
        pytest.main('-v tests')
    finally:
        os.chdir(orig_dir)


def test_style():
    """ Test style using flake8
    """
    orig_dir = os.getcwd()
    orig_argv = sys.argv
    
    os.chdir(ROOT_DIR)
    sys.argv[1:] = ['imageio', 'make']
    sys.argv.append('--ignore=E226,E241,E265,W291,W293')
    sys.argv.append('--exclude=six.py,py24_ordereddict.py')
    try:
        from flake8.main import main
    except ImportError:
        print('Skipping flake8 test, flake8 not installed')
    else:
        print('Running flake8... ')  # if end='', first error gets ugly
        sys.stdout.flush()
        try:
            main()
        except SystemExit as ex:
            if ex.code in (None, 0):
                pass  # do not exit yet, we want to print a success msg
            else:
                raise RuntimeError('flake8 failed')
    finally:
        os.chdir(orig_dir)
        sys.argv[:] = orig_argv
