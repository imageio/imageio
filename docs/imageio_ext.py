""" Invoke various functionality for imageio docs.
"""

from pathlib import Path

import imageio


def setup(app):
    app.connect("source-read", rstjinja)


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

    if docname.endswith("standardimages"):
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
        example_plugin = (
            Path(imageio.plugins.__file__).parent / "example.py"
        ).read_text()
        example_plugin = [line.rstrip() for line in example_plugin.splitlines()]

        src = source[0]
        rendered = app.builder.templates.render_string(
            src, {"example_plugin": example_plugin}
        )
        source[0] = rendered
