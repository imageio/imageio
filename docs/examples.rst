Imageio Usage Examples
======================

Some of these examples use Visvis to visualize the image data,
but one can also use Matplotlib to show the images.

Imageio provides a range of :doc:`example images <getting_started/standardimages>`,
which can be used by using a URI like ``'imageio:chelsea.png'``. The images
are automatically downloaded if not already present on your system.
Therefore most examples below should just work.


Read an image of a cat
----------------------

Probably the most important thing you'll ever need.

.. code-block:: python

    import imageio as iio

    im = iio.imread('imageio:chelsea.png')
    print(im.shape)
    
If the image is a GIF:

.. code-block:: python

    import imageio as iio
    
    im = iio.get_reader('cat.gif')
    for frame in im:
        print(frame.shape)  # Each frame is a numpy matrix
    
If the GIF is stored in memory:

.. code-block:: python

    import imageio as iio
    
    im = iio.get_reader(image_bytes, '.gif')
    

Read from fancy sources
-----------------------

Imageio can read from filenames, file objects, http, zipfiles and bytes.

.. code-block:: python

    import imageio as iio
    import visvis as vv

    im = iio.imread('http://upload.wikimedia.org/wikipedia/commons/d/de/Wikipedia_Logo_1.0.png')
    vv.imshow(im)

Note: reading from HTTP and zipfiles works for many formats including png and jpeg, but may not work
for all formats (some plugins "seek" the file object, which HTTP/zip streams do not support).
In such a case one can download/extract the file first. For HTTP one can use something like
``imageio.imread(imageio.core.urlopen(url).read(), '.gif')``.

Read all Images in a Folder
---------------------------

One common scenario is that you want to read all images in a folder, e.g. for a scientific analysis, or
because these are all your training examples. Assuming the folder only contains image files, you can
read it using a snippet like

.. code-block:: python

    import imageio as iio
    from pathlib import Path

    images = list()
    for file in Path("path/to/folder").iterdir():
        im = iio.imread(file)
        images.append(im)


Iterate over frames in a movie
------------------------------

.. code-block:: python

    import imageio as iio

    reader = iio.get_reader('imageio:cockatoo.mp4')
    for i, im in enumerate(reader):
        print('Mean of frame %i is %1.1f' % (i, im.mean()))


Grab screenshot or image from the clipboard
-------------------------------------------

(Screenshots are supported on Windows and OS X, clipboard on Windows only.)

.. code-block:: python

    import imageio as iio

    im_screen = iio.imread('<screen>')
    im_clipboard = iio.imread('<clipboard>')


Grab frames from your webcam
----------------------------

Use the special ``<video0>`` uri to read frames from your webcam (via
the ffmpeg plugin). You can replace the zero with another index in case
you have multiple cameras attached. You need to ``pip install imageio-ffmpeg``
in order to use this plugin.

.. code-block:: python

    import imageio as iio
    import visvis as vv

    reader = iio.get_reader('<video0>')
    t = vv.imshow(reader.get_next_data(), clim=(0, 255))
    for im in reader:
        vv.processEvents()
        t.SetData(im)


Convert a movie
------------------------------

Here we take a movie and convert it to gray colors. Of course, you
can apply any kind of (image) processing to the image here ...
You need to ``pip install imageio-ffmpeg`` in order to use the ffmpeg plugin.

.. code-block:: python

    import imageio as iio

    reader = iio.get_reader('imageio:cockatoo.mp4')
    fps = reader.get_meta_data()['fps']

    writer = iio.get_writer('~/cockatoo_gray.mp4', fps=fps)

    for im in reader:
        writer.append_data(im[:, :, 1])
    writer.close()



Read medical data (DICOM)
-------------------------

.. code-block:: python

    import imageio as iio
    dirname = 'path/to/dicom/files'

    # Read as loose images
    ims = iio.mimread(dirname, 'DICOM')
    # Read as volume
    vol = iio.volread(dirname, 'DICOM')
    # Read multiple volumes (multiple DICOM series)
    vols = iio.mvolread(dirname, 'DICOM')


Volume data
-----------

.. code-block:: python

    import imageio as iio
    import visvis as vv

    vol = iio.volread('imageio:stent.npz')
    vv.volshow(vol)


Writing videos with FFMPEG and vaapi
------------------------------------
Using vaapi (on Linux only) (intel only?) can help free up resources on
your laptop while you are encoding videos. One notable
difference between vaapi and x264 is that vaapi doesn't support the color
format yuv420p.

Note, you will need ffmpeg compiled with vaapi for this to work.

.. code-block:: python

    import imageio as iio
    import numpy as np

    # All images must be of the same size
    image1 = np.stack([imageio.imread('imageio:camera.png')] * 3, 2)
    image2 = iio.imread('imageio:astronaut.png')
    image3 = iio.imread('imageio:immunohistochemistry.png')

    w = iio.get_writer('my_video.mp4', format='FFMPEG', mode='I', fps=1,
                           codec='h264_vaapi',
                           output_params=['-vaapi_device',
                                          '/dev/dri/renderD128',
                                          '-vf',
                                          'format=gray|nv12,hwupload'],
                           pixelformat='vaapi_vld')
    w.append_data(image1)
    w.append_data(image2)
    w.append_data(image3)
    w.close()

A little bit of explanation:

  * ``output_params``
  
    * ``vaapi_device`` speficifies the encoding device that will be used.
    * ``vf`` and ``format`` tell ffmpeg that it must upload to the dedicated
      hardware. Since vaapi only supports a subset of color formats, we ensure
      that the video is in either gray or nv12 before uploading it. The ``or``
      operation is achieved with ``|``.

  * ``pixelformat``: set to ``'vaapi_vld'`` to avoid a warning in ffmpeg.
  * ``codec``: the code you wish to use to encode the video. Make sure your
    hardware supports the chosen codec. If your hardware supports h265, you
    may be able to encode using ``'hevc_vaapi'``
    

Writing to Bytes (Encoding)
---------------------------

You can convert ndimages into byte strings. For this, you have to explicitly
specify the desired format, as a byte string doesn't carry any information about
the format or color space to use. Since backends differ in the way this
information should be provided, you also have to explicitly specify the backend
(plugin) to use. Note that, if the backend supports writing to file-like
objects, the entire process will happen without touching your file-system. If
you, for example, want to write with pillow, you can use:

.. code-block:: python

    from imageio import v3 as iio

    # load an example image
    img = iio.imread('imageio:astronaut.png')

    # png-encoded bytes string
    # Note: defaults to RGB color space
    png_encoded = iio.imwrite("<bytes>", img, plugin="pillow", format="PNG")
    
    # jpg-encoded bytes string
    # Note: defaults to RGB color space
    jpg_encoded = iio.imwrite("<bytes>", img, plugin="pillow", format="JPEG")

    # RGBA bytes string
    # Important Note: omitting mode="RGBA" would result in a corrupted byte string
    img = iio.imread('imageio:astronaut.png', mode="RGBA")
    jpg_encoded = iio.imwrite("<bytes>", img, plugin="pillow", format="JPEG", mode="RGBA")

Writing to BytesIO
------------------

Similar to writing to byte strings, you can also write to BytesIO directly.

.. code-block:: python

    from imageio import v3 as iio
    import io

    # load an example image
    img = iio.imread('imageio:astronaut.png')

    # write as PNG
    output = io.BytesIO()
    iio.imwrite(output, img, plugin="pillow", format="PNG")
    
    # write as JPG
    output = io.BytesIO()
    iio.imwrite(output, img, plugin="pillow", format="JPEG")

Optimizing a GIF using pygifsicle
------------------------------------
When creating a `GIF <https://it.wikipedia.org/wiki/Graphics_Interchange_Format>`_
using `imageio <https://imageio.readthedocs.io/en/stable/>`_ the resulting images
can get quite heavy, as the created GIF is not optimized.
This can be useful when the elaboration process for the GIF is not finished yet
(for instance if some elaboration on specific frames stills need to happen),
but it can be an issue when the process is finished and the GIF is unexpectedly big.

GIF files can be compressed in several ways, the most common one method
(the one used here) is saving just the differences between the following frames.
In this example, we apply the described method to a given GIF `my_gif` using
`pygifsicle <https://github.com/LucaCappelletti94/pygifsicle>`_, a porting
of the general-purpose GIF editing command-line library
`gifsicle <https://www.lcdf.org/gifsicle/>`_. To install pygifsicle and gifsicle,
`read the setup on the project page <https://github.com/LucaCappelletti94/pygifsicle>`_:
it boils down to installing the package using pip and following
the console instructions:

.. code-block:: shell

    pip install pygifsicle

Now, let's start by creating a gif using imageio:

.. code-block:: python

    import imageio as iio
    import matplotlib.pyplot as plt
    
    n = 100
    gif_path = "test.gif"
    frames_path = "{i}.jpg"
    
    n = 100
    plt.figure(figsize=(4,4))
    for i, x in enumerate(range(n)):
        plt.scatter(x/n, x/n)
        plt.xlim(0, 1)
        plt.ylim(0, 1)
        plt.savefig("{i}.jpg".format(i=i))
        
    with iio.get_writer(gif_path, mode='I') as writer:
        for i in range(n):
            writer.append_data(iio.imread(frames_path.format(i=i)))
            
This way we obtain a 2.5MB gif.

We now want to compress the created GIF.
We can either overwrite the initial one or create a new optimized one:
We start by importing the library method:

.. code-block:: python

    from pygifsicle import optimize
    
    optimize(gif_path, "optimized.gif") # For creating a new one
    optimize(gif_path) # For overwriting the original one
   
The new optimized GIF now weights 870KB, almost 3 times less.

Putting everything together:

.. code-block:: python

    import imageio as iio
    import matplotlib.pyplot as plt
    from pygifsicle import optimize
    
    n = 100
    gif_path = "test.gif"
    frames_path = "{i}.jpg"
    
    n = 100
    plt.figure(figsize=(4,4))
    for i, x in enumerate(range(n)):
        plt.scatter(x/n, x/n)
        plt.xlim(0, 1)
        plt.ylim(0, 1)
        plt.savefig("{i}.jpg".format(i=i))
        
    with iio.get_writer(gif_path, mode='I') as writer:
        for i in range(n):
            writer.append_data(iio.imread(frames_path.format(i=i)))
            
    optimize(gif_path)

Reading Images from ZIP archives
--------------------------------

.. note::

    In the future, this syntax will change to better match the URI
    standard by using fragments. The updated syntax will be 
    ``"Path/to/file.zip#path/inside/zip/to/image.png"``.

.. code-block:: python

    import imageio as iio

    image = iio.imread("Path/to/file.zip/path/inside/zip/to/image.png")




Reading Multiple Files from a ZIP archive
-----------------------------------------

Assuming there is only image files in the ZIP archive, you can iterate
over them with a simple script like the one below.

.. code-block:: python

    import os
    from zipfile import ZipFile
    import imageio as iio

    images = list()
    with ZipFile("imageio.zip") as zf:
        for name in zf.namelist():
            im = iio.imread(name)
            images.append(im)
