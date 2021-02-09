from .imopen import imopen
import numpy as np


def imread(uri, *args, index=None, plugin=None, **kwargs):
    with imopen()(uri, *args, plugin=plugin, **kwargs) as img_file:
        return np.asarray(img_file.read(index=index))


def imiter(uri, *args, plugin=None, **kwargs):
    with imopen()(uri, *args, plugin=plugin, **kwargs) as img_file:
        for image in img_file.iter():
            yield np.asarray(image)
