""" Invoke various functionality for imageio docs.
"""

import os
from pathlib import Path

import imageio

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DOC_DIR = THIS_DIR


files_to_remove = []


def setup(app):
    init()
    app.connect("build-finished", clean)


def init():

    print("Special preparations for imageio docs:")

    for func in [
        prepare_reader_and_witer,
        create_plugin_docs,
        create_standard_images_docs,
    ]:
        print("  " + func.__doc__.strip())
        func()


def clean(app, *args):
    for fname in files_to_remove:
        filename = os.path.join(DOC_DIR, fname)
        if os.path.isfile(filename):
            os.remove(filename)


def _write(fname, text):
    files_to_remove.append(fname)
    with open(os.path.join(DOC_DIR, fname), "wb") as f:
        f.write(text.encode("utf-8"))


##


def prepare_reader_and_witer():
    """Prepare Format.Reader and Format.Writer for doc generation."""

    # Create Reader and Writer subclasses that are going to be placed
    # in the format module so that autoclass can find them. They need
    # to be new classes, otherwise sphinx considers them aliases.
    # We create the class using type() so that we can copy the __doc__.
    Reader = type(
        "Reader",
        (imageio.core.format.Format.Reader,),
        {"__doc__": imageio.core.format.Format.Reader.__doc__},
    )
    Writer = type(
        "Writer",
        (imageio.core.format.Format.Writer,),
        {"__doc__": imageio.core.format.Format.Writer.__doc__},
    )

    imageio.core.format.Reader = Reader
    imageio.core.format.Writer = Writer

    # We set the docs of the original classes, and remove the original
    # classes so that Reader and Writer do not show up in the docs of
    # the Format class.
    imageio.core.format.Format.Reader = None  # .__doc__ = ''
    imageio.core.format.Format.Writer = None  # .__doc__ = ''


def create_plugin_docs():
    """Create docs for creating plugins."""

    # Build main plugin dir
    title = "Creating imageio plugins"
    text = "%s\n%s\n\n" % (title, "=" * len(title))

    text += ".. automodule:: imageio.plugins\n\n"

    # Insert code from example plugin
    text += "Example / template plugin\n-------------------------\n\n"
    text += ".. code-block:: python\n    :linenos:\n\n"
    filename = imageio.plugins.example.__file__.replace(".pyc", ".py")
    code = open(filename, "rb").read().decode("utf-8")
    code = "\n".join(["    " + line.rstrip() for line in code.splitlines()])
    text += code

    # Write
    _write("development/plugins.rst", text)

def create_standard_images_docs():
    """Create documentation for imageio's standard images."""

    with open(Path(DOC_DIR) / "_templates" / "standard_images.rst", "r") as file:
        text = file.read()

    from imageio.core.request import EXAMPLE_IMAGES

    baseurl = "https://github.com/imageio/imageio-binaries/raw/master/images/"

    def sort_by_ext_and_name(x):
        return tuple(reversed(x.rsplit(".", 1)))

    for name in sorted(EXAMPLE_IMAGES, key=sort_by_ext_and_name):
        description = EXAMPLE_IMAGES[name]
        text += "* `%s <%s>`_: %s\n\n" % (name, baseurl + name, description)

    _write("getting_started/standardimages.rst", text)
