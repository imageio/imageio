Bird's eye view on ImageIO
==========================

The aim of this page is to give you a high level overview of how ImageIO works
under the hood. We think this is useful for two reasons: 

#.  If something doesn't work as it should, you need to know where to search for
    causes. The overview on this page aims to help you in this regard by giving you
    an idea of how things work, and - hence - where things may go sideways. 
#.  If you do find a bug and decide to report it, this page helps us establish
    some joint vocabulary so that we can quickly get onto the same page, figure out
    what's broken, and how to fix it.


Terminology
-----------

You can think of ImageIO in three parts that work in sequence in order to load
an image.

ImageIO Core 
    The user-facing APIs (legacy + v3) and a plugin manager. You
    send requests to iio.core and it uses a set of plugins (see below) to figure out
    which backend (see below) to use to fulfill your request. It does so by directly
    sending the request to the plugin you specified or by (intelligently) searching
    all plugins if you didn't specify one explicitly.

Plugin
    A backend-facing adapter/wrapper that responds to a request from
    iio.core. It can convert a request that comes from iio.core into a sequence of
    instructions for the backend that fullfill the request (eg., read/write/iter). A
    plugin is also aware if its backend is or isn't installed and handles this case
    appropriately, e.g., it deactivates itself if the backend isn't present.

Backend 
    A (potentially 3d party) library that can read and/or write
    images or image-like objects (videos, etc.). Every backend is optional, so it is
    up to you to decide which backends to install depending on your needs. Examples
    for backends are pillow, tifffile, or ffmpeg.


Issues
------

In this repo, we maintain iio.core as well as all the plugins. So, if you find a
bug or have a plroblem with either the core or any plugin, please open a new
issue `here <https://github.com/imageio/imageio/issues>`_.

If you find a bug or have problems with a specific backend, e.g. reading is very
slow, please file an issue upstream (the place where the backend is maintained).
When in doubt, you can always ask us, and we will redirect you appropriately.


New Plugins
-----------

If you end up writing a new plugin, we very much welcome you to contribute it
back to us so that we can offer as expansive a list of backends and supported
formats as possible. In return, we help you maintain the plugin - note: a plugin is
typically different from the backend - and make sure that changes to ImageIO
don't break your plugin. This we can only guarantee if it is part of the
codebase, because we can (a) write unit tests for it and (b) update your plugin
to take advantage of new features. That said, we generally try to be
backward-compatible whenever possible.

The backend itself will live elsewhere, usually in a different repository. This
keeps things lightweight yet powerful. Often backends are already actively
maintained elsewhere, and depending on that is gives us access to the latest
features and bug fixes.
