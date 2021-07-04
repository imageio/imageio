ImageResources
==============

Reading images isn't always limited to simply loading a file from a local disk.
Maybe you are writing a web application and your want to read images from HTTP,
or your images are already in memory as a BytesIO object. Maybe you are doing
machine learning and decided that it is smart to compress your images inside a
ZIP file to reduce the IO bottleneck. All these are examples of different
places where image data is stored (aka. resource). 

ImageIO supports reading (and writing where applicable) for all the above
examples and more. To stay organized, we group all these sources/resources
together and call them ``ImageResource``. Often ImageResources are expressed
as URIs though sometimes (e.g., if they are streams) they can be python objects,
too.

Here, you can find the documentation on what kind of ImageResources ImageIO
currently supports together with documentation and an example on how to
read/write them.


Files
-----

Arguably the most common type of resource. You specify it using the path to the
file, e.g. ::

    img = iio.imread("path/to/my/image.jpg")

Notice that this is a convenience shorthand (since it is so common).
Alternatively, you can use the full URI to the resource on your disk ::

    img = iio.imread("file://path/to/my/image.jpg")


Standard Images
---------------

Standard images are a curated dataset of pictures in different formats that you can use to test
your pipelines. You can access them via the ``imageio`` scheme ::

    img = iio.imread("imageio://chelsea.png")

A list of all currently available standard images can be found in the section on :doc:`Standard Images <standardimages>`.

TODO: Write prose on what request types (files, objects, http, ...) are supported.