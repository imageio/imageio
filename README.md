# IMAGEIO

[![Build Status](https://travis-ci.org/imageio/imageio.svg?branch=master)](https://travis-ci.org/imageio/imageio)
[![Coverage Status](https://coveralls.io/repos/imageio/imageio/badge.png?branch=master)](https://coveralls.io/r/imageio/imageio?branch=master)
[![Pypi downloads](https://pypip.in/d/imageio/badge.png)](https://crate.io/packages/imageio)
[![Documentation Status](https://readthedocs.org/projects/imageio/badge/?version=latest)](https://readthedocs.org/projects/imageio/?badge=latest)
   
Website: http://imageio.github.io

<!-- From below ends up on the website Keep this ---- DIVIDER ---- -->

<p class='summary'>

The imageio library aims to support reading and writing a wide 
range of image data, including animated images, volumetric data, 
and scientific formats. It is written in pure Python (2.x and 3.x) 
and is designed to be powerful, yet simple in usage and installation.
</p>
<p>
Imageio has a relatively simple core that provides a common interface 
to different file formats. The actual file formats are implemented in 
plugins, which makes imageio easy to extend. A large range of formats
are already supported (in part thanks to the freeimage library), but we 
aim to include much more (scientific) formats in the future.
</p>


<h2>Example</h2>
Here's a minimal example of how to use imageio. For the docs for 
<a href='http://imageio.readthedocs.org/en/latest/examples.html'>more examples</a>.
<pre>
>>> import imageio
>>> im = imageio.imread('chelsea.png')
>>> im.shape  # im is a numpy array
(300, 451, 3)
>>> imageio.imsave('chelsea-gray.jpg', im[:,:,0])
</pre>

<h2>API in a nutshell</h2>
As a user, you just have to remember a handfull of functions:

<ul>
    <li>imread() and imsave() - for single images</li>
    <li>mimread() and mimsave() - for image series (animations)</li>
    <li>volread() and volsave() - for volumetric image data</li>
    <li>read() and save() - for more control (e.g. streaming)</li>
    <li>See the <a href='http://imageio.readthedocs.org/en/latest/userapi.html'>user api</a> for more information</li>
</ul>


<h2>Features</h2>
<ul>
    <li>Simple interface via a consise set of functions.</li>
    <li>Easy to install (no compilation required, binaries are automatically downloaded).</li>    
    <li>Pure Python, runs on Python 2.x, 3.x, Pypy, Jython?</li>
    <li>Lots of supported formats.</li>
    <li>Can also read from zipfiles, http/ftp, and raw bytes.</li>
    <li>Easy to extend using plugins.</li>
</ul>


<h2>Installation</h2>

<ul>
    <li>Via conda: <kdb>conda install imageio</kdb></li> 
    <li>Via pip: <kdb>pip install imageio</kdb></li>
</ul>
