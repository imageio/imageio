# -*- coding: utf-8 -*-
# Copyright (c) 2014, Vispy team, imageio team
# Distributed under the (new) BSD License. See LICENSE.txt for more info.

""" The core of imageio; everything that is not a plugin.
"""


from .util import Image, DictWitNames, appdata_dir  # noqa
from .util import BaseProgressIndicator, StdoutProgressIndicator  # noqa
from .util import string_types, text_type, binary_type  # noqa
from .findlib import load_lib
from .fetching import get_remote_file  # noqa
from .request import Request, RETURN_BYTES  # noqa
from .format import Format, FormatManager  # noqa
from .format import EXPECT_IM, EXPECT_MIM, EXPECT_VOL, EXPECT_MVOL  # noqa
# todo: reader, writer
# todo: read or write request?

