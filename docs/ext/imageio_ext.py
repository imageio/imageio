""" Invoke various functionality for imageio docs.
"""

import imageio
import docbuilder_plugins
import docbuilder_formats


class Reader(imageio.core.format.Format.Reader):
    pass
class Writer(imageio.core.format.Format.Writer):
    pass
Reader.__doc__ = imageio.core.format.Format.Reader.__doc__
Writer.__doc__ = imageio.core.format.Format.Writer.__doc__


def init():
    
    # Shortcuts for Format.Reader and Format.Writer, 
    # because autodoc does not understand otherwise
    imageio.core.format.Reader = Reader
    imageio.core.format.Writer = Writer
    
    print('Generating docs for format.')
    docbuilder_formats.main()
    print('Generating docs for creating plugins.')
    docbuilder_plugins.main()

    
def clean(app, *args):
    docbuilder_formats.clean()
    docbuilder_plugins.clean()


def setup(app):
    init()
    app.connect('build-finished', clean)
