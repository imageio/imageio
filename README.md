# IMAGEIO

[![Build status](https://ci.appveyor.com/api/projects/status/4wjqg4o5r2q53iwt/branch/master?svg=true)](https://ci.appveyor.com/project/almarklein/imageio/branch/master)
[![Build Status](https://travis-ci.org/imageio/imageio.svg?branch=master)](https://travis-ci.org/imageio/imageio)
[![Coverage Status](https://coveralls.io/repos/imageio/imageio/badge.png?branch=master)](https://coveralls.io/r/imageio/imageio?branch=master)
[![Documentation Status](https://readthedocs.org/projects/imageio/badge/?version=latest)](https://imageio.readthedocs.org)
   
Website: http://imageio.github.io

<!-- From below ends up on the website Keep this ---- DIVIDER ---- -->

<p class='summary'>
Imageio is a Python library that provides an easy interface to read and
write a wide range of image data, including animated images, video,
volumetric data, and scientific formats. It is cross-platform, runs on
Python 2.x and 3.x, and is easy to install.
</p>

<h2>Example</h2>
Here's a minimal example of how to use imageio. See the docs for 
<a href='http://imageio.readthedocs.org/en/latest/examples.html'>more examples</a>.
<pre>
>>> import imageio
>>> im = imageio.imread('imageio:chelsea.png')  # read a standard image
>>> im.shape  # im is a numpy array
(300, 451, 3)
>>> imageio.imwrite('~/chelsea-gray.jpg', im[:, :, 0])
</pre>

<h2>API in a nutshell</h2>
As a user, you just have to remember a handfull of functions:

<ul>
    <li>imread() and imwrite() - for single images</li>
    <li>mimread() and mimwrite() - for image series (animations)</li>
    <li>volread() and volwrite() - for volumetric image data</li>
    <li>get_reader() and get_writer() - for more control (e.g. streaming)</li>
    <li>See the <a href='http://imageio.readthedocs.org/en/latest/userapi.html'>user api</a> for more information</li>
</ul>


<h2>Features</h2>
<ul>
    <li>Simple interface via a consise set of functions.</li>
    <li>Easy to <a href='http://imageio.readthedocs.org/en/latest/installation.html'>install</a> using conda or pip.</li>    
    <li>Few dependencies (only Numpy).</li>
    <li>Pure Python, runs on Python 2.6+, 3.x, and Pypy</li>
    <li>Cross platform, runs on Windows, Linux, OS X (Raspberry Pi planned)</li>
    <li>Lots of supported <a href='http://imageio.readthedocs.org/en/latest/formats.html'>formats</a>.</li>
    <li>Can read from file names, file objects, zipfiles, http/ftp, and raw bytes.</li>
    <li>Easy to extend using plugins.</li>
    <li>Code quality is maintained with many tests and continuous integration.</li>
</ul>


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
We plan to provide a wide range of image formats. Also scientific
formats. Any help in implementing more formats is very welcome!
</p><p>
The codebase adheres to (a subset of) the PEP8 style guides. We strive
for maximum test coverage (100% for the core, >95% for each plugin).
</p>


<h2>Dependencies</h2>

Minimal requirements:
<ul>
    <li>Python 3.x, 2.7 or 2.6</li>
    <li>Numpy</li>
    <li>Pillow</li>
</ul>

Optional Python packages:
<ul>
    <li>SimpleITK (for ITK formats)</li>
    <li>astropy (for FITS plugin)</li>
    <li>osgeo (for GDAL plugin)</li>
</ul>  


Optional libraries and executables that Imageio provides and can be downloaded
with one function call:
<ul>
    <li>freeimage (library)</li>
    <li>ffmpeg (executable)</li>
    <li>avbin (library)</li>
</ul>


<h2>Origin and outlook</h2>
<p>
Imageio was based out of the frustration that many libraries that needed
to read or write image data produced their own functionality for IO.
PIL did not meet the needs very well, and libraries like scikit-image
need to be able to deal with scientific formats. I felt there was a
need for a good image io library, which is an easy dependency, easy to
maintain, and scalable to exotic file formats.
</p><p>
Imageio started out as component of the scikit-image
project, through which it was able to support a lot of common formats.
We created a simple but powerful core, a clean user API, and a proper
plugin system.
</p><p>
The purpose of imageio is to support reading and writing of image data.
We're not processing images, you should use scikit-image for that. Imageio
should be easy to install and be lightweight. Imageio's plugin system
makes it possible to scale the number of supported formats and still
keep a low footprint.
</p><p>
It is impossible for one person to implement and maintain a wide variety
of formats. My hope is to form a group of developers, who each maintain
one or more plugins. In that way, the burder of each developer is low,
and together we can make imageio into a really useful library!
</p>
