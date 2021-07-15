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

Format List
-----------
Each backend listed here is listed using the format string you would use to call
the respective backend explicitly. For example, if you have a PNG file that you wish
to open with pillow you would use ::

    iio.imread("image.png", format="PNG-PIL")

and the backend will be listed as ``PNG-PIL``.

:mod:`FreeImage <imageio.plugins.freeimage>`
:mod:`Pillow <imageio.plugins.pillow_legacy>`
:mod:`itk <imageio.plugins.simpleitk>`
:mod:`FFMPEG <imageio.plugins.ffmpeg>`
:mod:`GDAL <imageio.plugins.gdal>`
:mod:`tiff <imageio.plugins.tifffile>`
:mod:`fits <imageio.plugins.fits>`
:mod:`DICOM <imageio.plugins.dicom>`
:mod:`Lytro <imageio.plugins.lytro>`
:mod:`FEI/SEM <imageio.plugins.feisem>`
:mod:`npz <imageio.plugins.npz>`
:mod:`BSDF <imageio.plugins.bsdf>`
:mod:`SPE <imageio.plugins.spe>`
:mod:`SWF <imageio.plugins.swf>`


3fr (Hasselblad raw format)
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

arw (Sony alpha)
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

avi (Audio Video Interleave)
    Backends: :mod:`FFMPEG <imageio.plugins.ffmpeg>`

bay (Casio raw format)
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

bmp (`Bitmap <https://en.wikipedia.org/wiki/BMP_file_format>`_)
    Backends: :mod:`BMP-FI <imageio.plugins.freeimage>`, :mod:`BMP-PIL
    <imageio.plugins.pillow_legacy>`, :mod:`itk <imageio.plugins.simpleitk>`

bmq (Re-Volt mipmap)
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

bsdf (`Binary Structured Data Format <http://bsdf.io/>`_)
    Backend: :mod:`BSDF <imageio.plugins.bsdf>`

bufr (Binary Universal Form for the Representation of meteorological data)
    Backend: :mod:`BUFR-PIL <imageio.plugins.pillow_legacy>`

bw (Silicon Graphics Image)
    Backend: :mod:`SGI-FI <imageio.plugins.freeimage>`, :mod:`SGI-PIL
    <imageio.plugins.pillow_legacy>`

cap (Scirra Construct image format)
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

cine (`AMETEK High Speed Camera Format <https://phantomhighspeed-knowledge.secure.force.com/servlet/fileField?id=0BE1N000000kD2i#:~:text=Cine%20is%20a%20video%20file,camera%20model%20and%20image%20resolution.>`_)
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

cr2
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

crw
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

cs1
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

ct (Computerized Tomography)
    Backends: :mod:`DICOM <imageio.plugins.dicom>`

cur (Windows Cursor Icons)
    Backends: :mod:`CUR-PIL <imageio.plugins.pillow_legacy>`

cut (Dr. Halo)
    Backends: :mod:`CUT-FI <imageio.plugins.freeimage>`

dc2
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

dcm (DICOM file format)
    Backends: :mod:`itk <imageio.plugins.simpleitk>`, :mod:`DICOM
    <imageio.plugins.dicom>`

dcr
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

dcx (Intel DCX)
    Backends: :mod:`DCX-PIL <imageio.plugins.pillow_legacy>`

dds (DirectX Texture Container)
    Backend: :mod:`DDS-FI <imageio.plugins.freeimage>`, :mod:`DDS-PIL
    <imageio.plugins.pillow_legacy>`

DIB (Windows Bitmap)
    Backend: :mod:`DIB-PIL <imageio.plugins.pillow_legacy>`

dicom (DICOM file format)
    Backends: :mod:`itk <imageio.plugins.simpleitk>`

dng
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

drf
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

dsc
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

ecw (Enhanced Compression Wavelet)
    Backends: :mod:`GDAL <imageio.plugins.gdal>`

emf (Windows Metafile)
    Backends: :mod:`WMF-PIL <imageio.plugins.pillow_legacy>`

eps (Encapsulated Postscript)
    Backends: :mod:`EPS-PIL <imageio.plugins.pillow_legacy>`

erf 
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

exr (ILM OpenEXR)
    Backends: :mod:`EXR-FI <imageio.plugins.freeimage>`

fff
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

fit (Flexible Image Transport System File)
    Backends: :mod:`FITS-PIL <imageio.plugins.pillow_legacy>`, :mod:`fits
    <imageio.plugins.fits>`

fits (Flexible Image Transport System File)
    Backends: :mod:`FITS-PIL <imageio.plugins.pillow_legacy>`, :mod:`fits
    <imageio.plugins.fits>`

flc (Autodesk FLC Animation)
    Backends: :mod:`FLI-PIL <imageio.plugins.pillow_legacy>`

fli (Autodesk FLI Animation)
    Backends: :mod:`FLI-PIL <imageio.plugins.pillow_legacy>`

fpx (Kodak FlashPix)
    Backends: :mod:`FPX-PIL <imageio.plugins.pillow_legacy>`

ftc (Independence War 2: Edge Of Chaos Texture Format)
    Backends: :mod:`FTEX-PIL <imageio.plugins.pillow_legacy>`

fts (Flexible Image Transport System File)
    Backends: :mod:`fits <imageio.plugins.fits>`

ftu (Independence War 2: Edge Of Chaos Texture Format)
    Backends: :mod:`FTEX-PIL <imageio.plugins.pillow_legacy>`

fz (Flexible Image Transport System File)
    Backends: :mod:`fits <imageio.plugins.fits>`

g3 (Raw fax format CCITT G.3)
    Backends: :mod:`G3-FI <imageio.plugins.freeimage>`

gbr (GIMP brush file)
    Backends: :mod:`GBR-PIL <imageio.plugins.pillow_legacy>`

gdcm (Grassroots DICOM)
    Backends: :mod:`itk <imageio.plugins.simpleitk>`

gif (Graphics Interchange Format)
    Backends: :mod:`GIF-FI <imageio.plugins.freeimage>`, :mod:`GIF-PIL
    <imageio.plugins.pillow_legacy>`

gipl (UMDS GIPL)
    Backends: :mod:`itk <imageio.plugins.simpleitk>`

grib (gridded meteorological data)
    Backends: :mod:`GRIB-PIL <imageio.plugins.pillow_legacy>`

h5 (Hierarchical Data Format 5)
    Backends: :mod:`HDF5-PIL <imageio.plugins.pillow_legacy>`

hdf (Hierarchical Data Format 5)
    Backends: :mod:`HDF5-PIL <imageio.plugins.pillow_legacy>`

hdf5 (Hierarchical Data Format 5)
    Backends: :mod:`itk <imageio.plugins.simpleitk>`

hdp (JPEG Extended Range)
    Backends: :mod:`JPEG-XR-FI <imageio.plugins.freeimage>`

hdr (High Dynamic Range Image)
    Backends: :mod:`HDR-FI <imageio.plugins.freeimage>`, :mod:`itk
    <imageio.plugins.simpleitk>`

ia
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

icns (Mac OS Icon File)
    Backends: :mod:`ICNS-PIL <imageio.plugins.pillow_legacy>`

ico (Windows Icon File)
    Backends: :mod:`ICO-FI <imageio.plugins.freeimage>`, :mod:`ICO-PIL
    <imageio.plugins.pillow_legacy>`

iff (ILBM Interleaved Bitmap)
    Backends: :mod:`IFF-FI <imageio.plugins.freeimage>` 

iim (IPTC/NAA)
    Backends: :mod:`IPTC-PIL <imageio.plugins.pillow_legacy>`

iiq
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

im (IFUNC Image Memory)
    Backends: :mod:`IM-PIL <imageio.plugins.pillow_legacy>`

img
    Backends: :mod:`itk <imageio.plugins.simpleitk>`, :mod:`GDAL
    <imageio.plugins.gdal>`

img.gz
    Backends: :mod:`itk <imageio.plugins.simpleitk>`

IMT (IM Tools)
    Backends: :mod:`IMT-PIL <imageio.plugins.pillow_legacy>`

ipl (Image Processing Lab)
    Backends: :mod:`itk <imageio.plugins.simpleitk>`

j2c (JPEG 2000)
    Backends: :mod:`J2K-FI <imageio.plugins.freeimage>`, :mod:`JPEG2000-PIL <imageio.plugins.pillow_legacy>`

j2k (JPEG 2000)
    Backends: :mod:`J2K-FI <imageio.plugins.freeimage>`, :mod:`JPEG2000-PIL <imageio.plugins.pillow_legacy>`

jfif (JPEG)
    Backends: :mod:`JPEG-PIL <imageio.plugins.pillow_legacy>`

jif (JPEG)
    Backends: :mod:`JPEG-FI <imageio.plugins.freeimage>`

jng (JPEG Network Graphics)
    Backends: :mod:`JNG-FI <imageio.plugins.freeimage>`

jp2 (JPEG 2000)
    Backends: :mod:`JP2-FI <imageio.plugins.freeimage>`, :mod:`JPEG2000-PIL <imageio.plugins.pillow_legacy>`

jpc (JPEG 2000)
    Backends: :mod:`JPEG2000-PIL <imageio.plugins.pillow_legacy>`

jpe (JPEG)
    Backends: :mod:`JPEG-FI <imageio.plugins.freeimage>`, :mod:`JPEG-PIL <imageio.plugins.pillow_legacy>`

jpeg (Joint Photographic Experts Group)
    Backends: :mod:`JPEG-FI <imageio.plugins.freeimage>`, :mod:`JPEG-PIL <imageio.plugins.pillow_legacy>`, :mod:`itk <imageio.plugins.simpleitk>`, :mod:`GDAL <imageio.plugins.gdal>`

jpf (JPEG 2000)
    Backends: :mod:`JPEG2000-PIL <imageio.plugins.pillow_legacy>`

jpg (Joint Photographic Experts Group)
    Backends: :mod:`JPEG-FI <imageio.plugins.freeimage>`, :mod:`JPEG-PIL <imageio.plugins.pillow_legacy>`, :mod:`itk <imageio.plugins.simpleitk>`, :mod:`GDAL <imageio.plugins.gdal>`

jpx (JPEG 2000)
    Backends: :mod:`JPEG2000-PIL <imageio.plugins.pillow_legacy>`

jxr (JPEG Extended Range)
    Backends: :mod:`JPEG-XR-FI <imageio.plugins.freeimage>`

k25
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

kc2
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

kdc
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

koa (C64 Koala Graphics)
    Backends: :mod:`KOALA-FI <imageio.plugins.freeimage>`

lbm (ILBM Interleaved Bitmap)
    Backends: :mod:`IFF-FI <imageio.plugins.freeimage>` 

lfp (Lytro F01)
    Backends: :mod:`LYTRO-LFP <imageio.plugins.lytro>`

lfr (Lytro Illum)
    Backends: :mod:`LYTRO-LFR <imageio.plugins.lytro>`

lsm (ZEISS LSM)
    Backends: :mod:`itk <imageio.plugins.simpleitk>`, :mod:`tiff <imageio.plugins.tifffile>`

MCIDAS (`McIdas area file <https://www.ssec.wisc.edu/mcidas/doc/prog_man/2003print/progman2003-formats.html>`_)
    Backends: :mod:`MCIDAS-PIL <imageio.plugins.pillow_legacy>`

mdc
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

mef
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

mgh (FreeSurfer File Format)
    Backends: :mod:`itk <imageio.plugins.simpleitk>`

mha (ITK MetaImage)
    Backends: :mod:`itk <imageio.plugins.simpleitk>`

mhd (ITK MetaImage Header)
    Backends: :mod:`itk <imageio.plugins.simpleitk>`

mic (Microsoft Image Composer)
    Backends: :mod:`MIC-PIL <imageio.plugins.pillow_legacy>`

mkv (Matroska Multimedia Container)
    Backends: :mod:`FFMPEG <imageio.plugins.ffmpeg>`

mnc (Medical Imaging NetCDF)
    Backends: :mod:`itk <imageio.plugins.simpleitk>`

mnc2 (Medical Imaging NetCDF 2)
    Backends: :mod:`itk <imageio.plugins.simpleitk>`

mos (Leaf Raw Image Format)
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

mov (QuickTime File Format)
    Backends: :mod:`FFMPEG <imageio.plugins.ffmpeg>`

mp4 (MPEG-4 Part 14)
    Backends: :mod:`FFMPEG <imageio.plugins.ffmpeg>`

mpeg (Moving Picture Experts Group)
    Backends: :mod:`FFMPEG <imageio.plugins.ffmpeg>`

mpg (Moving Picture Experts Group)
    Backends: :mod:`FFMPEG <imageio.plugins.ffmpeg>`

mpo (JPEG Multi-Picture Format (CIPA DC-007))
    Backends: :mod:`MPO-PIL <imageio.plugins.pillow_legacy>`

mri (Magnetic resonance imaging)
    Backends: :mod:`DICOM <imageio.plugins.dicom>`

mrw
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

msp (Windows Paint)
    Backends: :mod:`MSP-PIL <imageio.plugins.pillow_legacy>`

nef
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

nhdr
    Backends: :mod:`itk <imageio.plugins.simpleitk>`

nia
    Backends: :mod:`itk <imageio.plugins.simpleitk>`

nii
    Backends: :mod:`itk <imageio.plugins.simpleitk>`

nii.gz
    Backends: :mod:`itk <imageio.plugins.simpleitk>`

npz
    Backends: :mod:`npz <imageio.plugins.npz>`

nrrd
    Backends: :mod:`itk <imageio.plugins.simpleitk>`

nrw
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

orf
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

pbm (Pbmplus image)
    Backends: :mod:`PPM-FI <imageio.plugins.freeimage>`, :mod:`PPM-PIL <imageio.plugins.pillow_legacy>`, (Portable Bitmap (ASCII): :mod:`PBM-FI <imageio.plugins.freeimage>`, (Portable Bitmap (RAW): :mod:`PBMRAW-FI <imageio.plugins.freeimage>`

pcd (Kodak PhotoCD)
    Backends: :mod:`PCD-FI <imageio.plugins.freeimage>`, :mod:`PCD-PIL <imageio.plugins.pillow_legacy>`

pct
    Backends: (Macintosh PICT) :mod:`PICT-PIL <imageio.plugins.pillow_legacy>`

PCX (Zsoft Paintbrush)
    Backends: :mod:`PCX-FI <imageio.plugins.freeimage>`, :mod:`PCX-PIL <imageio.plugins.pillow_legacy>`

pef
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

pfm
    Backends: :mod:`PFM-FI <imageio.plugins.freeimage>`

pgm 
    Backends: (Pbmplus image) :mod:`PPM-PIL <imageio.plugins.pillow_legacy>`, (Portable Greymap (ASCII)) :mod:`PGM-FI <imageio.plugins.freeimage>`, (Portable Greymap (RAW)) :mod:`PGMRAW-FI <imageio.plugins.freeimage>`

pic (Macintosh PICT)
    Backends: :mod:`PICT-PIL <imageio.plugins.pillow_legacy>`, :mod:`itk <imageio.plugins.simpleitk>`

pict (Macintosh PICT)
    Backends: :mod:`PICT-PIL <imageio.plugins.pillow_legacy>`

png (Portable Network Graphics)
    Backends: :mod:`PNG-FI <imageio.plugins.freeimage>`, :mod:`PNG-PIL <imageio.plugins.pillow_legacy>`, :mod:`itk <imageio.plugins.simpleitk>`

ppm 
    Backends: (Pbmplus image) :mod:`PPM-PIL <imageio.plugins.pillow_legacy>`, (Portable Pixelmap (ASCII)) :mod:`PPM-FI <imageio.plugins.freeimage>`, (Portable Pixelmap (Raw)) :mod:`PPMRAW-FI <imageio.plugins.freeimage>`

ps (Ghostscript)
    Backend: :mod:`EPS-PIL <imageio.plugins.pillow_legacy>`

psd (Adope Photoshop 2.5 and 3.0)
    Backends: :mod:`PSD-PIL <imageio.plugins.pillow_legacy>`, :mod:`PSD-FI <imageio.plugins.freeimage>`

ptx
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

pxn
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

pxr (PIXAR raster image)
    Backends: :mod:`PIXAR-PIL <imageio.plugins.pillow_legacy>`

qtk
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

raf
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

ras (Sun Raster File)
    Backends: :mod:`SUN-PIL <imageio.plugins.pillow_legacy>`, :mod:`RAS-FI <imageio.plugins.freeimage>`

raw
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`, :mod:`LYTRO-ILLUM-RAW <imageio.plugins.lytro>`, :mod:`LYTRO-F01-RAW <imageio.plugins.lytro>`

rdc
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

rgb (Silicon Graphics Image)
    Backends: :mod:`SGI-PIL <imageio.plugins.pillow_legacy>`

rgba (Silicon Graphics Image)
    Backends: :mod:`SGI-PIL <imageio.plugins.pillow_legacy>`

rw2
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

rwl
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>` 

rwz
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

sgi (Silicon Graphics Image)
    Backends: :mod:`SGI-PIL <imageio.plugins.pillow_legacy>`

spe (SPE File Format)
    Backends: :mod:`SPE <imageio.plugins.spe>`

SPIDER
    Backends: :mod:`SPIDER-PIL <imageio.plugins.pillow_legacy>`

sr2
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

srf
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

srw
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

sti
    Backends: :mod:`RAW-FI <imageio.plugins.freeimage>`

stk
    Backends: :mod:`tiff <imageio.plugins.tifffile>`

swf (Shockwave Flash)
    Backends: :mod:`SWF <imageio.plugins.swf>`

targa (Truevision TGA)
    Backends: :mod:`TARGA-FI <imageio.plugins.freeimage>`

tga (Truevision TGA)
    Backends: :mod:`TGA-PIL <imageio.plugins.pillow_legacy>`, :mod:`TARGA-FI <imageio.plugins.freeimage>`

tif (Tagged Image File)
    Backends: :mod:`tiff <imageio.plugins.tifffile>`, :mod:`TIFF-PIL <imageio.plugins.pillow_legacy>`, :mod:`TIFF-FI <imageio.plugins.freeimage>`, :mod:`FEI <imageio.plugins.feisem>`, :mod:`itk <imageio.plugins.simpleitk>`, :mod:`GDAL <imageio.plugins.gdal>`

tiff (Tagged Image File Format)
    Backends: :mod:`tiff <imageio.plugins.tifffile>`, :mod:`TIFF-PIL <imageio.plugins.pillow_legacy>`, :mod:`TIFF-FI <imageio.plugins.freeimage>`, :mod:`FEI <imageio.plugins.feisem>`, :mod:`itk <imageio.plugins.simpleitk>`, :mod:`GDAL <imageio.plugins.gdal>`

vtk
    Backends: :mod:`itk <imageio.plugins.simpleitk>`

wap (Wireless Bitmap)
    Backends: :mod:`WBMP-FI <imageio.plugins.freeimage>`

wbm (Wireless Bitmap)
    Backends: :mod:`WBMP-FI <imageio.plugins.freeimage>`

wbmp (Wireless Bitmap)
    Backends: :mod:`WBMP-FI <imageio.plugins.freeimage>`

wdp (JPEG Extended Range)
    Backends: :mod:`JPEG-XR-FI <imageio.plugins.freeimage>`

webm ()
    Backends: :mod:`FFMPEG <imageio.plugins.ffmpeg>`

webp (Google WebP)
    Backends: :mod:`WEBP-FI <imageio.plugins.freeimage>`

wmf (Windows Meta File)
    Backends: :mod:`WMF-PIL <imageio.plugins.pillow_legacy>`

wmv

xbm (X11 Bitmap)
    Backends: :mod:`XBM-PIL <imageio.plugins.pillow_legacy>`, :mod:`XBM-FI <imageio.plugins.freeimage>`

xpm (X11 Pixel Map)
    Backends: :mod:`XPM-PIL <imageio.plugins.pillow_legacy>`, :mod:`XPM-FI <imageio.plugins.freeimage>`

XVTHUMB (Thumbnail Image)
    Backends: :mod:`XVTHUMB-PIL <imageio.plugins.pillow_legacy>`


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