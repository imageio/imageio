Imageio environment variables
=============================

This page lists the environment variables that imageio uses. You can
set these to control some of imageio's behavior. Each operating system
has its own way for setting environment variables, but to set a variable
for the current Python process use
``os.environ['IMAGEIO_VAR_NAME'] = 'value'``.

* ``IMAGEIO_NO_INTERNET``: Makes imageio not use the internet connection to
  retrieve files (like libraries or sample data). Some plugins (e.g.
  freeimage and ffmpeg) will try to use the system version in this case.
* ``IMAGEIO_FFMPEG_EXE``: Set the ffmpeg executable. Set to simply
  "ffmpeg" to use your system ffmpeg executable.
