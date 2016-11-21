""" The test suite of freeimage plugin
"""

import os
import sys
import zipfile
import shutil

from pytest import raises  # noqa
from imageio.testing import get_test_dir

import imageio
from imageio.core import get_remote_file, IS_PYPY, urlopen  # noqa

test_dir = get_test_dir()

# During this test, pretend that FI is the default format?
# imageio.formats.sort('-FI')


# Url to download images from
ulr = ("http://sourceforge.net/projects/freeimage/files/"
       "Test%20Suite%20%28graphics%29/2.5.0/")

# Names of zipfiles to download
names = ['png', 'jpeg', 'bmp', 'ico',  'tiff', 'targa', 'koa', 'mng', 'iff', 
         'psd', 'ppm', 'pcx'] 

# Define what formats are not writable, we will convert these to png
NOT_WRITABLE = ['.pgm', '.koa', '.pcx', '.mng', '.iff', '.psd', '.lbm']

# Define files that fail (i.e. crash)
FAILS = []
if sys.platform.startswith('linux'):
    FAILS.extend(['quad-jpeg.tif', 'test1g.tif', 'ycbcr-cat.tif'])

THISDIR = os.path.dirname(os.path.abspath(__file__))
TESTDIR = os.path.join(THISDIR, 'temp')
ZIPDIR = os.path.join(THISDIR, 'zipped')


def run_feeimage_test_suite():
    """ Run freeimage test suite.
    Lots of images. Berrer done locally and then checking the result.
    Not so much suited for CI, I think.
    """
    
    if not os.path.isdir(TESTDIR):
        os.mkdir(TESTDIR)
    if not os.path.isdir(ZIPDIR):
        os.mkdir(ZIPDIR)
    
    for name in names:
        fname = os.path.join(ZIPDIR, name+'.zip')
        # Make sure that the file is there
        if not os.path.isfile(fname):
            print('Downloading %s.zip' % name)
            f1 = urlopen(ulr+name+'.zip')
            f2 = open(fname, 'wb')
            shutil.copyfileobj(f1, f2)
            f1.close()
            f2.close()
        
        # Check contents
        zf = zipfile.ZipFile(fname, 'r')
        subnames = zf.namelist()
        zf.extractall(TESTDIR)
        zf.close()
        
        # Read and write each one
        for subname in subnames:
            if subname in FAILS:
                continue
            fname_zip = fname+'/%s' % subname
            subname_, ext = os.path.splitext(subname)
            fname_dst1 = os.path.join(TESTDIR, subname+'_1'+ext)
            fname_dst2 = os.path.join(TESTDIR, subname+'_2'+ext)
            if os.path.splitext(subname)[1].lower() in NOT_WRITABLE:
                fname_dst1 += '.png'
                fname_dst2 += '.png'
            print('Reading+saving %s' % subname)
            try:
                # Read from zip, save to file
                im = imageio.imread(fname_zip)
                imageio.imsave(fname_dst1, im)
                # Read from file, save to file
                im = imageio.imread(fname_dst1)
                imageio.imsave(fname_dst2, im)
            except Exception:
                e_type, e_value, e_tb = sys.exc_info()
                del e_tb
                err = str(e_value)
                print('woops! ' + fname_zip)
                print('  ' + err)


if __name__ == '__main__':
    run_feeimage_test_suite()
