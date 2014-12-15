Installing imageio
==================

Imageio is written in pure Python, so installation is easy. 
Imageio works on Python 2.6 and up (including Python 3). It also works
on Pypy. For some formats, imageio needs
additional libraries (e.g. freeimage), which are downloaded
automatically and stored in a folder in your application data.

To install imageio, use one of the following methods:
    
* If you are in a conda env: ``conda install -c pyzo imageio``
* If you have pip: ``pip install imageio``
* Good old ``python setup.py install``

To install imageio with the freeimage library and a few images included,
you can force downloading the libs when building, or use one of the
provided archives from pypi:
    
* ``python setup.py build_with_fi install``
* ``pip install https://pypi.python.org/packages/source/i/imageio/imageio-x.y-linux64.zip``

For developers, we provide a simple mechanism to allow importing 
imageio from the cloned repository. See the file ``imageio.proxy.io`` for
details.
