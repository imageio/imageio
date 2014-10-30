"""
Build docs for formats.
"""

import os
import sys

import imageio


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DOC_DIR = os.path.dirname(THIS_DIR)

files_to_remove = []


generaltext = """
.. note::
    The  parameters listed below can be specifief as keyword arguments in
    the ``read()``, ``imread()``, ``mimread()`` etc. functions.
"""

def _write(fname, text):
    files_to_remove.append(fname)
    with open(os.path.join(DOC_DIR, fname), 'wb') as f:
        f.write(text.encode('utf-8'))


def main():
    
    # Build main plugin dir
    title = "Imageio formats"
    text = '%s\n%s\n\n' % (title, '=' * len(title))
    
    text += 'This page lists all formats currently supported by imageio:'
    
    # Get bullet list of all formats
    ss = ['']
    for format in imageio.formats: 
        s = '  * :ref:`%s <%s>` - %s' % (format.name, 
                                         format.name, format.description)
        ss.append(s)
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
        text += generaltext + '\n\n'
        text += 'Extensions: %s\n\n' % ext
        docs = '    ' + format.__doc__.lstrip()
        docs = '\n'.join([x[4:].rstrip() for x in docs.splitlines()])
        #
        text += docs + '\n\n'
        
        #members = '\n  :members:\n\n'
        #text += '.. autoclass:: %s.Reader%s' % (format.__module__, members)
        #text += '.. autoclass:: %s.Writer%s' % (format.__module__, members)
        
        _write('format_%s.rst' % format.name.lower(), text)


def clean():
    for fname in files_to_remove:
        os.remove(os.path.join(DOC_DIR, fname))
