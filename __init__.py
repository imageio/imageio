# -*- coding: utf-8 -*-
# Copyright (c) 2012, imageio contributers

""" 
The imageio library aims to support reading and writing a wide 
range of image data, including animated images. It is written 
in pure Python (2.x and 3.x) and most functionality is obtained
by wrapping the FreeImage library using ctypes. The imageio 
projected is intended as a replacement for PIL.

Four functions are exposed:
  * imread() - to read an image file and return a numpy array
  * imwrite() - to write a numpy array to an image file
  * movieread() - (name may change) to read animated image data as a list of numpy arrays
  * moviewrite() - (name may change) to write a list of numpy array to an animated image

Further, via the module imageio.freeimage part of the FreeImage library 
is exposed.

Well this is the idea anyway. We're still developing :)

"""


from imageio.freeimage_plugin import imread, imwrite
