


class Constants:
    
    kb = 1.380649e-23   # Boltzman constant


from enum import Enum

class Unit(float, Enum):
    nm = 1e-7
    um  = 1e-4
    m = 1e2
    W_mK = 1e-2
    J_m3K = 1e-6
    W_m2K = 1e-4


class Conversion_class:

    def J_gK_to_J_m3K(self, value, density_gm3):
        return value*density_gm3
    
    def to_J_m3Ks(self, value):
        return value/Unit.J_m3K
    
    def to_W_mK(self, value):
        return value/Unit.W_mK
    
    def to_nm(self, value):
        return value/Unit.nm
    
    def to_um(self, value):
        return value/Unit.um
    
    def to_m(self, value):
        return value/Unit.m

    def to_W_m2K(self, value):
        return value/Unit.W_m2K

Conversion = Conversion_class()

import numpy as np
from scipy.integrate import quad

def complex_quadrature(func, a, b, **kwargs):
    def real_func(x):
        return np.real(func(x))
    def imag_func(x):
        return np.imag(func(x))
    real_integral = quad(real_func, a, b, **kwargs)
    imag_integral = quad(imag_func, a, b, **kwargs)
    return (real_integral[0] + 1j*imag_integral[0], real_integral[1:], imag_integral[1:])
