# IMAGEIO

[![PyPI Version](https://img.shields.io/pypi/v/imageio.svg)](https://pypi.python.org/pypi/imageio/)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/imageio.svg)](https://pypi.python.org/pypi/imageio/)
[![Build Status](https://travis-ci.org/imageio/imageio.svg?branch=master)](https://travis-ci.org/imageio/imageio)
[![Coverage Status](https://coveralls.io/repos/imageio/imageio/badge.png?branch=master)](https://coveralls.io/r/imageio/imageio?branch=master)
[![Documentation Status](https://readthedocs.org/projects/imageio/badge/?version=latest)](https://imageio.readthedocs.io)
[![PyPi Download stats](http://pepy.tech/badge/imageio)](http://pepy.tech/project/imageio)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.1488561.svg)](https://doi.org/10.5281/zenodo.1488561)

Website: http://imageio.github.io

<!-- From below ends up on the website Keep this ---- DIVIDER ---- -->

<p class='summary'>
Imageio is a Python library that provides an easy interface to read and
write a wide range of image data, including animated images, video,
volumetric data, and scientific formats. It is cross-platform, runs on
Python 3.5+, and is easy to install.
</p>

<h2>Example</h2>
Here's a minimal example of how to use imageio. See the docs for
<a href='http://imageio.readthedocs.io/en/latest/examples.html'>more examples</a>.
<pre>
import imageio
im = imageio.imread('imageio:chelsea.png')  # read a standard image
im.shape  # im is a numpy array
>> (300, 451, 3)
imageio.imwrite('~/chelsea-gray.jpg', im[:, :, 0])
</pre>

<h2>API in a nutshell</h2>
As a user, you just have to remember a handfull of functions:

<ul>
    <li>imread() and imwrite() - for single images</li>
    <li>mimread() and mimwrite() - for image series (animations)</li>
    <li>volread() and volwrite() - for volumetric image data</li>
    <li>get_reader() and get_writer() - for more control (e.g. streaming)</li>
    <li>See the <a href='http://imageio.readthedocs.io/en/latest/userapi.html'>user api</a> for more information</li>
</ul>


<h2>Features</h2>
<ul>
    <li>Simple interface via a consise set of functions.</li>
    <li>Easy to <a href='http://imageio.readthedocs.io/en/latest/installation.html'>install</a> using conda or pip.</li>
    <li>Few dependencies (only Numpy and Pillow).</li>
    <li>Pure Python, runs on Python 3.5+, and Pypy</li>
    <li>Cross platform, runs on Windows, Linux, OS X (Raspberry Pi planned)</li>
    <li>Lots of supported <a href='http://imageio.readthedocs.io/en/latest/formats.html'>formats</a>.</li>
    <li>Can read from file names, file objects, zipfiles, http/ftp, and raw bytes.</li>
    <li>Easy to extend using plugins.</li>
    <li>Code quality is maintained with many tests and continuous integration.</li>
</ul>


<h2>Citing imageio</h2>
<p>
If you use imageio for scientific work, we would appreciate a citation.
We have a <a href='https://doi.org/10.5281/zenodo.1488561'>DOI</a>!
</p>


<h2>Details</h2>
<p>
Imageio has a relatively simple core that provides a common interface
to different file formats. This core takes care of reading from different
sources (like http), and exposes a simple API for the plugins to access
the raw data. All file formats are implemented in plugins. Additional
plugins can easily be registered.
</p><p>
Some plugins rely on external libraries (e.g. ffmpeg). Imageio provides
a way to download these with one function call, and prompts the user to do
so when needed. The download is cached in your appdata
directory, this keeps imageio light and scalable.
</p><p>
Imageio provides a wide range of image formats, including scientific
formats. Any help with implementing more formats is very welcome!
</p><p>
The codebase adheres to (a subset of) the PEP8 style guides. We strive
for maximum test coverage (100% for the core, >95% for each plugin).
</p>


<h2>Dependencies</h2>

Minimal requirements:
<ul>
    <li>Python 3.5+</li>
    <li>Numpy</li>
    <li>Pillow</li>
</ul>

Optional Python packages:
<ul>
    <li>imageio-ffmpeg (for working with video files)</li>
    <li>itk or SimpleITK (for ITK formats)</li>
    <li>astropy (for FITS plugin)</li>
    <li>osgeo (for GDAL plugin)</li>
</ul>

Still on an earlier version of Python? Imageio version 2.6.x supports Python 2.7 and 3.4.


<h2>Origin and outlook</h2>
<p>
Imageio was based out of the frustration that many libraries that needed
to read or write image data produced their own functionality for IO.
PIL did not meet the needs very well, and libraries like scikit-image
need to be able to deal with scientific formats. There was a
need for a good image io library, which is an easy dependency, easy to
maintain, and scalable to exotic file formats.
</p><p>
Imageio started out as component of the scikit-image
project, through which it was able to support a lot of common formats.
We created a simple but powerful core, a clean user API, and a proper
plugin system.
</p><p>
The purpose of imageio is to support reading and writing of image data.
We're not processing images, you should use e.g. scikit-image for that. Imageio
should be easy to install and be lightweight. Imageio's plugin system
makes it possible to scale the number of supported formats and still
keep a small footprint.
</p><p>
It is our hope to form a group of developers, whom each maintain
one or more plugins. In that way, the burden of each developer is low,
and together we can make imageio into a really useful library!
</p>

<h2>Contributing</h2>

<p>Install a complete development environment:</p>

<pre>
pip install -r requirements.txt
pip install -e .
</pre>

<p><i>N.B. this does not include GDAL because it has awkward compiled dependencies</i></p>

<p>You may see failing test(s) due to missing installed components.
On ubuntu, do <code>sudo apt install libfreeimage3</code></p>

<p>
Style checks, unit tests and coverage are controlled by <code>invoke</code>.
Before committing, check these with:</p>

<pre>
# reformat code on python 3.6+
invoke autoformat
# check there are no style errors
invoke test --style
# check the tests pass
invoke test --unit
# check test coverage (re-runs tests)
invoke test --cover
</pre>
