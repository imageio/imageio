=======================
Developer documentation
=======================

.. toctree::
  :maxdepth: 2
  
  Developer API <devapi>
  Writing plugins <plugins>


Developer Installation
----------------------

For developers, we provide a simple mechanism to allow importing
imageio from the cloned repository <https://github.com/imageio/imageio.git>.
See the file ``imageio.proxy.py`` for details.

Further imageio has the following dev-dependencies:

``pip install black flake8 pytest pytest-cov sphinx numpydoc``