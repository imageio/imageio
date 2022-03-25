Freezing ImageIO
================

.. note::
    Starting with ``pyinstaller-hooks-contrib==2022.3`` pyinstaller will
    automatically include any ImageIO plugins that are installed in your
    environment. The techniques described here target earlier versions.

When freezing ImageIO you need to make sure that you are collecting the plugins
you need in addition to the core library. This will not happen automagically,
because plugins are lazy-loaded upon first use for better platform support and
reduced loading times. This lazy-loading is an interesting case as (1) these
plugins are exactly the kind of thing that PyInstaller_ tries desperately to
avoid collecting to minimize package size and (2) these plugins are - by
themself - super lightweight and won't bloat the package. 

To add plugins to the application your first option is to add all of imageio to
your package, which will also include the plugins. This can be done by using a
command-line switch when calling pyinstaller that will gather all plugins:

.. code-block::

    pyinstaller --collect-submodules imageio <entry_script.py>

Note that it is generally recommended to do this from within a virtual
environment in which you don't have unnecessary backends installed. Otherwise,
any backend that is present will be included in the package and, if it is not
being used, may increase package size unnecessarily.

Alternatively, if you want to limit the plugins used, you can include them
individually using ``--hidden-import``:

.. code-block::

    pyinstaller --hidden-import imageio.plugins.<plugin> <entry_script.py>

In addition, some plugins (e.g., ffmpeg) make use of external programs, and for
these, you will need to take extra steps to also include necessary binaries_. If
you can't make it work, feel free to submit a `new issue
<https://github.com/imageio/imageio/issues>`_, so that we can see how to improve
this documentation further.

.. _PyInstaller: https://pyinstaller.readthedocs.io/en/stable/

.. _binaries: https://pyinstaller.readthedocs.io/en/stable/usage.html#cmdoption-add-binary
