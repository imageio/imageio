-------------
Release notes
-------------


Planned
=======

* Improved handling and support for meta data.


Version 2.8.0 (TBD)
==========================

(skipping version 2.7 to avoid confusion with Python v2.7.)

This release drops support for Python 2.7 and Python 3.4.


Version 2.6.0 (07-10-2019)
==========================

This will likely be the last release to support Python 2.7.

Fixes:

* Fixed a security vulnerability for Windows users that have dcmtk installed,
  and where an attacker can set the filename.
* Fixed bug in ``image_as_uint`` (#451 by clintg6).
* Fix that only one webcam could be used when two cameras are connected that have the same name.
* Prevent paletted image with transparency to be converted to grayscale.

Improvements:

* Optimise 16-bit PNG write performance for newer versions of Pillow (#440 by Ariel Ladegaard).
* More flexible setting of memory limit in ``mimread`` and ``mvolread`` (#442 by Chris Barnes).
* Support for ASCII PNM files (#447 by Tobias Baumann).
* Improved support for JPEG2000 (can now provide parameters) (#456 by Pawel Korus).
* Added support for compressed FITS images (#458 by Joe Singleton).
* Improve imageio import time by avoiding pkg_resources import (#462 by Mark Harfouche).
* Added example for compressing GIFs using pygifsicle (#481 by Luca Cappelletti).


Version 2.5.0 (06-02-2019)
==========================

The ffmpeg plugin has been refactored:

* The core has been moved to a new library: imageio-ffmpeg.
* That library provides platform-specific wheels that includes ffmpeg,
  so just ``pip install imageio-ffmpeg`` instead of the download step.
* Note that this new library is py3k only.
* Termination of ffmpeg subprocess is now more reliable.
* The reader of the ffmpeg plugin now always reports ``inf`` as the number of
  frames. Use ``reader.count_frames()`` to get the actual number, or estimate
  it from the fps and duration in the meta data.
* Removed ``CannotReadFrameError``.

Other changes:
    
* The avbin plugin has been depreacted and will be removed in a future version.
* Imnproved speed for PIL and FFMPEG plugsins by avoiding memory copies.
* Update the included tiffile library.
* Support for SimpleITK.
* Speed up tiffile plugin when writing to something else than a filename.
* Fix that writing to a file object would not work for some plugins.
* Can now pass image data to the write functions as anything that resolves to
  a numpy array with a numeric dtype.
* One can now read from a memoryview.
* Fix error related to paletted BMP with the Pillow plugin.
* Improved logging.


Version 2.4.1 (06-09-2018)
==========================

* Fix installation issue on flavors of Ubuntu 14.04 /w Python 2.7  (#378).
* Use `np.frombuffer` instead of `np.fromstring` in some cases.


Version 2.4.0 (06-09-2018)
==========================

* Renamed ``Image`` class to ``Array`` and add documentation for this ndarray subclass.
* Reading from HTTP and zipfiles has been improved and better documented.
* Improvements to reading and writing of Tiff metadata (by Lukas Schrangl).
* Better dealing of tifffile dependencies on Python 2.7 (#330 and #337 by Chris Barnes).
* Reader for the SPE format (#358 by lschr).
* Better termination of FFMPEG when reading from webcam (#346 by Dennis Vang).
* FFMPEG support for reading 16bit videos (#342 by Peter Minin).


Version 2.3.0 (20-03-2018)
==========================

* Console entry points for binary downloads (by Paul Mueller).
* Dropped support for Python 2.6, 3.2 and 3.3.
* Reading images from a url can now also have "suffixes" like "?query=foo".
* The ``mimwrite()`` and ``mvolwrite()`` functions also work with generators.
* Fix rounding of float data.
* New Lytro plugin (by Maximilian Schambach).
* New plugin based on BSDF format (for images/volumes and series thereof,
  including support for random access and streaming).
* TIFFFILE update to latest ``tifffile.py`` implementation.
* DICOM fix that could fail in the presence of a directory.
* PILLOW improvements to API to provide same functionality as Scipy's ``imread()``.
* PILLOW fix for Gamma correction (#302).
* PILLOW now allows JPEG images to be read from a url.
* PILLOW fix determining of grayscale in 1 bit paletted images.
* FFMPEG improved device name parsing (by Dennis van Gerwen).
* FFMPEG now allows more control of position of extra parameters.
* FFMPEG improved parsing of fps from ffmpeg info.
* FFMPEG reader allows has ``fps`` argument to force reading at a specific FPS.


Version 2.2.0 (25-05-2017)
==========================

* New format for grabbing screenshots (for Windows and OS X).
* New format for grabbing image data from clipboard (Window only).
* Multipage Tiff files can now be read using ``volread()`` to obtain the image
  data as one array.
* Updated the ffmpeg executables that imageio provides.
* The ffmpeg format can now also use the ffmpeg exe provided by the ffmpeg
  conda package (``conda install ffmpeg -c conda-forge``).
* Fixes to ffmpeg format in general.
* Improve docs and rounding in animated GIF duration.
* Fix for setting number of loops in animated GIF.
* Fixes for transparent images in Pillow.
* Fixes for float indexing that is disallowed in new Numpy (Freeimage plugin).
* Fix for using missing ``close()`` on Pillow images.
* Updated version of tiffile plugin.


Version 2.1.2 (02-02-2017)
==========================

A bugfix release:

* Fix animated gif writer that was broken in newer Pillow version.
* FFMPEG plugin improvements: more reliable fps detection, can deal
  with missing FPS, more reliable subprocess termination,
* Mimread allows a few missing frames to better deal with certain video files.
* Allow question marks in url's.
* Allow Pillow plugin to read remote files by "enabling" ``seek()`` and ``tell()``.
* Use invoke to run development tasks instead of custom "make" module.


Version 2.1.1 (24-12-2016)
==========================

Minor improvements related to Debian packaging.


Version 2.1 (22-12-2016)
========================

* Standard images now have to be specified using e.g.
  ``imageio.imread('imageio:chelsea.png')`` to be more explicit about being
  a special case and potentially involving a download.
* Improvements and fixes for the ffmpeg plugin (including improved seeking).
* Several tweaks to the tests and setup script to make it pass the Debian
  build system.


Version 2.0 (10-12-2016)
========================

This release introduces a new plugin based on Pillow, which will take care of
the "common formats" like PNG and JPEG, which was previously the role of the
FreeImage plugin. The latter is still available but the FreeImage library
is no longer distributed by default.

* New Pillow plugin to privide the common formats.
* FreeImage plugin gets lower priority w.r.t. resolving a format.
* No more automatic downloading of libraries and executable (for
  FreeImage, FFMPEG and AVBIN plugins).
* Pillow plugin comes with a format to read/write animated GIF to supersede
  the one provided by FreeImage.
* Various improvements/fixes to the ffmpeg plugin.
* Fixes and improvements of the DICOM plugin.
* Better support of exr images via FreeImage (by Joel Nises).
* New FEI format (for images produced by the FEI SEM microscope).


Version 1.6 (19-09-2016)
========================

* Got rid of Lena image because it can be regarded offensive and is not (explicitly) publicly licensed.
* Fix issue with ffmpeg reader being slow on particular systems (#152).
* Tiff plugin updated.
* Add Tiff resolution support (Antony Lee).
* Support for 16bit PNG's (#150, by OrganicIrradiation).
* Fixes to ffmpeg plugin (#149, #145, #129).
* Fix in using IMAGEIO_FREEIMAGE_LIB (#141, by Radomirs Cirskis)
* Better ffmpeg verbosity and exe detection ( #138, #139, by Tim D. Smith).


Version 1.5 (31-01-2016)
========================

* Freeimage conda package (in main channel) is updated and works on all
  major OS's.
* Conda install imageio!
* Fix bug where the ffmpeg plugin fails on certain video files (#131).
* Fix how dicom uses dcmtk for JPEG compressed files.


Version 1.4 (18-11-2015)
========================

* Various improvements to the ffmpeg plugin.
* New tiffile plugin that should support most scientific formats.
* New simpleITK wrapper plugin.
* New gdal plugin.
* Freeimage plugin can load freeimage lib provided by conda.
* Dicom plugin improved handling of compressed files.
* Most plugins adopt lazy loading to keep imageio lean, fast, and scalable.
* We now build wheels for Pypi.
* Travis also tests Python 3.5.


Version 1.3 (02-07-2015)
========================

This release features several fixes and small improvements, especially
to the ffmpeg plugin.

* Fix 'FrameTime' in first frame of GIF image (#90)
* Fix that writing video could freeze on Windows (#84)
* Fix that ffmpeg process was sometimes not closed correctly (#79)
* Also protect user from clogging the machine for mvolread (#89)
* Better support for platforms other than Win/Linux/OSX (#87 )
* Support for reading from webcam on OSX (#83, #85)
* Support for dpx via the ffmpeg plugin (#81)
* Support for wmv via the ffmpeg plugin (#83)
* The ffmpeg plugin allows specifying pixelformat. The new default is
  more widely supported (#83)
* Allow passing additional arguments to ffmpeg command (#83)
* Quality of ffmpeg output now set via quality param instead of bitrate (#83)
* Imageio now has a few (documented) environment variables to specify
  the locations of plugin libraries/exes (thus preventing them from
  being automatically downloaded.


Version 1.2 (23-02-2015)
========================

Basically a hotfix release. But some new features were introduced.

* Fixed that pip-installing would put README.md and other files in sys.prefix.
* The used ffmpeg exe can be overridden with an environment variable 
  'IMAGEIO_FFMPEG_EXE'.
* Relative paths work again.
* FFMPEG plugin moved to correct timeframe when seeking (thanks Zulko)


Version 1.1 (04-02-2015)
========================

Imageio is now a dependency of `Moviepy <https://github.com/Zulko/moviepy/>`_, 
which exposed a few issues to fix. Imageio is now also available as a
Debian package (thanks Ghislain!). Furher, we tweaked our function names
to be cleared and more consistent (the old names still work).

* All ``Xsave()`` functions are renamed to ``Xwrite()``. 
  Also ``read()`` and ``save()`` are now ``get_reader()`` and ``get_writer()``.
  The old names are available as aliases (and will be for the foreseable
  future) for backward compatibility.
* Protect user from bringing computer in swap-mode by doing e.g.
  ``mimread('hunger games.avi')``.
* Continuous integration for Windows via Appveyor.
* All imports are relative, so imageio can be used as a subpackage in
  a larger project.
* FFMPEG is the default plugin for reading video (since AVBIN has issues).
* Better handling on NaN and Inf when converting to uint8.
* Provide dist packages that include freeimage lib and a few example images.
* Several changes to ease building into Debian package.
* Fixed segfault when saving gif 
  (thanks levskaya, https://github.com/imageio/imageio/pull/53).
* Don't fail when userdir is not writable.
* Gif plugin writer has fps param for consistency with avi/mp4 etc.


Version 1.0 (13-11-2014)
========================

In this release we did a lot of work to push imageio to a new level.
The code is now properly tested, and we have several more formats.

The big changes:

* Many unit tests were written to cover over 95% of the code base.
  (the core of imageio has 100% coverage).
* Setup continuous integration (CI) using Travis.
* Imageio now follows PEP8 style guides (and this is tested with CI).
* Refactoring of the code base. Resulting in a cleaner namespace.
* Many improvements to the documementation.

Plugins:

* The FFMPEG format is now well supported. Binaries are provided.
* New AVBIN format for more efficient reading of video files.
* New NPZ format that can store (a series of) arbitrarily shaped numpy arrays.
* New SWF format (shockwave flash) for lossless animated images.
* Improvements to the GIF format. The GIF and ANIGIF formats are now merged.

Further:

* New simple website to act as a front page (http://imageio.github.io).
* Compatibility with Pypy.
* We provide a range of :doc:`standard images <standardimages>` that are 
  automatically downloaded.
* Binaries (libs and executables) that plugins of imageio uses are now
  downloaded at runtime, not at build/install time. This simplifies
  things a lot.
* freeimage plugin now fully functional on pypy
* Added utilities for developers (run ``python make`` from the repo root).
* PNG, JPEG, BMP,GIF and other plugins can now handle float data (pixel
  values are assumed to be between 0 and 1.
* Imageio now expand the user dir when filename start with '~/'.
* Many improvements and fixes overall.


Version 0.5.1 (23-06-2014)
==========================

* DICOM reader closes file after reading pixel data 
  (avoid too-many-open-files error)
* Support for video data (import and export) via ffmpeg
* Read images from usb camera via ffmpeg (experimental)


Version 0.4.1 (26-10-2013)
==========================

* We moved to github!
* Raise error if URI could not be understood.
* Small improvement for better error reporting.
* FIxes in mvolread and DICOM plugin


Version 0.4 (27-03-2013)
========================

Some more thorough testing resulted in several fixes and improvements over
the last release.

* Fixes to reading of meta data in freeimage plugin which could
  cause errors when reading a file.
* Support for reading 4 bpp images.
* The color table for index images is now applied to yield an RGBA image.
* Basic support for Pypy.
* Better __repr__ for the Image class.


Version 0.3.2
=============

* Fix in dicom reader (RescaleSlope and RescaleIntercept were not found)
* Fixed that progress indicator made things slow


Version 0.3.1
=============

* Fix installation/distribution issue.


Version 0.3.0
=============

This was a long haul. Implemented several plugins for animation and
volumetric data to give an idea of what sort of API's work and which 
do not. 

* Refactored for more conventional package layout 
  (but importing without installing still supported)
* Put Reader and Writer classes in the namespace of the format. This
  makes a format a unified whole, and gets rid of the
  _get_reader_class and _get_write_class methods (at the cost of
  some extra indentation).
* Refactored Reader and Writer classes to come up with a better API
  for both users as plugins.
* The Request class acts as a smart bridging object. Therefore all
  plugins can now read from a zipfile, http/ftp, and bytes. And they
  don't have to do a thing.
* Implemented specific BMP, JPEG, PNG, GIF, ICON formats.
* Implemented animated gif plugin (based on freeimage).
* Implemented standalone DICOM plugin.


Version 0.2.3
=============

* Fixed issue 2 (fail at instal, introduced when implementing freezing)


Version 0.2.2
=============

* Improved documentation.
* Worked on distribution.
* Freezing should work now.


Version 0.2.1
=============

* Introduction of the imageio.help function.
* Wrote a lot of documentation.
* Added example (dummy) plugin.


Version 0.2
===========

* New plugin system implemented after discussions in group.
* Access to format information.


Version 0.1
===========

* First version with a preliminary plugin system.
