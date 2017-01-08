import os
import sys
import webbrowser

from invoke import task

from ._config import ROOT_DIR


@task
def lint(ctx):
    """ alias for "invoke test --style"
    """
    from imageio import testing
    try:
        testing.test_style()
    except RuntimeError as err:
        print(str(err))
        sys.exit(1)


@task(optional=['unit', 'style'],
      help=dict(unit='run unit tests (pytest)',
                installed='like unit, but prefer using installed package, ' +
                          'and do not allow the use of internet.',
                style='run style tests (flake8)',
                cover='show test coverage'))
def test(ctx, unit=False, installed=False, style=False, cover=False):
    """ run tests (unit, style)
    """
    
    from imageio import testing
    
    if not (unit or installed or style or cover):
        sys.exit('Test task needs --unit, --style or --cover')
    
    if unit:
        sys.exit(testing.test_unit())
    
    if style:
        try:
            testing.test_style()
        except RuntimeError as err:
            print(str(err))
            sys.exit(1)
    
    if installed:
        for p in list(sys.path):
            if p in ('', '.'):
                sys.path.remove(p)
            elif p == ROOT_DIR or p == os.path.dirname(ROOT_DIR):
                sys.path.remove(p)
        os.environ['IMAGEIO_NO_INTERNET'] = '1'
        sys.exit(testing.test_unit())
    
    if cover:
        res = testing.test_unit(cov_report='html')
        if res:
            raise RuntimeError('Cannot show coverage, tests failed.')
        print('Launching browser.')
        fname = os.path.join(os.getcwd(), 'htmlcov', 'index.html')
        if not os.path.isfile(fname):
            raise IOError('Generated file not found: %s' % fname)
        webbrowser.open_new_tab(fname)
