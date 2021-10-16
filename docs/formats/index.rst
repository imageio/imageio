Supported Formats
=================

ImageIO reads and writes images by deligating your request to one of many
backends, e.g., pillow, ffmpeg, tifffile, etc. Each backend supports
its own set of formats, which is how ImageIO manages to support so many
of them.

Below you can find a (non-exhaustive) list of formats that ImageIO supports
together with the backend supporting it. This list is non-exhaustive, because it
only lists the formats we were aware of at the time the docs were written. If
any backend introduces support for new formats they, too, will be supported but
our docs may take time to update and reflect this. If in doubt, check the docs
of the respective backend.

Known Formats
-------------
Below you can find an alphabetically sorted list of *all*
extensions/file-formats that ImageIO is aware of. If an extension is listed
here, it is supported. If an extension is not listed here, it may still be
supported if one of the backends supports the extension/format. If you encoutner
the latter, please `create a new issue
<https://github.com/imageio/imageio/issues>`_ so that we can keep below list up
to date and add support for any missing formats.

Each entry in the list below follows the following format::

    - <extension> (<format name>): <plugin> <plugin> ...

where ``<plugin>`` is the name of a plugin that can handle the format. If you
wish to use a specific plugin to load a format, you would use the name as
specified. For example, if you have a PNG file that you wish to open with pillow
and the ``<plugin>`` is called ``PNG-PIL`` you would call ::

    iio.imread("image.png", format="PNG-PIL")

{% for format in formats %}
{% if format.external_link %}
- **{{ format.extension }}** (`{{ format.name }} <{{format.external_link}}>`_): {% for name in format.priority %} :mod:`{{name}} <{{plugins[name]}}>` {% endfor %}
{% elif format.name %}
- **{{ format.extension }}** ({{ format.name }}): {% for name in format.priority %} :mod:`{{name}} <{{plugins[name]}}>` {% endfor %}
{% else %}
- **{{ format.extension }}**: {% for name in format.priority %} :mod:`{{name}} <{{plugins[name]}}>` {% endfor %}
{%endif%}
{% endfor %}

Formats by Plugin
-----------------
Below you can find a list of each plugin that exists in ImageIO together with the formats
that this plugin supports. This can be useful, for example, if you have to decide which
plugins to install and/or depend on in your project.

:mod:`FreeImage <imageio.plugins.freeimage>`
    tif, tiff, jpeg, jpg, bmp, png, bw, dds, gif, ico, j2c, j2k, jp2,pbm, pcd, PCX,
    pgm, ppm, psd, ras, rgb, rgba, sgi, tga, xbm, xpm, pic, raw, 3fr, arw, bay,
    bmq, cap, cine, cr2, crw, cs1, cut, dc2, dcr, dng, drf, dsc, erf, exr, fff, g3,
    hdp, hdr, ia, iff, iiq, jif, jng, jpe, jxr, k25, kc2, kdc, koa, lbm, mdc, mef,
    mos, mrw, nef, nrw, orf, pct, pef, pfm, pict, ptx, pxn, qtk, raf, rdc, rw2,
    rwl, rwz, sr2, srf, srw, sti, targa, wap, wbm, wbmp, wdp, webp

:mod:`Pillow <imageio.plugins.pillow_legacy>`
    tif, tiff, jpeg, jpg, bmp, png, bw, dds, gif, ico, j2c, j2k, jp2, pbm, pcd, PCX,
    pgm, ppm, psd, ras, rgb, rgba, sgi, tga, xbm, xpm, fit, fits, bufr,
    CLIPBOARDGRAB, cur, dcx, DIB, emf, eps, flc, fli, fpx, ftc, ftu, gbr, grib, h5,
    hdf, icns, iim, im, IMT, jfif, jpc, jpf, jpx, MCIDAS, mic, mpo, msp, ps, pxr,
    SCREENGRAB, SPIDER, wmf, XVTHUMB

:mod:`ITK <imageio.plugins.simpleitk>`
    tif, tiff, jpeg, jpg, bmp, png, pic, img, lsm, dcm, dicom, gdcm, gipl, hdf5,
    hdr, img.gz, ipl, mgh, mha, mhd, mnc, mnc2, nhdr, nia, nii, nii.gz, nrrd, vtk

:mod:`FFMPEG <imageio.plugins.ffmpeg>`
    avi, mkv, mov, mp4, mpeg, mpg, WEBCAM, webm, wmv

:mod:`GDAL <imageio.plugins.gdal>`
    tif, tiff, jpeg, jpg, img, ecw

:mod:`tifffile <imageio.plugins.tifffile>`
    tif,tiff,lsm,stk

:mod:`FITS <imageio.plugins.fits>`
    fit,fits,fts,fz

:mod:`DICOM <imageio.plugins.dicom>`
    dcm,ct,mri

:mod:`Lytro <imageio.plugins.lytro>`
    raw,lfp,lfr

:mod:`FEI/SEM <imageio.plugins.feisem>`
    tif, tiff

:mod:`Numpy <imageio.plugins.npz>`
    npz

:mod:`BSDF <imageio.plugins.bsdf>`
    bsdf

:mod:`SPE <imageio.plugins.spe>`
    spe

:mod:`SWF <imageio.plugins.swf>`
    swf