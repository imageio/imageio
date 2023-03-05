Imageio Usage Examples
======================

Some of these examples use Visvis to visualize the image data,
but one can also use Matplotlib to show the images.

Imageio provides a range of :doc:`example images <user_guide/standardimages>`,
which can be used by using a URI like ``'imageio:chelsea.png'``. The images
are automatically downloaded if not already present on your system.
Therefore most examples below should just work.


Read an image of a cat
----------------------

Probably the most important thing you'll ever need.

.. code-block:: python

    import imageio.v3 as iio

    im = iio.imread('imageio:chelsea.png')
    print(im.shape)  # (300, 451, 3)
    
If the image is a GIF:

.. code-block:: python

    import imageio.v3 as iio
    
    # index=None means: read all images in the file and stack along first axis
    frames = iio.imread("imageio:newtonscradle.gif", index=None)
    # ndarray with (num_frames, height, width, channel)
    print(frames.shape)  # (36, 150, 200, 3)   

Read from fancy sources
-----------------------

Imageio can read from filenames, file objects.

.. code-block:: python

    import imageio.v3 as iio
    import io


    # from HTTPS
    web_image = "https://upload.wikimedia.org/wikipedia/commons/d/d3/Newtons_cradle_animation_book_2.gif"
    frames = iio.imread(web_image, index=None)

    # from bytes
    bytes_image = iio.imwrite("<bytes>", frames, extension=".gif")
    frames = iio.imread(bytes_image, index=None)

    # from byte streams
    byte_stream = io.BytesIO(bytes_image)
    frames = iio.imread(byte_stream, index=None)
   
    # from file objects
    class MyFileObject:
        def read(size:int=-1):
            return bytes_image

        def close():
            return  # nothing to do

    frames = iio.imread(MyFileObject())

Read all Images in a Folder
---------------------------

.. code-block:: python

    import imageio.v3 as iio
    from pathlib import Path

    images = list()
    for file in Path("path/to/folder").iterdir():
        if not file.is_file():
            continue

        images.append(iio.imread(file))

Note, however, that ``Path().iterdir()`` does not guarantees the order in which
files are read.

Grab screenshot or image from the clipboard
-------------------------------------------

(Screenshots are supported on Windows and OS X, clipboard on Windows only.)

.. code-block:: python

    import imageio.v3 as iio

    im_screen = iio.imread('<screen>')
    im_clipboard = iio.imread('<clipboard>')


Grab frames from your webcam
----------------------------

.. note::
    For this to work, you need to install the ffmpeg backend::

        pip install imageio[ffmpeg]

.. code-block:: python

    import imageio.v3 as iio
    import numpy as np

    for idx, frame in enumerate(iio.imiter("<video0>")):
        print(f"Frame {idx}: avg. color {np.sum(frame, axis=-1)}")

Note: You can replace the zero with another index in case you have multiple
devices attached.

Convert a short movie to grayscale
----------------------------------

.. note::
    For this to work, you need to install the ffmpeg backend::

        pip install imageio[ffmpeg]

.. code-block:: python

    import imageio as iio
    import numpy as np

    # read the video (it fits into memory)
    # Note: this will open the image twice. Check the docs (advanced usage) if
    # this is an issue for your use-case
    metadata = iio.immeta("imageio:cockatoo.mp4", exclude_applied=False)
    frames = iio.imread("imageio:cockatoo.mp4", index=None)
    
    # manually convert the video
    gray_frames = np.dot(frames, [0.2989, 0.5870, 0.1140])
    gray_frames = np.round(gray_frames).astype(np.uint8)
    gray_frames_as_rgb = np.stack([gray_frames] * 3, axis=-1)

    # write the video
    iio.imwrite("cockatoo_gray.mp4", gray_frames_as_rgb, fps=metadata["fps"])

Read or iterate frames in a video
---------------------------------

.. note::
    For this to work, you need to install the pyav backend::

        pip install av

.. code-block:: python

    import imageio.v3 as iio

    # read a single frame
    frame = iio.imread(
        "imageio:cockatoo.mp4", 
        index=42, 
        plugin="pyav", 
    )

    # bulk read all frames
    # Warning: large videos will consume a lot of memory (RAM)
    frames = iio.imread("imageio:cockatoo.mp4", plugin="pyav")

    # iterate over large videos
    for frame in iio.imiter("imageio:cockatoo.mp4", plugin="pyav"):
        print(frame.shape, frame.dtype)


Re-encode a (large) video
-------------------------

.. note::
    For this to work, you need to install the pyav backend::

        pip install av

.. code-block:: python

    import imageio.v3 as iio

    # assume this is too large to keep all frames in memory
    source = "imageio:cockatoo.mp4"
    dest = "reencoded_cockatoo.mkv"

    fps = iio.immeta(source, plugin="pyav")["fps"]

    with iio.imopen(dest, "w", plugin="pyav") as out_file:
        out_file.init_video_stream("vp9", fps=fps)

        for frame in iio.imiter(source, plugin="pyav"):
            out_file.write_frame(frame)


Read medical data (DICOM)
-------------------------

.. code-block:: python

    import imageio.v3 as iio
    dirname = 'path/to/dicom/files'

    # Read multiple images of different shape
    ims = [img for img in iio.imiter(dirname, plugin='DICOM')]
    # Read as volume
    vol = iio.imread(dirname, plugin='DICOM')
    # Read multiple volumes of different shape
    vols = [img for img in iio.imiter(dirname, plugin='DICOM')]


Volume data
-----------

.. code-block:: python

    import imageio.v3 as iio
    import visvis as vv

    vol = iio.imread('imageio:stent.npz')
    vv.volshow(vol)


Writing videos with FFMPEG and vaapi
------------------------------------
Using vaapi can help free up CPU time on your device while you are encoding
videos. One notable difference between vaapi and x264 is that vaapi doesn't
support the color format yuv420p.

Note, you will need ffmpeg compiled with vaapi for this to work.

.. code-block:: python

    import imageio.v2 as iio
    import numpy as np

    # All images must be of the same size
    image1 = np.stack([iio.imread('imageio:camera.png')] * 3, 2)
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
    hardware supports the chosen codec. If your hardware supports h265, you may
    be able to encode using ``'hevc_vaapi'``
    

Writing to Bytes (Encoding)
---------------------------

You can convert ndimages into byte strings. For this, you have to hint the
desired extension (using ``extension=``), as a byte string doesn't specify any
information about the format or color space to use. Note that, if the backend
supports writing to file-like objects, the entire process will happen without
touching your file-system.

.. code-block:: python

    import imageio.v3 as iio

    # load an example image
    img = iio.imread('imageio:astronaut.png')

    # png-encoded bytes string
    png_encoded = iio.imwrite("<bytes>", img, extension=".png")
    
    # jpg-encoded bytes string
    jpg_encoded = iio.imwrite("<bytes>", img, extension=".jpeg")

    # RGBA bytes string
    img = iio.imread('imageio:astronaut.png', mode="RGBA")
    png_encoded = iio.imwrite("<bytes>", img, extension=".png")

Writing to BytesIO
------------------

Similar to writing to byte strings, you can also write to BytesIO directly.

.. code-block:: python

    import imageio.v3 as iio
    import io

    # load an example image
    img = iio.imread('imageio:astronaut.png')

    # write as PNG
    output = io.BytesIO()
    iio.imwrite(output, img, plugin="pillow", extension=".png")
    
    # write as JPG
    output = io.BytesIO()
    iio.imwrite(output, img, plugin="pillow", extension=".jpeg")

Optimizing a GIF using pygifsicle
------------------------------------
When creating a `GIF
<https://it.wikipedia.org/wiki/Graphics_Interchange_Format>`_ using `imageio
<https://imageio.readthedocs.io/en/stable/>`_ the resulting images can get quite
heavy, as the created GIF is not optimized. This can be useful when the
elaboration process for the GIF is not finished yet (for instance if some
elaboration on specific frames stills need to happen), but it can be an issue
when the process is finished and the GIF is unexpectedly big.

GIF files can be compressed in several ways, the most common one method (the one
used here) is saving just the differences between the following frames. In this
example, we apply the described method to a given GIF `my_gif` using `pygifsicle
<https://github.com/LucaCappelletti94/pygifsicle>`_, a porting of the
general-purpose GIF editing command-line library `gifsicle
<https://www.lcdf.org/gifsicle/>`_. To install pygifsicle and gifsicle, `read
the setup on the project page
<https://github.com/LucaCappelletti94/pygifsicle>`_: it boils down to installing
the package using pip and following the console instructions:

.. code-block:: shell

    pip install pygifsicle

Now, let's start by creating a gif using imageio:

.. code-block:: python

    import imageio.v3 as iio
    import matplotlib.pyplot as plt
    import numpy as np

    n = 100
    gif_path = "test.gif"

    n = 100
    plt.figure(figsize=(4, 4))
    for x in range(n):
        plt.scatter(x / n, x / n)
        plt.xlim(0, 1)
        plt.ylim(0, 1)
        plt.savefig(f"{x}.jpg")

    frames = np.stack([iio.imread(f"{x}.jpg") for x in range(n)], axis=0)

    iio.imwrite(gif_path, frames)

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

    import imageio.v3 as iio
    import matplotlib.pyplot as plt
    import numpy as np
    from pygifsicle import optimize

    n = 100
    gif_path = "test.gif"

    n = 100
    plt.figure(figsize=(4, 4))
    for x in range(n):
        plt.scatter(x / n, x / n)
        plt.xlim(0, 1)
        plt.ylim(0, 1)
        plt.savefig(f"{x}.jpg")

    frames = np.stack([iio.imread(f"{x}.jpg") for x in range(n)], axis=0)

    iio.imwrite(gif_path, frames)
    optimize(gif_path)

Reading Images from ZIP archives
--------------------------------

.. note::

    In the future, this syntax will change to better match the URI standard by
    using fragments. The updated syntax will be
    ``"Path/to/file.zip#path/inside/zip/to/image.png"``.

.. code-block:: python

    import imageio.v3 as iio

    image = iio.imread("Path/to/file.zip/path/inside/zip/to/image.png")




Reading Multiple Files from a ZIP archive
-----------------------------------------

Assuming there are only image files in the ZIP archive you can iterate over
them with a simple script like the one below.

.. code-block:: python

    import os
    from zipfile import ZipFile
    import imageio.v3 as iio

    images = list()
    with ZipFile("imageio.zip") as zf:
        for name in zf.namelist():
            im = iio.imread(name)
            images.append(im)

Reading Metadata
----------------

ImageIO differentiates between two types of metadata: format-specific metadata
and standardized metadata.

Format-specific metadata comes in the form of a python dict and aims to expose
all the metadata contained in the image using the containers/plugins key and
format::

    import imageio.v3 as iio

    metadata = iio.immeta("imageio:chelsea.png")
    print(metadata["mode"])  # "RGB"

Standardized metadata, on the other hand, comes in the form of the
:class:`ImageProperties <imageio.core.v3_plugin_api.ImageProperties>` dataclass
and aims to expose a curated set of metadata using a standardized name and
format independent of the underlying container or plugin::

    import imageio.v3 as iio

    props = iio.improps("imageio:chelsea.png")
    print(props.shape)  # (300, 451, 3)
    print(props.dtype)  # dtype('uint8')
