
import os
import sys
import inspect

import pytest
from _pytest import runner

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
if not runner.pytest_runtest_call.__module__.startswith('imageio'):
    runner.pytest_runtest_call_orig = runner.pytest_runtest_call
    runner.pytest_runtest_call = pytest_runtest_call


def run_tests_if_main(show_coverage=False):
    """ Run tests in a given file if it is run as a script
    
    Coverage is reported for running this single test. Set show_coverage to
    launch the report in the web browser.
    """
    local_vars = inspect.currentframe().f_back.f_locals
    if not local_vars.get('__name__', '') == '__main__':
        return
    # we are in a "__main__"
    os.chdir(ROOT_DIR)
    fname = local_vars['__file__']
    _clear_imageio()
    pytest.main('-v -x --color=yes --cov imageio --cov-report html %s' % fname)
    if show_coverage:
        import webbrowser
        fname = os.path.join(ROOT_DIR, 'htmlcov', 'index.html')
        webbrowser.open_new_tab(fname)


def test_unit(cov_report='term'):
    """ Run all unit tests
    """
    orig_dir = os.getcwd()
    os.chdir(ROOT_DIR)
    try:
        _clear_imageio()
        pytest.main('-v --cov imageio --cov-report %s tests' % cov_report)
    finally:
        os.chdir(orig_dir)


def _clear_imageio():
    # Remove ourselves from sys.modules to force an import
    for key in list(sys.modules.keys()):
        if key.startswith('imageio'):
            del sys.modules[key]


def __test_style():
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


def test_style():
    """ Test style using flake8
    """
    # Test if flake is there
    try:
        from flake8.main import main  # noqa
    except ImportError:
        print('Skipping flake8 test, flake8 not installed')
        return
    
    # Reporting
    print('Running flake8 ... ')
    sys.stdout = FileForTesting(sys.stdout)
    
    # Init
    ignores = ['E226', 'E241', 'E265', 'W291', 'W293']
    fail = False
    count = 0
    
    # Iterate over files
    for dir, dirnames, filenames in os.walk(ROOT_DIR):
        # Skip this dir?
        exclude_dirs = set(['.git', 'docs', 'build', 'dist', '__pycache__'])
        if exclude_dirs.intersection(dir.split(os.path.sep)):
            continue
        # Check all files ...
        for fname in filenames:
            if fname.endswith('.py'):
                # Get test options for this file
                filename = os.path.join(dir, fname)
                skip, extra_ignores = _get_style_test_options(filename)
                if skip:
                    continue
                # Test
                count += 1
                thisfail = _test_style(filename, ignores + extra_ignores)
                if thisfail:
                    fail = True
                    print('----')
                sys.stdout.flush()
    
    # Report result
    sys.stdout.revert()
    if fail:
        raise RuntimeError('    Arg! flake8 failed (checked %i files)' % count)
    else:
        print('    Hooray! flake8 passed (checked %i files)' % count)


class FileForTesting(object):
    """ Alternative to stdout that makes path relative to ROOT_DIR
    """
    def __init__(self, original):
        self._original = original
    
    def write(self, msg):
        if msg.startswith(ROOT_DIR):
            msg = os.path.relpath(msg, ROOT_DIR)
        self._original.write(msg)
        self._original.flush()
    
    def flush(self):
        self._original.flush()
    
    def revert(self):
        sys.stdout = self._original


def _get_style_test_options(filename):
    """ Returns (skip, ignores) for the specifies source file.
    """
    skip = False
    ignores = []
    text = open(filename, 'rb').read().decode('utf-8')
    # Iterate over lines
    for i, line in enumerate(text.splitlines()):
        if i > 20:
            break
        if line.startswith('# styletest:'):
            if 'skip' in line:
                skip = True
            elif 'ignore' in line:
                words = line.replace(',', ' ').split(' ')
                words = [w.strip() for w in words if w.strip()]
                words = [w for w in words if 
                         (w[1:].isnumeric() and w[0] in 'EWFCN')]
                ignores.extend(words)
    return skip, ignores


def _test_style(filename, ignore):
    """ Test style for a certain file.
    """
    if isinstance(ignore, (list, tuple)):
        ignore = ','.join(ignore)
    
    orig_dir = os.getcwd()
    orig_argv = sys.argv
    
    os.chdir(ROOT_DIR)
    sys.argv[1:] = [filename]
    sys.argv.append('--ignore=' + ignore)
    try:
        from flake8.main import main
        main()
    except SystemExit as ex:
        if ex.code in (None, 0):
            return False
        else:
            return True
    finally:
        os.chdir(orig_dir)
        sys.argv[:] = orig_argv
