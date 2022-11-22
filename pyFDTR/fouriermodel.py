from sympy import *
from .domain import *
from pyFDTR.util import complex_quadrature
import numpy as np
import quadpy
import mpmath
from scipy import integrate
from numba import njit

class FourierModelFDTR:

	def __init__(self,domain,rpump,rprobe, beamoffset = 0):
		self.domain=domain   # Defined domain (layers + temperature + ..)
		self.rpump=rpump  	 # Pump beam radius 1/e2
		self.rprobe=rprobe   # Probe beam radius 1/e2
		self.beamoffset = beamoffset
		self.matrix = None
		self.lfunction = None


	def tointegrate2D_mpmath(self, x,y):
		return self.lfunction(x,y)
	
	def tointegrate_mpmath(self, x):
		return self.lfunction(x)


	def tointegrate(self, x):
		return complex(self.lfunction(x))

	def tointegrate2D(self, x):
		return self.lfunction(x[0],x[1])


	def tointegrate2D_real(self, x,y):
		return np.real(self.lfunction(x,y))


	def tointegrate2D_imag(self, x,y):
		return np.imag(self.lfunction(x,y))

	
	def get_phase(self,frequency):
		self.frequency = frequency  # Set frequency 
		if self.matrix == None: 
			self.domain.calc_transfer_matrix()  # Calculate layers heat transfer matrix
			self.matrix = self.domain.matrix
		
		if self.beamoffset == 0:
			# Calculate function to be integrated "Inverse Hankel"
			eta = symbols('eta')
			eps = symbols('eps')
			omega = symbols('omega')
			Lintegrand =  (1 / (2.0 * pi) ) * eps * exp( -( (self.rprobe * self.rprobe + self.rpump * self.rpump ) * eps* eps ) / (8) ) * ( - self.matrix[1,1] / self.matrix[1,0] )
			self.integrand = Lintegrand.subs(eta,0.0)
			self.integrand = self.integrand.subs(omega,2.0*np.pi*self.frequency)
			self.lfunction = lambdify(eps,self.integrand,'numpy')
			
			# integration
			upperbound = 4.0 / np.sqrt(self.rpump * self.rpump + self.rprobe * self.rprobe)
			result = complex_quadrature(self.tointegrate,0.0,upperbound,epsrel=1e-7)

			calc_phase = 180*np.arctan(np.imag(result[0])/np.real(result[0]))/np.pi

		else:
			# Calculate function to be integrated "Inverse Hankel"
			eta = symbols('eta')
			eps = symbols('eps')
			omega = symbols('omega')
			Lintegrand =  (1 / (2.0 * pi)**2 ) * exp( -( (self.rprobe ** 2 + self.rpump ** 2) * (eps**2 + eta**2 )) / (8) ) *  exp(complex(0,1)*eps*self.beamoffset) * ( - self.matrix[1,1] / self.matrix[1,0] )
			self.integrand = Lintegrand.subs(omega,2.0*np.pi*self.frequency)
			self.lfunction = lambdify([eps,eta],self.integrand,'numpy')
			
			# integration
			upperbound = 20.0 / np.sqrt(self.rpump * self.rpump + (self.rprobe)*(self.rprobe))
			#print(upperbound)

			#scheme = quadpy.c2._witherden_vincent.witherden_vincent_21()
			scheme = quadpy.c2._sommariva.sommariva_51()
			#scheme = quadpy.c2._burnside.burnside()
			result = scheme.integrate(self.tointegrate2D,quadpy.c2.rectangle_points([0.0, upperbound], [0.0, upperbound]))
			result += scheme.integrate(self.tointegrate2D,quadpy.c2.rectangle_points([0.0, upperbound], [0.0, -upperbound]))
			result += scheme.integrate(self.tointegrate2D,quadpy.c2.rectangle_points([-upperbound,0.0], [0.0 ,upperbound]))
			result += scheme.integrate(self.tointegrate2D,quadpy.c2.rectangle_points([-upperbound, 0.0 ], [0.0,-upperbound]))

			calc_phase = 180*np.arctan(np.imag(result)/np.real(result))/np.pi

		if calc_phase < 0 :
			return calc_phase
		else: 
			return calc_phase-180


	def get_phase_mpmath(self,frequency):
		self.frequency = frequency  # Set frequency 
		if self.matrix == None: 
			self.domain.calc_transfer_matrix()  # Calculate layers heat transfer matrix
			self.matrix = self.domain.matrix
		if self.beamoffset == 0:
			# Calculate function to be integrated "Inverse Hankel"
			eta = symbols('eta')
			eps = symbols('eps')
			omega = symbols('omega')
			Lintegrand =  (1 / (2.0 * pi) ) * eps * exp( -( (self.rprobe * self.rprobe + self.rpump * self.rpump ) * eps* eps ) / (8) ) * ( - self.matrix[1,1] / self.matrix[1,0] )
			self.integrand = Lintegrand.subs(eta,0.0)
			self.integrand = self.integrand.subs(omega,2.0*np.pi*self.frequency)
			self.lfunction = lambdify(eps,self.integrand,'math')

			upperbound = 4.0 / np.sqrt(self.rpump * self.rpump + self.rprobe * self.rprobe)

			result = mpmath.quad(self.tointegrate_mpmath,[0.0, upperbound])
		else:
			# Calculate function to be integrated "Inverse Hankel"
			eta = symbols('eta')
			eps = symbols('eps')
			omega = symbols('omega')
			Lintegrand =  (1 / (2.0 * pi)**2 ) * exp( -( (self.rprobe ** 2 + self.rpump ** 2) * (eps**2 + eta**2 )) / (8) ) *  exp(complex(0,1)*eps*self.beamoffset) * ( - self.matrix[1,1] / self.matrix[1,0] )
			self.integrand = Lintegrand.subs(omega,2.0*np.pi*self.frequency)
			self.lfunction = lambdify([eps,eta],self.integrand,'mpmath')
			
			# integration
			upperbound = 2.0 / np.sqrt(self.rpump * self.rpump + (self.rprobe+self.beamoffset)*(self.rprobe+self.beamoffset))

			result = mpmath.quad(self.tointegrate2D_mpmath,[-upperbound, upperbound], [-upperbound, upperbound])

		calc_phase =  180*mpmath.atan(result.imag/result.real)/mpmath.pi
	
		if calc_phase < 0 :
			return calc_phase
		else: 
			return calc_phase-180

	def get_phase_scipy(self,frequency):
		self.frequency = frequency  # Set frequency 
		if self.matrix == None: 
			self.domain.calc_transfer_matrix()  # Calculate layers heat transfer matrix
			self.matrix = self.domain.matrix
		
		# Calculate function to be integrated "Inverse Hankel"
		eta = symbols('eta')
		eps = symbols('eps')
		omega = symbols('omega')
		Lintegrand =  (1 / (2.0 * pi)**2 ) * exp( -( (self.rprobe ** 2 + self.rpump ** 2) * (eps**2 + eta**2 )) / (8) ) *  exp(complex(0,1)*eps*self.beamoffset) * ( - self.matrix[1,1] / self.matrix[1,0] )
		self.integrand = Lintegrand.subs(omega,2.0*np.pi*self.frequency)
		self.lfunction = lambdify([eps,eta],self.integrand,'numpy')
		
		# integration
		upperbound = 20.0 / np.sqrt(self.rpump * self.rpump + (self.rprobe)*(self.rprobe))
		result_real = integrate.dblquad(self.tointegrate2D_real,-upperbound, upperbound, -upperbound, upperbound,epsrel=1e-6)
		result_imag = integrate.dblquad(self.tointegrate2D_imag,-upperbound, upperbound, -upperbound, upperbound,epsrel=1e-6)

		return 180*np.arctan(result_imag[0]/result_real[0])/np.pi