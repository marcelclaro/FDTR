


class Constants:
    
    kb = 1.380649e-23   # Boltzman constant

class Conversion:

    def J_gK_to_J_m3K(self, value, density_gm3):
        return value*density_gm3
    
    def nm(self, value):
        return value*1e-7

    def um(self, value):
        return value*1e-4


import scipy
from scipy.integrate import quad

def complex_quadrature(func, a, b, **kwargs):
    def real_func(x):
        return scipy.real(func(x))
    def imag_func(x):
        return scipy.imag(func(x))
    real_integral = quad(real_func, a, b, **kwargs)
    imag_integral = quad(imag_func, a, b, **kwargs)
    return (real_integral[0] + 1j*imag_integral[0], real_integral[1:], imag_integral[1:])
