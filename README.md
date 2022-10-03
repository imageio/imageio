# IMAGEIO

[![CI](https://github.com/imageio/imageio/workflows/CI/badge.svg)](https://github.com/imageio/imageio/actions/workflows/ci.yml)
[![CD](https://github.com/imageio/imageio/workflows/CD/badge.svg)](https://github.com/imageio/imageio/actions/workflows/cd.yml)
[![codecov](https://codecov.io/gh/imageio/imageio/branch/master/graph/badge.svg?token=81Zhu9MDec)](https://codecov.io/gh/imageio/imageio)
[![Docs](https://readthedocs.org/projects/imageio/badge/?version=latest)](https://imageio.readthedocs.io)

[![Supported Python Versions](https://img.shields.io/pypi/pyversions/imageio.svg)](https://pypi.python.org/pypi/imageio/)
[![PyPI Version](https://img.shields.io/pypi/v/imageio.svg)](https://pypi.python.org/pypi/imageio/)
![PyPI Downloads](https://img.shields.io/pypi/dm/imageio?color=blue)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.1488561.svg)](https://doi.org/10.5281/zenodo.1488561)



Website: https://imageio.readthedocs.io/

<p class='summary'>
Imageio is a Python library that provides an easy interface to read and
write a wide range of image data, including animated images, video,
volumetric data, and scientific formats. It is cross-platform, runs on
Python 3.7+, and is easy to install.
</p>

<p>
    Professional support is available via <a href='https://tidelift.com/funding/github/pypi/imageio'>Tidelift</a>.
</p>

<h2>Example</h2>
Here's a minimal example of how to use imageio. See the docs for
<a href='https://imageio.readthedocs.io/en/stable/examples.html'>more examples</a>.

```python
import imageio.v3 as iio
im = iio.imread('imageio:chelsea.png')  # read a standard image
im.shape  # im is a NumPy array of shape (300, 451, 3)
iio.imwrite('chelsea.jpg', im)  # convert to jpg
```

<h2>API in a nutshell</h2>
As a user, you just have to remember a handful of functions:

<ul>
    <li>imread() - for reading</li>
    <li>imwrite() - for writing</li>
    <li>imiter() - for iterating image series (animations/videos/OME-TIFF/...)</li>
    <li>improps() - for standardized metadata</li>
    <li>immeta() - for format-specific metadata</li>
    <li>imopen() - for advanced usage</li>
</ul>

See the <a href='https://imageio.readthedocs.io/en/stable/reference/index.html'>API docs</a> for more information.


<h2>Features</h2>
<ul>
    <li>Simple interface via a concise set of functions</li>
    <li>Easy to <a href='https://imageio.readthedocs.io/en/stable/getting_started/installation.html'>install</a> using Conda or pip</li>
    <li>Few dependencies (only NumPy and Pillow)</li>
    <li>Pure Python, runs on Python 3.7+, and PyPy</li>
    <li>Cross platform, runs on Windows, Linux, macOS</li>
    <li>More than 295 supported <a href='https://imageio.readthedocs.io/en/stable/formats/index.html'>formats</a></li>
    <li>Read/Write support for various <a href='https://imageio.readthedocs.io/en/stable/getting_started/requests.html'>resources</a> (files, URLs, bytes, FileLike objects, ...)</li>
    <li>Code quality is maintained via continuous integration and continous deployment</li>
</ul>


<h2>Dependencies</h2>

Minimal requirements:
<ul>
    <li>Python 3.7+</li>
    <li>NumPy</li>
    <li>Pillow >= 8.3.2</li>
</ul>

Optional Python packages:
<ul>
    <li>imageio-ffmpeg (for working with video files)</li>
    <li>pyav (for working with video files)</li>
    <li>tifffile (for working with TIFF files)</li>
    <li>itk or SimpleITK (for ITK plugin)</li>
    <li>astropy (for FITS plugin)</li>
    <li><a href='https://codeberg.org/monilophyta/imageio-flif'>imageio-flif</a> (for working with <a href='https://github.com/FLIF-hub/FLIF'>FLIF</a> image files)</li>
</ul>

<h2>Citing imageio</h2>
<p>
If you use imageio for scientific work, we would appreciate a citation.
We have a <a href='https://doi.org/10.5281/zenodo.1488561'>DOI</a>!
</p>


<h2>Security contact information</h2>

To report a security vulnerability, please use the
<a href='https://tidelift.com/security'>Tidelift security contact</a>.
Tidelift will coordinate the fix and disclosure.


<h2>ImageIO for enterprise</h2>

Available as part of the Tidelift Subscription.

The maintainers of imageio and thousands of other packages are working with Tidelift to deliver commercial support and maintenance for the open source dependencies you use to build your applications. Save time, reduce risk, and improve code health, while paying the maintainers of the exact dependencies you use.
<a href='https://tidelift.com/subscription/pkg/pypi-imageio?utm_source=pypi-imageio&utm_medium=referral&utm_campaign=readme'>Learn more</a>.


<h2>Details</h2>
<p>
    The core of ImageIO is a set of user-facing APIs combined with a plugin manager. API calls choose sensible defaults and then call the plugin manager, which deduces the correct plugin/backend to use for the given resource and file format. The plugin manager then adds sensible backend-specific defaults and then calles one of ImageIOs many backends to perform the actual loading. This allows ImageIO to take care of most of the gory details of loading images for you, while still allowing you to customize the behavior when and where you need to. You can find a more detailed explanation of this process in <a href='https://imageio.readthedocs.io/en/stable/getting_started/overview.htmle'>our documentation</a>.

<h2>Contributing</h2>

We welcome contributions of any kind. Here are some suggestions on how you are able to contribute

- add missing formats to the format list
- suggest/implement support for new backends
- report/fix any bugs you encounter while using ImageIO

To assist you in getting started with contributing code, take a look at the [development section](https://imageio.readthedocs.io/en/stable/development/index.html) of the docs. You will find instructions on setting up the dev environment as well as examples on how to contribute code.
