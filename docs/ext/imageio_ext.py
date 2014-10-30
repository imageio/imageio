""" Invoke various functionality for imageio docs.
"""

import imageio
import docbuilder_plugins
import docbuilder_formats


def _deal_with_reader_and_witer():
    # Create Reader and Writer subclasses that are going to be placed
    # in the format module so that autoclass can find them. They need
    # to be new classes, otherwise sphinx considers them aliases.
    class Reader(imageio.core.format.Format.Reader):
        pass
    class Writer(imageio.core.format.Format.Writer):
        pass
    imageio.core.format.Reader = Reader
    imageio.core.format.Writer = Writer
    
    # We set the docs of the original classes, and remove the docstring
    # from the original classes so that Reader and Writer do not show
    # up in the docs of the Format class.
    Reader.__doc__ = imageio.core.format.Format.Reader.__doc__
    Writer.__doc__ = imageio.core.format.Format.Writer.__doc__
    imageio.core.format.Format.Reader.__doc__ = ''
    imageio.core.format.Format.Writer.__doc__ = ''


def init():
    
    print('Preparing Format.Reader and Format.Writer for doc generation.')
    _deal_with_reader_and_witer()
    
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
