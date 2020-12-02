from .imopen import imopen
import numpy as np


def imread(uri, *, index=None, plugin=None, **kwargs):
    with imopen(uri, **kwargs) as img_file:
        return np.asarray(img_file.read(index=index))


def imiter(uri, *, plugin=None, **kwargs):
    with imopen(uri, **kwargs) as img_file:
        for image in img_file.iter():
            yield np.asarray(image)
