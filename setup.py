# -*- coding: utf-8 -*-
# Copyright (C) 2014-2020, imageio contributors
#
# imageio is distributed under the terms of the (new) BSD License.
# The full license can be found in 'license.txt'.

# styletest: skip

"""

Release:

  * Write release notes
  * Increase __version__
  * git tag the release (and push the tag to Github)
  * Upload to Pypi: python setup.py sdist bdist_wheel upload
  * Update conda recipe on conda-forge feedstock

"""

import os
from itertools import chain

try:
    from setuptools import setup  # Supports wheels
except ImportError:
    from distutils.core import setup  # Supports anything else


name = "imageio"
description = "Library for reading and writing a wide range of image, video, scientific, and volumetric data formats."

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

# Get version and docstring
__version__ = None
__doc__ = ""
docStatus = 0  # Not started, in progress, done
initFile = os.path.join(THIS_DIR, "imageio", "__init__.py")
for line in open(initFile).readlines():
    if line.startswith("__version__"):
        exec(line.strip())
    elif line.startswith('"""'):
        if docStatus == 0:
            docStatus = 1
            line = line.lstrip('"')
        elif docStatus == 1:
            docStatus = 2
    if docStatus == 1:
        __doc__ += line.rstrip() + "\n"

# Template for long description. __doc__ gets inserted here
long_description = """
.. image:: https://github.com/imageio/imageio/workflows/CI/badge.svg
    :target: https://github.com/imageio/imageio/actions

__doc__

Release notes: https://github.com/imageio/imageio/blob/master/CHANGELOG.md

Example:

.. code-block:: python

    >>> import imageio
    >>> im = imageio.imread('imageio:astronaut.png')
    >>> im.shape  # im is a numpy array
    (512, 512, 3)
    >>> imageio.imwrite('astronaut-gray.jpg', im[:, :, 0])

See the `API Reference <https://imageio.readthedocs.io/en/stable/reference/index.html>`_
or `examples <https://imageio.readthedocs.io/en/stable/examples.html>`_
for more information.
"""

# Prepare resources dir
package_data = [
    "py.typed",
    "**/*.pyi",
    "*.pyi",
]


# pinned to > 8.3.2 due to security vulnerability
# See: https://github.com/advisories/GHSA-98vv-pw6r-q6q4
install_requires = ["numpy", "pillow>= 8.3.2,<10.1.0"]

plugins = {
    "bsdf": [],
    "dicom": [],
    "feisem": [],
    "ffmpeg": ["imageio-ffmpeg", "psutil"],
    "freeimage": [],
    "lytro": [],
    "numpy": [],
    "pillow": [],
    "simpleitk": [],
    "spe": [],
    "swf": [],
    "tifffile": ["tifffile"],
    "pyav": ["av"],
}

cpython_only_plugins = {
    "fits": ["astropy"],
}

extras_require = {
    "build": ["wheel"],
    "linting": ["black", "flake8"],
    "test": ["pytest", "pytest-cov", "fsspec[github]"],
    "docs": ["sphinx<6", "numpydoc", "pydata-sphinx-theme"],
    **plugins,
    **cpython_only_plugins,
    "gdal": ["gdal"],  # gdal currently fails to install :(
    "itk": ["itk"],  # itk builds from source (expensive on CI).
}

extras_require["full"] = sorted(set(chain.from_iterable(extras_require.values())))
extras_require["dev"] = extras_require["test"] + extras_require["linting"]
extras_require["all-plugins"] = sorted(
    set(chain(*plugins.values(), *cpython_only_plugins.values()))
)
extras_require["all-plugins-pypy"] = sorted(set(chain(*plugins.values())))


setup(
    name=name,
    version=__version__,
    author="imageio contributors",
    author_email="almar.klein@gmail.com",
    license="BSD-2-Clause",
    url="https://github.com/imageio/imageio",
    download_url="http://pypi.python.org/pypi/imageio",
    keywords="image video volume imread imwrite io animation ffmpeg",
    description=description,
    long_description=long_description.replace("__doc__", __doc__),
    platforms="any",
    provides=["imageio"],
    python_requires=">=3.8",
    install_requires=install_requires,
    extras_require=extras_require,
    packages=["imageio", "imageio.core", "imageio.plugins", "imageio.config"],
    package_dir={"imageio": "imageio"},
    zip_safe=False,
    # Data in the package
    package_data={"imageio": package_data},
    entry_points={
        "console_scripts": [
            "imageio_download_bin=imageio.__main__:download_bin_main",
            "imageio_remove_bin=imageio.__main__:remove_bin_main",
        ]
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Education",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
