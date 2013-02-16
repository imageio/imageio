
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
        meta = meta if meta is not None else {}
        ob = array.view(cls)
        ob._copy_meta(meta)
        return ob
    
    def _copy_meta(self, meta):
        """ Make a 2-level deep copy of the meta dictionary.
        """
        self._meta = DictWitNames()
        for key, val in meta.items():
            if isinstance(val, dict):
                val = DictWitNames(val)  # Copy this level
            self._meta[key] = val
    
    def __repr__(self):
        n = 'x'.join([str(i) for i in self.shape])
        ndim = self.ndim
        if self.shape[-1] in (1,3,4):
            ndim -= 1
        return '<%iD image of %s elements>' % (ndim, n)
    
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
            self._copy_meta(ob.meta)
        else:
            self._copy_meta({})
    
    def __array_wrap__(self, out, context=None):
        """ So that we return a native numpy array (or scalar) when a
        reducting ufunc is applied (such as sum(), std(), etc.)
        """
        if not out.shape:
            return out.dtype.type(out)  # Scalar
        elif out.shape != self.shape:
            return np.asarray(out)
        else:
            return out  # Type Image


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
            # This would have been nice, but it would mean that changes
            # to the given val would not have effect.
            #if isinstance(val, dict):
            #    val = DictWitNames(val)
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
    
    