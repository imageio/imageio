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
:doc:`examples  <examples>` and :doc:`user api <userapi>`.

Still running Python 2.7? Read :doc:`here <drop27>`.


Developers
----------

For developers, we provide a simple mechanism to allow importing
imageio from the cloned repository. See the file ``imageio.proxy.py`` for
details.

Further imageio has the following dev-dependencies:

``pip install black flake8 pytest pytest-cov sphinx numpydoc``
