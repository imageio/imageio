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
imageio from the cloned repository <https://github.com/imageio/imageio.git>::

    git clone https://github.com/imageio/imageio.git
    cd imageio
    pip install -e .[dev]
