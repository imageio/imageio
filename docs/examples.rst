Imageio usage examples
======================

Some of these examples use Visvis to visualize the image data,
but one can also use Matplotlib to show the images.

Imageio provides a range of :doc:`example images <standardimages>`,
which can be used by using a URI like ``'imageio:chelsea.png'``. The images
are automatically downloaded if not already present on your system.
Therefore most examples below should just work.


Read an image of a cat
----------------------

Probably the most important thing you ever need.

.. code-block:: python

    import imageio

    im = imageio.imread('imageio:chelsea.png')
    print(im.shape)


Read from fancy sources
-----------------------

Imageio can read from filenames, file objects, http, zipfiles and bytes.

.. code-block:: python

    import imageio
    import visvis as vv

    im = imageio.imread('http://upload.wikimedia.org/wikipedia/commons/d/de/Wikipedia_Logo_1.0.png')
    vv.imshow(im)

Note: reading from HTTP and zipfiles works for many formats including png and jpeg, but may not work
for all formats (some plugins "seek" the file object, which HTTP/zip streams do not support).
In such a case one can download/extract the file first. For HTTP one can use something like
``imageio.imread(imageio.core.urlopen(url).read(), '.gif')``.

Iterate over frames in a movie
------------------------------

.. code-block:: python

    import imageio

    reader = imageio.get_reader('imageio:cockatoo.mp4')
    for i, im in enumerate(reader):
        print('Mean of frame %i is %1.1f' % (i, im.mean()))


Grab screenshot or image from the clipboard
-------------------------------------------

(Screenshots are supported on Windows and OS X, clipboard on Windows only.)

.. code-block:: python

    import imageio

    im_screen = imageio.imread('<screen>')
    im_clipboard = imageio.imread('<clipboard>')


Grab frames from your webcam
----------------------------

Use the special ``<video0>`` uri to read frames from your webcam (via
the ffmpeg plugin). You can replace the zero with another index in case
you have multiple cameras attached. You need to ``pip install imageio-ffmpeg``
in order to use this plugin.

.. code-block:: python

    import imageio
    import visvis as vv

    reader = imageio.get_reader('<video0>')
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

    import imageio

    reader = imageio.get_reader('imageio:cockatoo.mp4')
    fps = reader.get_meta_data()['fps']

    writer = imageio.get_writer('~/cockatoo_gray.mp4', fps=fps)

    for im in reader:
        writer.append_data(im[:, :, 1])
    writer.close()



Read medical data (DICOM)
-------------------------

.. code-block:: python

    import imageio
    dirname = 'path/to/dicom/files'

    # Read as loose images
    ims = imageio.mimread(dirname, 'DICOM')
    # Read as volume
    vol = imageio.volread(dirname, 'DICOM')
    # Read multiple volumes (multiple DICOM series)
    vols = imageio.mvolread(dirname, 'DICOM')


Volume data
-----------

.. code-block:: python

    import imageio
    import visvis as vv

    vol = imageio.volread('imageio:stent.npz')
    vv.volshow(vol)


Writing videos with FFMPEG and vaapi
------------------------------------
Using vaapi (on Linux only) (intel only?) can help free up resources on
your laptop while you are encoding videos. One notable
difference between vaapi and x264 is that vaapi doesn't support the color
format yuv420p.

Note, you will need ffmpeg compiled with vaapi for this to work.

.. code-block:: python
    import imageio
    import numpy as np

    # All images must be of the same size
    image1 = np.stack([imageio.imread('imageio:camera.png')] * 3, 2)
    image2 = imageio.imread('imageio:astronaut.png')
    image3 = imageio.imread('imageio:immunohistochemistry.png')

    w = imageio.get_writer('my_video.mp4', format='FFMPEG', mode='I', fps=1,
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
      operation is acheived with ``|``.
  * ``pixelformat``: set to ``'vaapi_vld'`` to avoid a warning in ffmpeg.
  * ``codec``: the code you wish to use to encode the video. Make sure your
    hardware supports the chosen codec. If your hardware supports h265, you
    may be able to encode using ``'hevc_vaapi'``
