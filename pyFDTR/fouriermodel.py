from sympy import *
from .domain import *
from pyFDTR.util import complex_quadrature
import numpy as np

class FourierModelFDTR:

	matrix = None
	lfunction = None

	def __init__(self,domain,rpump,rprobe):
		self.domain=domain
		self.rpump=rpump
		self.rprobe=rprobe

	def set_frequency(self,frequency=200):
		self.frequency = frequency

	def tointegrate(self, chi_var):
		return complex(self.lfunction(chi_var))


	def get_phase(self,frequency):
		self.frequency = frequency
		self.domain.calc_transfer_matrix()
		self.matrix = self.domain.matrix
		chi = symbols('chi')
		omega = symbols('omega')
		Lintegrand =  (1 / (2 * pi) ) * chi * exp( -( (self.rprobe**2 + self.rpump **2) * chi ** 2 ) / (8) ) * ( - self.matrix[1,1] / self.matrix[1,0] )
		self.integrand = Lintegrand.subs(omega,self.frequency)
		self.lfunction = lambdify(chi,self.integrand,'mpmath')
		upperbound = 2 / sqrt(self.rpump ** 2 + self.rprobe ** 2)
		result = complex_quadrature(self.tointegrate,0,upperbound)
		return -(90 + (180*np.arctan(np.imag(result[0])/np.real(result[0]))/np.pi))



