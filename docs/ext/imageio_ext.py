""" Invoke various functionality for imageio docs.
"""

import os
import sys

import imageio

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DOC_DIR = os.path.dirname(THIS_DIR)


files_to_remove = []


def setup(app):
    init()
    app.connect('build-finished', clean)


def init():
    
    print('Special preparations for imageio docs:')
    
    for func in [prepare_reader_and_witer,
                 prepare_core_docs,
                 create_plugin_docs,
                 create_format_docs,
                 create_standard_images_docs,
                 ]:
        print('  ' + func.__doc__.strip())
        func()


def clean(app, *args):
    for fname in files_to_remove:
        filename = os.path.join(DOC_DIR, fname)
        if os.path.isfile(filename):
            os.remove(filename)


def _write(fname, text):
    files_to_remove.append(fname)
    with open(os.path.join(DOC_DIR, fname), 'wb') as f:
        f.write(text.encode('utf-8'))


##


def prepare_reader_and_witer():
    """ Prepare Format.Reader and Format.Writer for doc generation.
    """
    
    # Create Reader and Writer subclasses that are going to be placed
    # in the format module so that autoclass can find them. They need
    # to be new classes, otherwise sphinx considers them aliases.
    # We create the class using type() so that we can copy the __doc__.
    Reader = type('Reader', (imageio.core.format.Format.Reader, ),
                  {'__doc__':imageio.core.format.Format.Reader.__doc__ })
    Writer = type('Writer', (imageio.core.format.Format.Writer, ),
                  {'__doc__':imageio.core.format.Format.Writer.__doc__ })
    
    imageio.core.format.Reader = Reader
    imageio.core.format.Writer = Writer
    
    # We set the docs of the original classes, and remove the original
    # classes so that Reader and Writer do not show up in the docs of
    # the Format class.
    imageio.core.format.Format.Reader = None  # .__doc__ = ''
    imageio.core.format.Format.Writer = None  # .__doc__ = ''


def prepare_core_docs():
    """ Prepare imageio.core for doc generation.
    """
    # Set __all__ and add to __doc__ in imageio.core module,
    # so that the documentation gets generated correctly.
    
    D = imageio.core.__dict__
    
    excludes = 'binary_type', 'text_type'
    
    # Collect functions and classes in imageio.core
    functions, classes = [], []
    func_type = type(prepare_core_docs)
    for name in D:
        if name.startswith('_') or name in excludes:
            continue
        ob = D[name]
        if isinstance(ob, type):
            classes.append(name)
        elif isinstance(ob, func_type):
            functions.append(name)
    
    # Write summaries
    classes.sort()
    functions.sort()
    extradocs = '\nFunctions: '
    extradocs += ', '.join([':func:`.%s`' % n for n in functions])
    extradocs += '\n\nClasses: '
    extradocs += ', '.join([':class:`.%s`' % n for n in classes])
    extradocs += '\n\n----\n'
    
    # Update
    D['__doc__'] += extradocs
    D['__all__'] = functions + classes



def create_plugin_docs():
    """ Create docs for creating plugins.
    """
    
    # Build main plugin dir
    title = "Creating imageio plugins"
    text = '%s\n%s\n\n' % (title, '=' * len(title))
    
    text += '.. automodule:: imageio.plugins\n\n'
    
    # Insert code from example plugin
    text += 'Example / template plugin\n-------------------------\n\n'
    text += ".. code-block:: python\n    :linenos:\n\n"
    filename = imageio.plugins.example.__file__.replace('.pyc', '.py')
    code = open(filename, 'rb').read().decode('utf-8')
    code = '\n'.join(['    ' + line.rstrip() for line in code.splitlines()])
    text += code
    
    # Write
    _write('plugins.rst', text)

format_doc_text = """
This page lists all formats currently supported by imageio. Each format
can support extra keyword arguments for reading and writing, which can be 
specified in the call to ``get_reader()``, ``get_writer()``, ``imread()``,
``imwrite()`` etc. Further, formats are free to provide additional
methods on their Reader and Writer objects. These parameters and extra
methods are specified in the documentation for each format.
"""

def create_format_docs():
    """ Create documentation for the formats.
    """
    
    # Build main plugin dir
    title = "Imageio formats"
    text = '%s\n%s\n%s\n\n' % ('=' * len(title), title, '=' * len(title))
    
    text += format_doc_text
    
    # Get bullet list of all formats
    ss = ['\n']
    covered_formats = []
    modemap = {'i': 'Single images', 'I': 'Multiple images',
               'v': 'Single volumes', 'V': 'Multiple volumes', }
    for mode in 'iIvV-':
        subtitle = modemap.get(mode, 'Unsorted')
        subs = []
        for format in imageio.formats: 
            if ((mode in format.modes) or 
                (mode == '-' and format not in covered_formats)):
                covered_formats.append(format)
                s = '  * :ref:`%s <%s>` - %s' % (format.name, 
                                                 format.name, 
                                                 format.description)
                subs.append(s)
        if subs:
            ss.append('%s\n%s\n' % (subtitle, '^' * len(subtitle)))
            ss.extend(subs)
            ss.append('')
    
    text += '\n'.join(ss) + '\n\n'
    _write('formats.rst', text)
    
    
    # Get more docs for each format
    for format in imageio.formats:
        
        title = '%s %s' % (format.name, format.description)
        ext = ', '.join(['``%s``' % e for e in format.extensions])
        ext = ext or 'None'
        #
        text = ':orphan:\n\n'
        text += '.. _%s:\n\n' % format.name
        text += '%s\n%s\n\n' % (title, '='*len(title))
        #
        text += 'Extensions: %s\n\n' % ext
        docs = '    ' + format.__doc__.lstrip()
        docs = '\n'.join([x[4:].rstrip() for x in docs.splitlines()])
        #
        text += docs + '\n\n'
        
        #members = '\n  :members:\n\n'
        #text += '.. autoclass:: %s.Reader%s' % (format.__module__, members)
        #text += '.. autoclass:: %s.Writer%s' % (format.__module__, members)
        _write('format_%s.rst' % format.name.lower(), text)


def create_standard_images_docs():
    """ Create documentation for imageio's standard images.
    """
    
    title = "Imageio standard images"
    text = '%s\n%s\n%s\n\n' % ('=' * len(title), title, '=' * len(title))
    
    docs = """
        Imageio provides a number of standard images. These include classic
        2D images, as well as animated and volumetric images. To the best
        of our knowledge, all the listed images are in public domain.
        
        The image names can be loaded by using a special URI,
        e.g. ``imread('imageio:astronaut.png')``.
        The images are automatically downloaded (and cached in your appdata
        directory).
        """
    text += '\n'.join([line.strip() for line in docs.splitlines()])
    text += '\n\n'
    
    from imageio.core.request import EXAMPLE_IMAGES
    baseurl = 'https://github.com/imageio/imageio-binaries/raw/master/images/'
    
    
    sort_by_ext_and_name = lambda x: tuple(reversed(x.rsplit('.', 1)))
    for name in sorted(EXAMPLE_IMAGES, key=sort_by_ext_and_name):
        description = EXAMPLE_IMAGES[name]
        text += '* `%s <%s>`_: %s\n\n' % (name,  baseurl + name, description)
    
    _write('standardimages.rst', text)
