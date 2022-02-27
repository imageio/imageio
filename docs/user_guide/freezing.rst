Freezing ImageIO
=======================

ImageIO has wide-ranging platform support, and to achieve this we now lazy-load
plugins. Most users only use a few plugins (1 or 2), so lazy-loading helps
mitigate a combinatoric explosion of interactions. ImageIO's lazy loading is an
interesting case as (1) these plugins are exactly the kind of thing that
PyInstaller_ tries desperately to avoid collecting to minimize package size and
(2) these plugins are super lightweight and won't bloat the package. 

A simple workaround that is to add a command line switch when calling
pyinstaller that will gather all plugins:

.. code-block::

  pyinstaller --collect-submodules imageio <entry_script.py>

Alternatively, if you really want to limit the plugins used:

.. code-block::

  pyinstaller --hidden-import imageio.plugins.<plugin> <entry_script.py>

Plugins that make use of external programs (like ffmpeg) will need to take
extra steps to include necessary binaries_.

.. _PyInstaller: https://pyinstaller.readthedocs.io/en/stable/

.. _binaries: https://pyinstaller.readthedocs.io/en/stable/usage.html#cmdoption-add-binary
