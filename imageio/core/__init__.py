# -*- coding: utf-8 -*-
# Copyright (c) 2014, Imageio team
# Distributed under the (new) BSD License. See LICENSE.txt for more info.

""" The core of imageio; everything that is not a plugin.
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
