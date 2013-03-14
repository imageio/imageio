---------------------------
Currently supported formats
---------------------------

You can get this list also by running ``imageio.help()``.

.. insertdocs start:: imageio._format_docs


List of currently supported formats:
  * :ref:`ANIGIF <ANIGIF>` - Animated gif
  * :ref:`BMP <BMP>` - Windows or OS/2 Bitmap
  * :ref:`ICO <ICO>` - Windows Icon
  * :ref:`JPEG <JPEG>` - JPEG - JFIF Compliant
  * :ref:`JNG <JNG>` - JPEG Network Graphics
  * :ref:`KOALA <KOALA>` - C64 Koala Graphics
  * :ref:`IFF <IFF>` - IFF Interleaved Bitmap
  * :ref:`MNG <MNG>` - Multiple Network Graphics
  * :ref:`PBM <PBM>` - Portable Bitmap (ASCII)
  * :ref:`PBMRAW <PBMRAW>` - Portable Bitmap (RAW)
  * :ref:`PCD <PCD>` - Kodak PhotoCD
  * :ref:`PCX <PCX>` - Zsoft Paintbrush
  * :ref:`PGM <PGM>` - Portable Greymap (ASCII)
  * :ref:`PGMRAW <PGMRAW>` - Portable Greymap (RAW)
  * :ref:`PNG <PNG>` - Portable Network Graphics
  * :ref:`PPM <PPM>` - Portable Pixelmap (ASCII)
  * :ref:`PPMRAW <PPMRAW>` - Portable Pixelmap (RAW)
  * :ref:`RAS <RAS>` - Sun Raster Image
  * :ref:`TARGA <TARGA>` - Truevision Targa
  * :ref:`TIFF <TIFF>` - Tagged Image File Format
  * :ref:`WBMP <WBMP>` - Wireless Bitmap
  * :ref:`PSD <PSD>` - Adobe Photoshop
  * :ref:`CUT <CUT>` - Dr. Halo
  * :ref:`XBM <XBM>` - X11 Bitmap Format
  * :ref:`XPM <XPM>` - X11 Pixmap Format
  * :ref:`DDS <DDS>` - DirectX Surface
  * :ref:`GIF <GIF>` - Graphics Interchange Format
  * :ref:`HDR <HDR>` - High Dynamic Range Image
  * :ref:`G3 <G3>` - Raw fax format CCITT G.3
  * :ref:`SGI <SGI>` - SGI Image Format
  * :ref:`EXR <EXR>` - ILM OpenEXR
  * :ref:`J2K <J2K>` - JPEG-2000 codestream
  * :ref:`JP2 <JP2>` - JPEG-2000 File Format
  * :ref:`PFM <PFM>` - Portable floatmap
  * :ref:`PICT <PICT>` - Macintosh PICT
  * :ref:`RAW <RAW>` - RAW camera image
  * :ref:`DUMMY <DUMMY>` - An example format that does nothing.
  * :ref:`DICOM <DICOM>` - Digital Imaging and Communications in Medicine

.. _ANIGIF:

ANIGIF Animated gif
^^^^^^^^^^^^^^^^^^^

Extensions: ``gif``

 A format for reading and writing animated GIF, based on the
    Freeimage library.
    
**Keyword arguments for reading**


    playback : bool
        'Play' the GIF to generate each frame (as 32bpp) instead of
        returning raw frame data when loading. Default True.
    
**Keyword arguments for writing**


    
    

.. _BMP:

BMP Windows or OS/2 Bitmap
^^^^^^^^^^^^^^^^^^^^^^^^^^

Extensions: ``bmp``

 A BMP format based on the Freeimage library.
        
**Keyword arguments for writing**


    compression : bool
        Whether to compress the bitmap using RLE when saving. Default False.
    
    

.. _ICO:

ICO Windows Icon
^^^^^^^^^^^^^^^^

Extensions: ``ico``

 An ICO format based on the Freeimage library.
    
**Keyword arguments for reading**


    makealpha : bool
        Convert to 32-bit and create an alpha channel from the AND-
        mask when loading. Default True.
    
    

.. _JPEG:

JPEG JPEG - JFIF Compliant
^^^^^^^^^^^^^^^^^^^^^^^^^^

Extensions: ``jpg``, ``jif``, ``jpeg``, ``jpe``

 A JPEG format based on the Freeimage library.
    
**Keyword arguments for reading**


    exifrotate : bool
        Automatically rotate the image according to the exif flag. Default True.
    quickread : bool
        Read the image more quickly, at the expense of quality. Default False.
    
**Keyword arguments for writing**


    quality : scalar
        The compression factor of the saved image (0..100), higher
        numbers result in higher quality but larger file size. Default 75.
    progressive : bool
        Save as a progressive JPEG file (e.g. for images on the web).
        Default False.
    optimize : bool
        On saving, compute optimal Huffman coding tables (can reduce a
        few percent of file size). Default False.
    baseline : bool
        Save basic JPEG, without metadata or any markers. Default False.
    
    

.. _JNG:

JNG JPEG Network Graphics
^^^^^^^^^^^^^^^^^^^^^^^^^

Extensions: ``jng``

 This is the default format used for FreeImage. Each Freeimage
    format has the 'flags' keyword argument. See the Freeimage
    documentation for more information.
    

.. _KOALA:

KOALA C64 Koala Graphics
^^^^^^^^^^^^^^^^^^^^^^^^

Extensions: ``koa``

 This is the default format used for FreeImage. Each Freeimage
    format has the 'flags' keyword argument. See the Freeimage
    documentation for more information.
    

.. _IFF:

IFF IFF Interleaved Bitmap
^^^^^^^^^^^^^^^^^^^^^^^^^^

Extensions: ``iff``, ``lbm``

 This is the default format used for FreeImage. Each Freeimage
    format has the 'flags' keyword argument. See the Freeimage
    documentation for more information.
    

.. _MNG:

MNG Multiple Network Graphics
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Extensions: ``mng``

 This is the default format used for FreeImage. Each Freeimage
    format has the 'flags' keyword argument. See the Freeimage
    documentation for more information.
    

.. _PBM:

PBM Portable Bitmap (ASCII)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Extensions: ``pbm``

 This is the default format used for FreeImage. Each Freeimage
    format has the 'flags' keyword argument. See the Freeimage
    documentation for more information.
    

.. _PBMRAW:

PBMRAW Portable Bitmap (RAW)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Extensions: ``pbm``

 This is the default format used for FreeImage. Each Freeimage
    format has the 'flags' keyword argument. See the Freeimage
    documentation for more information.
    

.. _PCD:

PCD Kodak PhotoCD
^^^^^^^^^^^^^^^^^

Extensions: ``pcd``

 This is the default format used for FreeImage. Each Freeimage
    format has the 'flags' keyword argument. See the Freeimage
    documentation for more information.
    

.. _PCX:

PCX Zsoft Paintbrush
^^^^^^^^^^^^^^^^^^^^

Extensions: ``pcx``

 This is the default format used for FreeImage. Each Freeimage
    format has the 'flags' keyword argument. See the Freeimage
    documentation for more information.
    

.. _PGM:

PGM Portable Greymap (ASCII)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Extensions: ``pgm``

 This is the default format used for FreeImage. Each Freeimage
    format has the 'flags' keyword argument. See the Freeimage
    documentation for more information.
    

.. _PGMRAW:

PGMRAW Portable Greymap (RAW)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Extensions: ``pgm``

 This is the default format used for FreeImage. Each Freeimage
    format has the 'flags' keyword argument. See the Freeimage
    documentation for more information.
    

.. _PNG:

PNG Portable Network Graphics
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Extensions: ``png``

 A PNG format based on the Freeimage library.
    
**Keyword arguments for reading**


    ignoregamma : bool
        Avoid gamma correction. Default False.
    
**Keyword arguments for writing**


    compression : {0, 1, 6, 9}
        The compression factor. Higher factors result in more
        compression at the cost of speed. Note that PNG compression is
        always lossless. Default 6.
    interlaced : bool
        Save using Adam7 interlacing. Default False.
    
    

.. _PPM:

PPM Portable Pixelmap (ASCII)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Extensions: ``ppm``

 This is the default format used for FreeImage. Each Freeimage
    format has the 'flags' keyword argument. See the Freeimage
    documentation for more information.
    

.. _PPMRAW:

PPMRAW Portable Pixelmap (RAW)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Extensions: ``ppm``

 This is the default format used for FreeImage. Each Freeimage
    format has the 'flags' keyword argument. See the Freeimage
    documentation for more information.
    

.. _RAS:

RAS Sun Raster Image
^^^^^^^^^^^^^^^^^^^^

Extensions: ``ras``

 This is the default format used for FreeImage. Each Freeimage
    format has the 'flags' keyword argument. See the Freeimage
    documentation for more information.
    

.. _TARGA:

TARGA Truevision Targa
^^^^^^^^^^^^^^^^^^^^^^

Extensions: ``tga``, ``targa``

 This is the default format used for FreeImage. Each Freeimage
    format has the 'flags' keyword argument. See the Freeimage
    documentation for more information.
    

.. _TIFF:

TIFF Tagged Image File Format
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Extensions: ``tif``, ``tiff``

 This is the default format used for FreeImage. Each Freeimage
    format has the 'flags' keyword argument. See the Freeimage
    documentation for more information.
    

.. _WBMP:

WBMP Wireless Bitmap
^^^^^^^^^^^^^^^^^^^^

Extensions: ``wap``, ``wbmp``, ``wbm``

 This is the default format used for FreeImage. Each Freeimage
    format has the 'flags' keyword argument. See the Freeimage
    documentation for more information.
    

.. _PSD:

PSD Adobe Photoshop
^^^^^^^^^^^^^^^^^^^

Extensions: ``psd``

 This is the default format used for FreeImage. Each Freeimage
    format has the 'flags' keyword argument. See the Freeimage
    documentation for more information.
    

.. _CUT:

CUT Dr. Halo
^^^^^^^^^^^^

Extensions: ``cut``

 This is the default format used for FreeImage. Each Freeimage
    format has the 'flags' keyword argument. See the Freeimage
    documentation for more information.
    

.. _XBM:

XBM X11 Bitmap Format
^^^^^^^^^^^^^^^^^^^^^

Extensions: ``xbm``

 This is the default format used for FreeImage. Each Freeimage
    format has the 'flags' keyword argument. See the Freeimage
    documentation for more information.
    

.. _XPM:

XPM X11 Pixmap Format
^^^^^^^^^^^^^^^^^^^^^

Extensions: ``xpm``

 This is the default format used for FreeImage. Each Freeimage
    format has the 'flags' keyword argument. See the Freeimage
    documentation for more information.
    

.. _DDS:

DDS DirectX Surface
^^^^^^^^^^^^^^^^^^^

Extensions: ``dds``

 This is the default format used for FreeImage. Each Freeimage
    format has the 'flags' keyword argument. See the Freeimage
    documentation for more information.
    

.. _GIF:

GIF Graphics Interchange Format
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Extensions: ``gif``

 A GIF format based on the Freeimage library.
    
**Keyword arguments for reading**


    playback : bool
        'Play' the GIF to generate each frame (as 32bpp) instead of
        returning raw frame data when loading. Default True.

    

.. _HDR:

HDR High Dynamic Range Image
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Extensions: ``hdr``

 This is the default format used for FreeImage. Each Freeimage
    format has the 'flags' keyword argument. See the Freeimage
    documentation for more information.
    

.. _G3:

G3 Raw fax format CCITT G.3
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Extensions: ``g3``

 This is the default format used for FreeImage. Each Freeimage
    format has the 'flags' keyword argument. See the Freeimage
    documentation for more information.
    

.. _SGI:

SGI SGI Image Format
^^^^^^^^^^^^^^^^^^^^

Extensions: ``sgi``

 This is the default format used for FreeImage. Each Freeimage
    format has the 'flags' keyword argument. See the Freeimage
    documentation for more information.
    

.. _EXR:

EXR ILM OpenEXR
^^^^^^^^^^^^^^^

Extensions: ``exr``

 This is the default format used for FreeImage. Each Freeimage
    format has the 'flags' keyword argument. See the Freeimage
    documentation for more information.
    

.. _J2K:

J2K JPEG-2000 codestream
^^^^^^^^^^^^^^^^^^^^^^^^

Extensions: ``j2k``, ``j2c``

 This is the default format used for FreeImage. Each Freeimage
    format has the 'flags' keyword argument. See the Freeimage
    documentation for more information.
    

.. _JP2:

JP2 JPEG-2000 File Format
^^^^^^^^^^^^^^^^^^^^^^^^^

Extensions: ``jp2``

 This is the default format used for FreeImage. Each Freeimage
    format has the 'flags' keyword argument. See the Freeimage
    documentation for more information.
    

.. _PFM:

PFM Portable floatmap
^^^^^^^^^^^^^^^^^^^^^

Extensions: ``pfm``

 This is the default format used for FreeImage. Each Freeimage
    format has the 'flags' keyword argument. See the Freeimage
    documentation for more information.
    

.. _PICT:

PICT Macintosh PICT
^^^^^^^^^^^^^^^^^^^

Extensions: ``pct``, ``pict``, ``pic``

 This is the default format used for FreeImage. Each Freeimage
    format has the 'flags' keyword argument. See the Freeimage
    documentation for more information.
    

.. _RAW:

RAW RAW camera image
^^^^^^^^^^^^^^^^^^^^

Extensions: ``3fr``, ``arw``, ``bay``, ``bmq``, ``cap``, ``cine``, ``cr2``, ``crw``, ``cs1``, ``dc2``, ``dcr``, ``drf``, ``dsc``, ``dng``, ``erf``, ``fff``, ``ia``, ``iiq``, ``k25``, ``kc2``, ``kdc``, ``mdc``, ``mef``, ``mos``, ``mrw``, ``nef``, ``nrw``, ``orf``, ``pef``, ``ptx``, ``pxn``, ``qtk``, ``raf``, ``raw``, ``rdc``, ``rw2``, ``rwl``, ``rwz``, ``sr2``, ``srf``, ``sti``

 This is the default format used for FreeImage. Each Freeimage
    format has the 'flags' keyword argument. See the Freeimage
    documentation for more information.
    

.. _DUMMY:

DUMMY An example format that does nothing.
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Extensions: None

 The dummy format is an example format that does nothing.
    It will never indicate that it can read or save a file. When
    explicitly asked to read, it will simply read the bytes. When 
    explicitly asked to save, it will raise an error.
    

.. _DICOM:

DICOM Digital Imaging and Communications in Medicine
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Extensions: ``dcm``, ``ct``, ``mri``

 A format for reading DICOM images: a common format used to store
    medical image data, such as X-ray, CT and MRI.
    
**Keyword arguments for reading**


    progress : {True, False, BaseProgressIndicator}
        Whether to show progress when reading from multiple files.
        Default True. By passing an object that inherits from
        BaseProgressIndicator, the way in which progress is reported
        can be costumized.
    
    

.. insertdocs end::
