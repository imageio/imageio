
import numpy as np


class ImageList(list):
    def __init__(self, meta=None):
        list.__init__(self)
        # Check
        if not (meta is None or isinstance(meta, dict)):
            raise ValueError('ImageList expects meta data to be a dict.')
        # Convert and return
        self._meta = meta if meta is not None else {}
    
    @property
    def meta(self):
        """ The dict with the meta data of this image.
        """ 
        return self._meta


class Image(np.ndarray):
    """ Image(array)
    
    For ND images. Objects of this class have a 'meta' attribute that
    keeps the meta information as a dict.
    
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
        # Scalars should act normal        
        if not self.shape:
            native = self.dtype.type(self)
            return native.__repr__()
        n = 'x'.join([str(i) for i in self.shape])
        return '<%iD image of %s elements>' % (self.ndim, n)
    
    def __str__(self):
        return np.ndarray.__str__(self) # print() shows elements as normal
    
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


class DictWitNames(dict):
    """ DictWitNames()
    A dict in which the keys can be get and set as if they were
    attributes. Very convenient in combination with autocompletion.
    
    This dict only makes sense if the keys are valid attribute names.
    
    """
    
    def __getattribute__(self, key):
        try:
            return object.__getattribute__(self, key)
        except AttributeError:
            if key in self:
                return self[key]
            else:
                raise
    
    def __setattr__(self, key, val):
        if key in self.__dict__:
            raise RuntimeError('The name %r is reserved.' % key)
        else:
            self[key] = val
    
    def __dir__(self):
       a = list(self.__dict__.keys())
       b = list(self.keys())
       return a+b



if __name__ == '__main__':
    a = np.ones((5,5))
    im1 = Image(a)
    im1.meta['foo'] = 'bar'
    im2 = im1*2
    
    L = ImageList()
    L.append(im1)
    L.append(im2)
    
    