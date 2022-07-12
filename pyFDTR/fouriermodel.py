from sympy import *
from .domain import *
from pyFDTR.util import complex_quadrature
import numpy as np

class FourierModelFDTR:

	matrix = None
	lfunction = None

	def __init__(self,domain,rpump,rprobe):
		self.domain=domain   # Defined domain (layers + temperature + ..)
		self.rpump=rpump  	 # Pump beam radius 1/e2
		self.rprobe=rprobe   # Probe beam radius 1/e2

	def set_frequency(self,frequency=200):
		self.frequency = frequency

	def tointegrate(self, chi_var):
		return complex(self.lfunction(chi_var))


	def get_phase(self,frequency):
		self.frequency = frequency  # Set frequency 
		self.domain.calc_transfer_matrix()  # Calculate layers heat transfer matrix
		self.matrix = self.domain.matrix
		
		# Calculate function to be integrated "Inverse Hankel"
		chi = symbols('chi')
		omega = symbols('omega')
		Lintegrand =  (1 / (2 * pi) ) * chi * exp( -( (self.rprobe**2 + self.rpump **2) * chi ** 2 ) / (8) ) * ( - self.matrix[1,1] / self.matrix[1,0] )
		self.integrand = Lintegrand.subs(omega,self.frequency)
		self.lfunction = lambdify(chi,self.integrand,'mpmath')
		
		# integration
		upperbound = 2 / sqrt(self.rpump ** 2 + self.rprobe ** 2)
		result = complex_quadrature(self.tointegrate,0,upperbound, epsrel=1.0e-7)
		
		return -(90 + (180*np.arctan(np.imag(result[0])/np.real(result[0]))/np.pi))



