import ctypes
import numpy as np
import numba
from contextlib import contextmanager

_CTYPES_TO_NP = {
    ctypes.c_float:   np.float32,
    ctypes.c_double:  np.float64,
    ctypes.c_int32:   np.int32,
    ctypes.c_uint32:  np.uint32,
    ctypes.c_int16:   np.int16,
    ctypes.c_uint16:  np.uint16,
    ctypes.c_int8:    np.int8,
    ctypes.c_uint8:   np.uint8,
}

def _arraytonumpy(shared_array, shape=None, dtype=None):
    """
    Covert a shared array to a numpy array

    Originally from pyklip Wang, J. J., Ruffio, J.-B., De Rosa, R. J., et al. 2015, ASCL, ascl:1506.001
    https://bitbucket.org/pyKLIP/pyklip/src/main/pyklip/parallelized.py

    Args:
        shared_array: a multiprocessing.Array array
        shape: a shape for the numpy array. otherwise, will assume a 1d array
        dtype: data type of the arrays. Should be either ctypes.c_float(default) or ctypes.c_double

    Returns:
        numpy_array: numpy array for vectorized operation. still points to the same memory!
                     returns None is shared_array is None
    """
    if dtype is None:
        dtype = ctypes.c_float
    np_dtype = _CTYPES_TO_NP.get(dtype)

    # if you passed in nothing you get nothing
    if shared_array is None:
        return None

    buf = shared_array.get_obj() if hasattr(shared_array, "get_obj") else shared_array
    numpy_array = np.frombuffer(buf, dtype=np_dtype)
    # numpy_array = np.frombuffer(shared_array.get_obj(), dtype=dtype)
    if shape is not None:
        numpy_array.shape = shape

    return numpy_array

@contextmanager
def numba_thread_scope(num_threads : int):
    """
    Context manager to temporarily set the number of threads used by numba, and reset when finished.

    Parameters
    ----------
    num_threads
        The number of threads to set.

    Examples
    --------
    with numba_thread_scope(num_threads):
        # Numba calls here
    """
    original_num_threads = numba.get_num_threads()
    numba.set_num_threads(num_threads)
    try:
        yield
    finally:
        numba.set_num_threads(original_num_threads)