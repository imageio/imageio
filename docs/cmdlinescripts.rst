Imageio command line scripts
============================

This page lists the command line scripts provided by imageio. To see
all options for a script, execute it with the ``--help`` option, e.g.
``imageio_download_bin --help``.

* ``imageio_download_bin``: Download binary dependencies for imageio
  plugins to the users application data directory. This script accepts
  the parameter ``--package-dir`` which will download the binaries to
  the directory where imageio is installed. This option is useful when
  freezing an application with imageio. It is supported out-of-the-box
  by PyInstaller version>=3.2.2.
* ``imageio_remove_bin``: Remove binary dependencies of imageio
  plugins from all directories managed by imageio. This script is
  useful when there is a corrupt binary or when the user prefers the
  system binary over the binary provided by imageio. 
