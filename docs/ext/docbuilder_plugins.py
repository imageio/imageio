"""
Build docs for plugins.
"""

import os

import imageio


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DOC_DIR = os.path.dirname(THIS_DIR)


def main():
    
    # Build main plugin dir
    title = "Creating imageio plugins"
    text = '%s\n%s\n\n' % (title, '=' * len(title))
    
    text += '.. automodule:: imageio.plugins\n\n'
    
    # Insert code from example plugin
    text += 'Example / template plugin\n-------------------------\n\n'
    text += ".. code-block:: python\n    :linenos:\n\n"
    filename = imageio.plugins.example.__file__
    code = open(filename, 'rb').read().decode('utf-8')
    code = '\n'.join(['    ' + line.rstrip() for line in code.splitlines()])
    text += code
    
    with open(os.path.join(DOC_DIR, 'plugins.rst'), 'wb') as f:
        f.write(text.encode('utf-8'))


def clean():
    os.remove(os.path.join(DOC_DIR, 'plugins.rst'))

