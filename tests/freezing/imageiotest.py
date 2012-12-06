import imageio
from urllib.request import urlopen # Py3k
print('Getting image ...')
im = imageio.imread('http://imgs.xkcd.com/comics/python.png')
print('Image retrieved!')
print('Saving image ...')
imageio.imsave('xkcd_python.jpg', im)
print('Saved image!')

im = imageio.imread('/home/almar/projects/pylib/imageio/_meuk/imzip.zip/lena.png')
imageio.imsave('lena.jpg', im[:,:,:3])
