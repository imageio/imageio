# -*- coding: utf-8 -*-
# Copyright (c) 2013, imageio contributers
# imageio is distributed under the terms of the (new) BSD License.

""" 
Utilities for imageio
"""

import os
import sys
import time

# Try load numpy from pypy
ISPYPY = False
try:
    import numpypy
    ISPYPY = True
except ImportError:
    pass

import numpy as np

# Extra numpypy compatibility
def _dstack(tup):
    for a in tup:
        a.shape = a.shape + tuple( [1]*(3-a.ndim) )
    return np.concatenate(tup, axis=2)
if not hasattr(np, 'dstack'):
    np.dstack = _dstack


# currently not used ... the only use it to easly provide the global meta info
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


# todo: Note that skimage also has an Image class that overloads ndarray
# See if we can learn from that
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
        try:
            ob = array.view(cls)
        except AttributeError:
            # In Pypy, we just return the original; no metadata on the array in Pypy!
            return array
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
        dtype = self.dtype
        ndim = self.ndim
        if self.shape[-1] in (1,3,4):
            ndim -= 1
        return '<%iD image: numpy array with %s elements of dtype %s>' % (ndim, n, dtype)
    
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



class BaseProgressIndicator:
    """ A progress indicator helps display the progres of a task to the
    user. Progress can be pending, running, finished or failed.
    
    Each task has:
      * a name - a short description of what needs to be done.
      * an action - the current action in performing the task (e.g. a subtask)
      * progress - how far the task is completed
      * max - the maximum number of progress units. If 0, the progress is undefinite
      * unit - the units in which the progress is counted
      * status - 0: pending, 1: in progress, 2: finished, 3: failed
    
    This class defines an abstract interface. Subclasses should implement
    _start, _stop, _update_progress(progressText), _write(message).
    """
    
    def __init__(self, name):
        self._name = name
        self._action = ''
        self._unit = ''
        self._max = 0
        self._status = 0
        self._last_progress_update = 0
    
    def start(self,  action='', unit='', max=0):
        if self._status == 1:
            self.finish() 
        self._action = action
        self._unit = unit
        self._max = max
        #
        self._progress = 0 
        self._status = 1
        self._start()
    
    def status(self):
        return self._status
    
    def set_progress(self, progress=0, force=False):
        self._progress = progress
        # Update or not?
        if not (force or (time.time() - self._last_progress_update > 0.1)):
            return
        self._last_progress_update = time.time()
        # Compose new string
        unit = self._unit or ''
        progressText = ''
        if unit == '%':
            progressText = '%2.1f%%' % progress
        elif self._max > 0:
            percent = 100 * float(progress) / self._max
            progressText = '%i/%i %s (%2.1f%%)' % (progress, self._max, unit, percent)
        elif progress > 0:
            if isinstance(progress, float):
                progressText = '%0.4g %s' % (progress, unit)
            else:
                progressText = '%i %s' % (progress, unit)
        # Update
        self._update_progress(progressText)
    
    def finish(self, message=None):
        self.set_progress(self._progress, True)  # fore update
        self._status = 2
        self._stop()
        if message is not None:
            self._write(message)
        
    
    def fail(self, message=None):
        self.set_progress(self._progress, True)  # fore update
        self._status = 3
        self._stop()
        message = 'FAIL ' + (message or '')
        self._write(message)
    
    def write(self, message):
        if self.__class__ == BaseProgressIndicator:
            # When this class is used as a dummy, print explicit message
            print(message)
        else:
            return self._write(message)
    
    # Implementing classes should implement these
    
    def _start(self):
        pass
        
    def _stop(self):
        pass
    
    def _update_progress(self, progressText):
        pass
    
    def _write(self, message):
        pass
    

class StdoutProgressIndicator(BaseProgressIndicator):
    
    def _start(self):
        self._chars_prefix, self._chars = '', ''
        # Write message
        if self._action:
            self._chars_prefix = '%s (%s): ' % (self._name, self._action)
        else:
            self._chars_prefix = '%s: ' % self._name
        sys.stdout.write(self._chars_prefix)
        sys.stdout.flush()
    
    def _update_progress(self, progressText):
        # If progress is unknown, at least make something move
        if not progressText:
            i1, i2, i3, i4 = '-\\|/'
            progressText = {i1:i2, i2:i3, i3:i4, i4:i1}.get(self._chars, i1)
        # Store new string and write
        delChars = '\b'*len(self._chars)
        self._chars = progressText
        sys.stdout.write(delChars+self._chars)
        sys.stdout.flush()
    
    def _stop(self):
        self._chars = self._chars_prefix = ''
        sys.stdout.write('\n')
        sys.stdout.flush()
    
    def _write(self, message):
        # Write message
        delChars = '\b'*len(self._chars_prefix+self._chars)
        sys.stdout.write(delChars+'  '+message+'\n')
        # Reprint progress text
        sys.stdout.write(self._chars_prefix+self._chars)
        sys.stdout.flush()



if __name__ == '__main__':
    a = np.ones((5,5))
    im1 = Image(a)
    im1.meta['foo'] = 'bar'
    im2 = im1*2
    
    L = ImageList()
    L.append(im1)
    L.append(im2)
    
    p = StdoutProgressIndicator('Testing')
    p.start('foo', '', 102)
    import time
    for i in range(100):
        time.sleep(0.02)
        p.set_progress(i)
    p.finish('Hooray')
    
    p.start('bar', 'items', 80)
    import time
    for i in range(100):
        time.sleep(0.02)
        p.set_progress(i)
    p.fail('Too little items found')
    
        
    
    