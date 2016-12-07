Installing imageio
==================

Imageio is written in pure Python, so installation is easy. 
Imageio works on Python 2.6 and up (including Python 3). It also works
on Pypy. Imageio depends on Numpy and Pillow. For some formats, imageio needs
additional libraries/executables (e.g. ffmpeg), which imageio helps you
download and store in a folder in your application data.

To install imageio, use one of the following methods:
    
* If you are in a conda env: ``conda install -c conda-forge imageio``
* If you have pip: ``pip install imageio``
* Good old ``python setup.py install``

For developers, we provide a simple mechanism to allow importing 
imageio from the cloned repository. See the file ``imageio.proxy.io`` for
details.
