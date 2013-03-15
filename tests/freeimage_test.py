"""
Download zipfiles with the test suite of freeimage.
We also use it to test reading from a zipfile.
"""
import os
import sys

from urllib.request import urlopen
import zipfile
import shutil

import imageio

ulr = "http://sourceforge.net/projects/freeimage/files/Test%20Suite%20%28graphics%29/2.5.0/"

names = ['png', 'jpeg', 'tiff', 'targa']  # etc..


if __name__ == '__main__':
    
    THISDIR = os.path.dirname(os.path.abspath(__file__))
    TESTDIR = os.path.join(THISDIR, 'temp')
    
    if not os.path.isdir(TESTDIR):
        os.mkdir(TESTDIR)
    
    for name in names:
        fname = os.path.join(TESTDIR, name+'.zip')
        # Make sure that the file is there
        if not os.path.isfile(fname):
            print('Downloading %s.zip' % name)
            f1 = urlopen(ulr+name+'.zip')
            f2 = open(os.path.join(TESTDIR, name+'.zip'), 'wb')
            shutil.copyfileobj(f1, f2)
            f1.close()
            f2.close()
        
        # Check contents
        zf = zipfile.ZipFile(fname, 'r')
        subnames = zf.namelist()
        zf.extractall()
        zf.close()
        
        # Read and write each one
        for subname in subnames:
            fname_zip = fname+'/%s' % subname
            fname_dst1 = os.path.join(TESTDIR, '_1'+subname)
            fname_dst2 = os.path.join(TESTDIR, '_2'+subname)
            print('Reading+saving %s' % subname)
            try:
                # Read from zip, save to file
                im = imageio.imread(fname_zip)
                imageio.imsave(fname_dst1, im)
                # Read from file, save to file
                im = imageio.imread(fname_dst1)
                imageio.imsave(fname_dst2, im)
            except Exception as err:
                print(err)
            
        