import numpy as np
import sys

__all__ = ['convert_endianness']

# def normalize_array_dtype(arr : np.ndarray, dtype : np.dtype | None = None):
#     """
#     Converts arrays to little endian.
    
#     Parameters
#     ----------
#     arr : np.ndarray
#         Input array to be normalized.
#     dtype : numpy datatype, optional
#         Desired data-type for the output array. If None, uses the type of the input array.

#     Returns
#     -------
#     np.ndarray
#         Array with the specified data-type. Operation is done without copying if the array is already of the desired type.
#     """
#     if dtype is not None:
#         return np.dtype(arr.dtype).type
#     return arr.astype(dtype, copy=False)

def convert_endianness(arr : np.ndarray, output_endianness : str = 'little'):
    if arr.dtype.byteorder == '=':
        current_endianness = sys.byteorder
    elif arr.dtype.byteorder == '<':
        current_endianness = 'little'
    else:   
        current_endianness = 'big'
    if current_endianness != output_endianness:
        return arr.byteswap().view(arr.dtype.newbyteorder(output_endianness))
    else:
        return arr