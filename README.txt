-------
IMAGEIO
-------

The imageio library aims to support reading and writing a wide 
range of image data, including animated images, volumetric data, and
scientific formats. It is written in pure Python (2.x and 3.x) and
is designed to be powerful, yet simple in usage and installation.

The imageio library is intended as a replacement for PIL. Currently, most
functionality is obtained by wrapping the FreeImage library using ctypes.

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

