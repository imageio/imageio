Imageio usage examples
======================


Read an image of a cat
----------------------

Probably the most important thing you ever need.

.. code-block:: python

    import imageio
    im = imageio.imread('chelsea.png')



Iterate over frames in a movie
------------------------------

.. code-block:: python

    import imageio
    reader = imageio.read('some_movie.avi')
    for im in reader:
        ...


Grab frames from your webcam
----------------------------

.. code-block:: python

    import imageio
    reader = imageio.read('<video0>')
    for im in reader:
        ...


Convert a movie
------------------------------

.. code-block:: python

    import imageio
    reader = imageio.read('some_movie.avi')
    writer = imageio.read('some_movie_gray.avi')
    for im in reader:
        writer.append_data(im[:, :, 1])


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
