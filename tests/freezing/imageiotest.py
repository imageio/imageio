import os
import imageio


print('Getting image from web ...')
im = imageio.imread('http://imgs.xkcd.com/comics/python.png')
imageio.imsave('xkcd_python.jpg', im)
print('Saved image xkcd_python.jpg!')

fname = 'C:\\almar\\Dropbox\\chelsea.zip'
if not os.path.isfile(fname):
    fname = '/home/almar/dropbox/chelsea.zip'
fname += '/chelsea.png'

print('Getting image from zipfile ...')
im = imageio.imread(fname)
imageio.imsave('chelsea.jpg', im[:, :, :3])
print('Saved image chelsea.jpg!')
