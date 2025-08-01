from sympy import *
from triton import jit
from .domain import *
from pyFDTR.util import complex_quadrature
import numpy as np
import mpmath
from scipy import integrate
from functools import lru_cache
import numba
from numba import njit


class FourierModelFDTR:

	def __init__(self,domain,rpump,rprobe, beamoffset = 0, backend='numpy', precision=15, jit=True):
		self.precision = precision
		self.domain=domain   # Defined domain (layers + temperature + ..)
		self.rpump=rpump  	 # Pump beam radius 1/e2
		self.rprobe=rprobe   # Probe beam radius 1/e2
		self.beamoffset = beamoffset
		self.matrix = None
		self.topmatrix = None
		self.lfunction = None
		self.backend = backend  # Set backend for calculations
		
		if self.matrix == None: 
			self.domain.calc_transfer_matrix()  # Calculate layers heat transfer matrix
			self.matrix = self.domain.matrix
		
		if self.domain.top_heat_path and self.topmatrix == None: 
			self.domain.calc_top_transfer_matrix() 
			self.topmatrix = self.domain.topmatrix
		else:
			self.topmatrix = None
		


		if self.beamoffset == 0:
			# Calculate function to be integrated "Inverse Hankel"
			eta = symbols('eta')
			eps = symbols('eps')
			omega = symbols('omega')
			if self.topmatrix == None:
				Lintegrand =  (1 / (2.0 * pi) ) * eps * exp( -( (self.rprobe * self.rprobe + self.rpump * self.rpump ) * eps* eps ) / (8) ) * \
					( - self.matrix[1,1] / self.matrix[1,0] )
			else:
				Lintegrand =  (1 / (2.0 * pi) ) * eps * exp( -( (self.rprobe * self.rprobe + self.rpump * self.rpump ) * eps* eps ) / (8) ) * \
					( (-self.matrix[1,1] / self.matrix[1,0]) / (1 + ((self.matrix[1,1]*self.topmatrix[1,0]) / (self.matrix[1,0]*self.topmatrix[0,0])) ))

			self.integrand = Lintegrand.evalf(self.precision,subs={eta: 0.0})
			if self.backend == 'numpy':
				self.lfunction = lambdify([eps,omega],self.integrand,'numpy')
			elif self.backend == 'mpmath':
				self.lfunction = lambdify([eps,omega],self.integrand,'mpmath')
			if jit:
				# Compile the function for better performance
				# Note: Numba's njit does not support lambdify functions directly, so we use lambdify with numpy backend
				# and then compile the resulting function with njit.
				self.lfunction = njit(self.lfunction)  # Compile the function for better performance
			

		else:
			# Calculate function to be integrated "Inverse Hankel"
			eta = symbols('eta')
			eps = symbols('eps')
			omega = symbols('omega')
			Lintegrand =  (1 / (2.0 * pi)**2 ) * exp( -( (self.rprobe ** 2 + self.rpump ** 2) * (eps**2 + eta**2 )) / (8) ) *  exp(complex(0,1)*eps*self.beamoffset) * ( - self.matrix[1,1] / self.matrix[1,0] )
			self.integrand = Lintegrand.evalf(self.precision)
			if self.backend == 'numpy':
				self.lfunction = lambdify([eps,eta,omega],self.integrand,'numpy')
			elif self.backend == 'mpmath':
				self.lfunction = lambdify([eps,eta,omega],self.integrand,'mpmath')
			if jit:
				self.lfunction = njit(self.lfunction)  # Compile the function for better performance


	def tointegrate2D_mpmath(self, x,y):
		return self.lfunction(x,y,self.omega)

	def tointegrate_mpmath(self, x):
		return self.lfunction(x, self.omega)


	def tointegrate(self, x):
		return complex(self.lfunction(x, self.omega))

	def tointegrate2D(self, x):
		return self.lfunction(x[0], x[1], self.omega)


	def tointegrate2D_real(self, x,y):
		return float(np.real(self.lfunction(x,y,self.omega)))


	def tointegrate2D_imag(self, x,y):
		return float(np.imag(self.lfunction(x,y,self.omega)))

	def get_phase(self,frequency):

		if self.matrix == None: 
			self.domain.calc_transfer_matrix()  # Calculate layers heat transfer matrix
			self.matrix = self.domain.matrix
		
		if self.domain.top_heat_path and self.topmatrix == None: 
			self.domain.calc_top_transfer_matrix() 
			self.topmatrix = self.domain.topmatrix
		else:
			self.topmatrix = None

		self.omega = 2.0*np.pi*frequency
		
		if self.backend == 'numpy':
			if self.beamoffset == 0:
				
				# integration
				upperbound = 20.0 / np.sqrt(self.rpump * self.rpump + self.rprobe * self.rprobe)
				result = complex_quadrature(self.tointegrate,0.0,upperbound,epsrel=1e-10)

				calc_phase = 180*np.arctan(np.imag(result[0])/np.real(result[0]))/np.pi

			else:
				
				# integration
				upperbound = 20.0 / np.sqrt(self.rpump * self.rpump + (self.rprobe)*(self.rprobe))
				#print(upperbound)

				#scheme = quadpy.c2._witherden_vincent.witherden_vincent_21()
				#scheme = quadpy.c2._burnside.burnside()

				result_real = integrate.dblquad(self.tointegrate2D_real,-upperbound, upperbound, -upperbound, upperbound,epsrel=1e-6)
				result_imag = integrate.dblquad(self.tointegrate2D_imag,-upperbound, upperbound, -upperbound, upperbound,epsrel=1e-6)

				calc_phase = 180*np.arctan(result_imag[0]/result_real[0])/np.pi
		elif self.backend == 'mpmath':
			mpmath.dps = self.precision; mpmath.pretty = True
			if self.beamoffset == 0:
				# Calculate function to be integrated "Inverse Hankel"				
				upperbound = 20.0 / np.sqrt(self.rpump * self.rpump + self.rprobe * self.rprobe)
				result = mpmath.quad(self.tointegrate_mpmath,[0.0, upperbound])
			else:
				# integration
				upperbound = 20.0 / np.sqrt(self.rpump * self.rpump + (self.rprobe+self.beamoffset)*(self.rprobe+self.beamoffset))

				result = mpmath.quad(self.tointegrate2D_mpmath,[-upperbound, upperbound], [-upperbound, upperbound])

			calc_phase =  180*mpmath.atan(result.imag/result.real)/mpmath.pi
			

		if calc_phase < 0 :
			return calc_phase
		else: 
			return calc_phase-180


	def update(self):
		if self.matrix == None: 
			self.domain.calc_transfer_matrix()  # Calculate layers heat transfer matrix
			self.matrix = self.domain.matrix
		
		if self.domain.top_heat_path and self.topmatrix == None: 
			self.domain.calc_top_transfer_matrix() 
			self.topmatrix = self.domain.topmatrix
		else:
			self.topmatrix = None
		


		if self.beamoffset == 0:
			# Calculate function to be integrated "Inverse Hankel"
			eta = symbols('eta')
			eps = symbols('eps')
			omega = symbols('omega')
			if self.topmatrix == None:
				Lintegrand =  (1 / (2.0 * pi) ) * eps * exp( -( (self.rprobe * self.rprobe + self.rpump * self.rpump ) * eps* eps ) / (8) ) * \
					( - self.matrix[1,1] / self.matrix[1,0] )
			else:
				Lintegrand =  (1 / (2.0 * pi) ) * eps * exp( -( (self.rprobe * self.rprobe + self.rpump * self.rpump ) * eps* eps ) / (8) ) * \
					( (-self.matrix[1,1] / self.matrix[1,0]) / (1 + ((self.matrix[1,1]*self.topmatrix[1,0]) / (self.matrix[1,0]*self.topmatrix[0,0])) ))

			self.integrand = Lintegrand.evalf(12,subs={eta: 0.0})
			if self.backend == 'numpy':
				self.lfunction = lambdify([eps,omega],self.integrand,'numpy')
			elif self.backend == 'mpmath':
				self.lfunction = lambdify([eps,omega],self.integrand,'mpmath')
			if jit:
				self.lfunction = njit(self.lfunction)  # Compile the function for better performance

		else:
			# Calculate function to be integrated "Inverse Hankel"
			eta = symbols('eta')
			eps = symbols('eps')
			omega = symbols('omega')
			Lintegrand =  (1 / (2.0 * pi)**2 ) * exp( -( (self.rprobe ** 2 + self.rpump ** 2) * (eps**2 + eta**2 )) / (8) ) *  exp(complex(0,1)*eps*self.beamoffset) * ( - self.matrix[1,1] / self.matrix[1,0] )
			if self.backend == 'numpy':
				self.lfunction = lambdify([eps,eta,omega],self.integrand,'numpy')
			elif self.backend == 'mpmath':
				self.lfunction = lambdify([eps,eta,omega],self.integrand,'mpmath')
			if jit:
				self.lfunction = njit(self.lfunction)  # Compile the function for better performance

	# def get_phase_scipy(self,frequency):
	# 	self.frequency = frequency  # Set frequency 
	# 	if self.matrix == None: 
	# 		self.domain.calc_transfer_matrix()  # Calculate layers heat transfer matrix
	# 		self.matrix = self.domain.matrix
		
	# 	# Calculate function to be integrated "Inverse Hankel"
	# 	eta = symbols('eta')
	# 	eps = symbols('eps')
	# 	omega = symbols('omega')
	# 	Lintegrand =  (1 / (2.0 * pi)**2 ) * exp( -( (self.rprobe ** 2 + self.rpump ** 2) * (eps**2 + eta**2 )) / (8) ) *  exp(complex(0,1)*eps*self.beamoffset) * ( - self.matrix[1,1] / self.matrix[1,0] )
	# 	self.integrand = Lintegrand.subs(omega,2.0*np.pi*self.frequency)
	# 	self.lfunction = lambdify([eps,eta],self.integrand,'numpy')
		
	# 	# integration
	# 	upperbound = 20.0 / np.sqrt(self.rpump * self.rpump + (self.rprobe)*(self.rprobe))
	# 	result_real = integrate.dblquad(self.tointegrate2D_real,-upperbound, upperbound, -upperbound, upperbound,epsrel=1e-6)
	# 	result_imag = integrate.dblquad(self.tointegrate2D_imag,-upperbound, upperbound, -upperbound, upperbound,epsrel=1e-6)

	# 	return 180*np.arctan(result_imag[0]/result_real[0])/np.pi