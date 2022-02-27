Installing imageio
==================

Imageio is written in pure Python, so installation is easy.
Imageio works on Python 3.5+. It also works on Pypy.
Imageio depends on Numpy and Pillow. For some formats, imageio needs
additional libraries/executables (e.g. ffmpeg), which imageio helps you
to download/install.

To install imageio, use one of the following methods:

* If you are in a conda env: ``conda install -c conda-forge imageio``
* If you have pip: ``pip install imageio``
* Good old ``python setup.py install``

After installation, checkout the
:doc:`examples <../examples>` and :doc:`user api <../reference/userapi>`.

Still running Python 2.7? Read :doc:`here <drop27>`.
