# -*- coding: utf-8 -*-
# Copyright (c) 2014, Imageio team
# Distributed under the (new) BSD License. See LICENSE.txt for more info.

""" This subpackage provides the core functionality of imageio
(everything but the plugins).
"""

from .util import Image, Dict, appdata_dir, urlopen  # noqa
from .util import BaseProgressIndicator, StdoutProgressIndicator  # noqa
from .util import string_types, text_type, binary_type  # noqa
from .findlib import load_lib  # noqa
from .fetching import get_remote_file  # noqa
from .request import Request, RETURN_BYTES  # noqa
from .format import Format, FormatManager  # noqa
# todo: reader, writer
# todo: read or write request?


def _prepare_docs():
    
    functions, classes = [], []
    for name in globals():
        func_type = type(load_lib)
        if name.startswith('_'):
            continue
        ob = globals()[name]
        if isinstance(ob, type):
            classes.append(name)
        elif isinstance(ob, func_type):
            functions.append(name)
    classes.sort()
    functions.sort()
    extradocs = '\nFunctions: '
    extradocs += ', '.join([':func:`.%s`' % n for n in functions])
    extradocs += '\n\nClasses: '
    extradocs += ', '.join([':class:`.%s`' % n for n in classes])
    extradocs += '\n\n----\n'
    
    # Update
    globals()['__doc__'] += extradocs
    globals()['__all__'] = functions + classes

_prepare_docs()
