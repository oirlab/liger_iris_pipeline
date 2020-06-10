cdef extern from "../iris_readout/src/drsrop.c":
    float* uptheramp (int* arr, int* time, int a, int b, int c)
    float* mcds (int* arr, int* time, int a, int b, int c, int num_coadd)
    float* nonlin_corr (int* arr, int* time, int a, int b, int c, int x0, int y0, float* c0, float* c1, float* c2, float* c3, float* c4)
import numpy as np
cimport numpy as np

def uptheramp_c(int[:,:,:] arr_f, int[:] arr_time):
    cdef float[:,:] results = <float[:arr_f.shape[1],:arr_f.shape[2]]> uptheramp(&arr_f[0,0,0], &arr_time[0], arr_f.shape[0], arr_f.shape[1], arr_f.shape[2])
    return np.asarray(results)
    
def mcds_c(int[:,:,:] arr_f, int[:] arr_time, int num_coadd):
    cdef float[:,:] results = <float[:arr_f.shape[1],:arr_f.shape[2]]> mcds(&arr_f[0,0,0], &arr_time[0], arr_f.shape[0], arr_f.shape[1], arr_f.shape[2], num_coadd)
    return np.asarray(results)

def nonlin_c(int[:,:,:] arr_f, int[:] arr_time, float[:,:] arr_c0, float[:,:] arr_c1, float[:,:] arr_c2, float[:,:] arr_c3, float[:,:] arr_c4):
    cdef float[:,:,:] results = <float[:arr_f.shape[0],:arr_f.shape[1],:arr_f.shape[2]]> nonlin_corr(&arr_f[0,0,0], &arr_time[0], arr_f.shape[0], arr_f.shape[1], arr_f.shape[2],0,0, &arr_c0[0,0],&arr_c1[0,0],&arr_c2[0,0],&arr_c3[0,0],&arr_c4[0,0] )
    return np.asarray(results)
