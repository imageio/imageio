""" Test imageio meta stuff, like namespaces and spuriuos imports
"""

from __future__ import print_function

import os
import sys
import subprocess

from pytest import raises  # noqa
from imageio.testing import run_tests_if_main

import imageio


def run_subprocess(command, return_code=False, **kwargs):
    """ Run command in subprocess and return stdout and stderr.
    Raise CalledProcessError if the process returned non-zero.
    """
    use_kwargs = dict(stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    use_kwargs.update(kwargs)
    
    p = subprocess.Popen(command, **use_kwargs)
    stdout, stderr = p.communicate()
    output = (stdout or b'').decode('utf-8'), (stderr or b'').decode('utf-8')
    if p.returncode:
        print(output[0], output[1])
        raise subprocess.CalledProcessError(p.returncode, command, output)
    return output


def loaded_modules(import_module, depth=None, all_modules=False):
    """ Import the given module in subprocess and return set of loaded modules

    Import a certain module in a clean subprocess and return the
    modules that are subsequently loaded. The given depth indicates the
    module level (i.e. depth=1 will only yield 'X.Y' but not 'X.Y.Z').
    """

    imageio_dir = os.path.dirname(os.path.dirname(
                                  os.path.abspath(imageio.__file__)))

    # Get the loaded modules in a clean interpreter
    code = "import sys, %s; print(', '.join(sys.modules))" % import_module
    res = run_subprocess([sys.executable, '-c', code], cwd=imageio_dir)[0]
    loaded_modules = [name.strip() for name in res.split(',')]
    
    # Filter by depth
    filtered_modules = set()
    if depth is None:
        filtered_modules = set(loaded_modules)
    else:
        for m in loaded_modules:
            parts = m.split('.')
            m = '.'.join(parts[:depth])
            filtered_modules.add(m)
    
    # Filter by imageio (or not)
    if all_modules:
        return filtered_modules
    else:
        imageio_modules = set()
        for m in filtered_modules:
            if m.startswith('imageio') and '__future__' not in m:
                imageio_modules.add(m)
        return imageio_modules


def test_namespace():
    """ Test that all names from the public API are in the main namespace """
    
    has_names = dir(imageio)
    has_names = set([n for n in has_names if not n.startswith('_')])
    
    need_names = ('help formats read save RETURN_BYTES '
                  'get_reader imread mimread volread mvolread '
                  'get_writer imwrite mimwrite volwrite mvolwrite '
                  'read save imsave mimsave volsave mvolsave '  # aliases
                  ).split(' ')
    need_names = set([n for n in need_names if n])
    
    # Check that all names are there
    assert need_names.issubset(has_names)
    
    # Check that there are no extra names
    extra_names = has_names.difference(need_names)
    extra_names.discard('testing')  # can be there during testing
    assert extra_names == set(['core', 'plugins', 'show_formats'])


def test_import_nothing():
    """ Not importing imageio should not import any imageio modules. """
    modnames = loaded_modules('os', 2)
    assert modnames == set()


def test_import_modules():
    """ Test that importing imageio does not import modules that should
    not be imported.
    """
    modnames = loaded_modules('imageio', 3)
    
    # Test if everything seems to be there
    assert 'imageio.core' in modnames
    assert 'imageio.plugins' in modnames
    assert 'imageio.plugins.ffmpeg' in modnames
    assert 'imageio.plugins.dicom' in modnames
    
    # Test that modules that should not be imported are indeed not imported
    assert 'imageio.freeze' not in modnames
    assert 'imageio.testing' not in modnames


def test_import_dependencies():
    """ Test that importing imageio is not dragging in anything other
    than the known dependencies.
    """
    
    # Get loaded modules when numpy is imported and when imageio is imported
    modnames_ref = loaded_modules('numpy', 1, True)
    modnames_new = loaded_modules('imageio', 1, True)
    
    # Get the difference; what do we import extra?
    extra_modules = modnames_new.difference(modnames_ref)

    known_modules = ['zipfile', 'importlib', 'logging', 'json', 'decimal',
                     'fractions', 'tempfile']  # discard these

    # Remove modules in standard library
    stdloc = os.path.dirname(os.__file__)
    print('os', stdloc)
    for modname in list(extra_modules):
        mod = sys.modules[modname]
        if modname.startswith('_') or modname in known_modules:
            extra_modules.discard(modname)
        elif not hasattr(mod, '__file__'):
            extra_modules.discard(modname)  # buildin module
        elif os.path.splitext(mod.__file__)[1] in ('.so', '.dylib', '.pyd'):
            extra_modules.discard(modname)  # buildin module
        elif os.path.dirname(mod.__file__) == stdloc:
            extra_modules.discard(modname)
        else:
            print(modname, mod.__file__)
    
    # Check that only imageio is left
    assert extra_modules == set(['imageio'])


run_tests_if_main()
