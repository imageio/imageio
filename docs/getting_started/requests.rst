ImageResources
==============

Reading images isn't always limited to simply loading a file from a local disk.
Maybe you are writing a web application and your want to read images from HTTP,
or your images are already in memory as a BytesIO object. Maybe you are doing
machine learning and decided that it is smart to compress your images inside a
ZIP file to reduce the IO bottleneck. All these are examples of different
places where image data is stored (aka. resources). 

ImageIO supports reading (and writing where applicable) for all of the above
examples and more. To stay organized, we group all these sources/resources
together and call them ``ImageResource``. Often ImageResources are expressed as
URIs though sometimes (e.g., in the case of byte streams) they can be python
objects, too.

Here, you can find the documentation on what kind of ImageResources ImageIO
currently supports together with documentation and an example on how to
read/write them.


Files
-----

Arguably the most common type of resource. You specify it using the path to the
file, e.g. ::

    img = iio.imread("path/to/my/image.jpg")  # relative path
    img = iio.imread("/path/to/my/image.jpg")  # absolute path on Linux
    img = iio.imread("C:\\path\\to\\my\\image.jpg")  # absolute path on Windows


Notice that this is a convenience shorthand (since it is so common).
Alternatively, you can use the full URI to the resource on your disk ::

    img = iio.imread("file://path/to/my/image.jpg")
    img = iio.imread("file:///path/to/my/image.jpg")
    img = iio.imread("file://C:\\path\\to\\my\\image.jpg")


Byte Streams
------------

ImageIO can directly handle (binary) file objects. This includes ``BytesIO`` objects (and subclasses thereof)
as well as generic objects that implement ``close`` and a ``read`` and/or ``write`` function.
Simply pass them into ImageIO the same way you would pass a URI::

    file_handle = open("some/image.jpg", "rb")
    img = iio.imread(file_handle)


Standard Images
---------------

Standard images are a curated dataset of pictures in different formats that you
can use to test your pipelines. You can access them via the ``imageio`` scheme
::

    img = iio.imread("imageio://chelsea.png")

A list of all currently available standard images can be found in the section on
:doc:`Standard Images <standardimages>`.


Web Servers (http/https)
------------------------

.. note::
    This is primarily intended for publically available ImageResources. If your
    server requires authentication, you will have to download the ImageResource
    yourself before handing it over to ImageIO.


Reading http and https is provided directly by ImageIO. This means that ImageIO
takes care of requesting and (if necessary) downloading the image and then hands
the image to a compatible backend to do the reading itself. It works with any
backend. If the backend supports file objects directly, this processes will
happen purely in memory.

You can read from public web servers using a URL string ::

    img = iio.imread("https://my-domain.com/path/to/some/image.gif")


File Servers (ftp/ftps)
-----------------------

.. note::
    This is primarily intended for publically available ImageResources. If your
    server requires authentication, you will have to download the ImageResource
    yourself before handing it over to ImageIO.


Reading ftp and ftps is provided directly by ImageIO following the same logic as
reading from web servers::

    img = iio.imread("ftp://my-domain.com/path/to/some/image.gif")


Webcam
------

.. note::
    To access your webcam you will need to have the ffmpeg backend installed::

        pip install imageio[ffmpeg]

With ImageIO you can directly read images (frame-by-frame) from a webcam that is
connected to the computer. To do this, you can use the special target::

    img = iio.imread("<video0>")

If you have multiple video sources, you can replace the ``0`` with the
respective number, e.g::

    img = iio.imread("<video2>")

If you need many frames, e.g., because you want to process a stream, it is often
much more performant to open the webcam once, keep it open, and read frames
on-demand. You can find an example of this in the :doc:`list of examples
<../examples>`.

Screenshots
-----------

.. note::
    Taking screenshots are only supported on Windows and Mac.

ImageIO gives you basic support for taking screenshots via the special target
``screen``::

    img = iio.imread("<screen>")


Clipboard
---------

.. note::
    reading from clipboard is only supported on Windows.

ImageIO gives you basic support for reading from your main clipboard via the special
target ``clipboard``::

    img = iio.imread("<clipboard>")


ZIP Archives
------------

You can directly read ImageResources from within ZIP archives without extracting them. For 
this purpose ZIP archives are treated as normal folders; however, nested zip archives are not
supported::

    img = iio.imread("path/to/file.zip/abspath/inside/zipfile/to/image.png")

Note that in a future version of ImageIO the syntax for reading ZIP archives will be updated
to use fragments, i.e., the path inside the zip file will become a URI fragment.
