
import numpy as np


class ImageList(list):
    def __repr__(self):
        return '<List of %i images>' % len(self)


class Image(np.ndarray):
    """ Image(array)
    
    """
    
    def __new__(cls, array, meta=None):
        # Check
        if not isinstance(array, np.ndarray):
            raise ValueError('Image expects a numpy array.')
        if not (meta is None or isinstance(meta, dict)):
            raise ValueError('Image expects meta data to be a dict.')
        # Convert and return
        ob = array.view(cls)
        ob._meta = meta if meta is not None else {}
        return ob
    
    def __repr__(self):
        n = 'x'.join([str(i) for i in self.shape])
        return '<Image of %s elements>' % n
    
    @property
    def meta(self):
        """ The dict with the meta data of this image.
        """ 
        return self._meta
    
    def __array_finalize__(self, ob):
        """ So the meta info is maintained when doing calculations with
        the array. 
        """
        if isinstance(ob, Image):
            self._meta = ob._meta.copy()
        else:
            self._meta = {}


if __name__ == '__main__':
    a = np.ones((5,5))
    im1 = Image(a)
    im1.meta['foo'] = 'bar'
    im2 = im1*2
    
    