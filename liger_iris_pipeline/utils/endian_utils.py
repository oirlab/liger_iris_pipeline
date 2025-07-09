import numpy as np

__all__ = ['normalize_dtype_array']

def normalize_dtype_array(arr):
    return arr.astype(np.dtype(arr.dtype).type, copy=False)