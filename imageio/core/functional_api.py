from .imopen import imopen


def imread(uri, *, index=None, plugin=None, **kwargs):
    with imopen(uri, **kwargs) as img_file:
        return img_file.read(index=index)


def imiter(uri, *, plugin=None, **kwargs):
    with imopen(uri, **kwargs) as img_file:
        for image in img_file.iter():
            yield image
