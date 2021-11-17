""" Invoke various functionality for imageio docs.
"""

from pathlib import Path

import imageio


def setup(app):
    init()
    app.connect("source-read", rstjinja)


def init():

    print("Special preparations for imageio docs:")

    for func in [
        prepare_reader_and_witer,
    ]:
        print("  " + func.__doc__.strip())
        func()


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


def rstjinja(app, docname, source):
    if docname == "formats/index":
        from imageio.config import known_plugins, extension_list

        src = source[0]
        rendered = app.builder.templates.render_string(
            src, {"formats": extension_list, "plugins": known_plugins}
        )
        source[0] = rendered

    if docname == "formats/video_formats":
        from imageio.config import known_plugins, video_extensions

        src = source[0]
        rendered = app.builder.templates.render_string(
            src, {"formats": video_extensions, "plugins": known_plugins}
        )
        source[0] = rendered

    if docname == "getting_started/standardimages":
        from imageio.core.request import EXAMPLE_IMAGES

        src = source[0]
        rendered = app.builder.templates.render_string(
            src,
            {
                "images": EXAMPLE_IMAGES,
                "ordered_keys": sorted(
                    EXAMPLE_IMAGES, key=lambda x: tuple(reversed(x.rsplit(".", 1)))
                ),
                "base_url": "https://github.com/imageio/imageio-binaries/raw/master/images/",
            },
        )
        source[0] = rendered

    if docname == "development/plugins":
        example_plugin = Path(
            imageio.plugins.example.__file__.replace(".pyc", ".py")
        ).read_text()
        example_plugin = [line.rstrip() for line in example_plugin.splitlines()]

        src = source[0]
        rendered = app.builder.templates.render_string(
            src, {"example_plugin": example_plugin}
        )
        source[0] = rendered
