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


Iterate over frames in a movie
------------------------------

.. code-block:: python

    import imageio
    
    reader = imageio.get_reader('imageio:cockatoo.mp4')
    for i, im in enumerate(reader):
        print('Mean of frame %i is %1.1f' % (i, im.mean()))


Grab frames from your webcam
----------------------------

Use the special ``<video0>`` uri to read frames from your webcam (via
the ffmpeg plugin). You can replace the zero with another index in case
you have multiple cameras attached.

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
