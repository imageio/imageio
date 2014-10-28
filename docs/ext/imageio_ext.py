""" Invoke various functionality for imageio docs.
"""

import imageio
#import examplesgenerator


def init():
    imageio._format_docs = imageio.formats.create_docs_for_all_formats()
    
    #print('Generating examples.')
    # examplesgenerator.main()
    
def clean(app, *args):
    pass
    #examplesgenerator.clean()

def setup(app):
    init()
    app.connect('build-finished', clean)
