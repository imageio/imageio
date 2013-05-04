-------
IMAGEIO
-------

The imageio library aims to support reading and writing a wide 
range of image data, including animated images, volumetric data, and
scientific formats. It is written in pure Python (2.x and 3.x) and
is designed to be powerful, yet simple in usage and installation.

Imageio has a relatively simple core that provides a common interface
to different file formats. The actual file formats are implemented in
plugins, which makes imageio easy to extend. A large range of formats
are already supported (in part thanks to the freeimage library), but
we aim to include much more (scientific) formats in the future.

website: http://imageio.readthedocs.org

Installation
------------

  * pip install imageio 
  * python setup.py install
  * etc.


For developers
--------------

You can clone the source from the repository and put it somwhere on your PYTHONPATH.
Then import imageio as usual, saving you from having to reinstall it after
each update.

