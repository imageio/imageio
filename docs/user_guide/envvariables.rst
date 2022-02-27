Imageio environment variables
=============================

This page lists the environment variables that imageio uses. You can
set these to control some of imageio's behavior. Each operating system
has its own way for setting environment variables, but to set a variable
for the current Python process use
``os.environ['IMAGEIO_VAR_NAME'] = 'value'``.

* ``IMAGEIO_NO_INTERNET``: If this value is "1", "yes", or "true" (case
  insensitive), makes imageio not use the internet connection to
  retrieve files (like libraries or sample data). Some plugins (e.g.
  freeimage and ffmpeg) will try to use the system version in this case.
* ``IMAGEIO_FFMPEG_EXE``: Set the path to the ffmpeg executable. Set
  to simply "ffmpeg" to use your system ffmpeg executable.
* ``IMAGEIO_FREEIMAGE_LIB``: Set the path to the freeimage library. If
  not given, will prompt user to download the freeimage library.
* ``IMAGEIO_FORMAT_ORDER``: Determine format preference. E.g. setting this
  to ``"TIFF, -FI"`` will prefer the FreeImage plugin over the Pillow plugin,
  but still prefer TIFF over that. Also see the ``formats.sort()`` method.
* ``IMAGEIO_REQUEST_TIMEOUT``: Set the timeout of http/ftp request in seconds.
  If not set, this defaults to 5 seconds.
* ``IMAGEIO_USERDIR``: Set the path to the default user directory. If not
  given, imageio will try ``~`` and if that's not available ``/var/tmp``.
