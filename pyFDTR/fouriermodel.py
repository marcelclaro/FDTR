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
import lmfit


class Fitting_parameters:
    
	class Fitting_parameter:
		def __init__(self, name, value, min=None, max=None):
			self.name = name
			self.value = value
			self.min = min
			self.max = max
			self.sympy_symbol = symbols(name)  # Create a sympy symbol for the parameter

	def __init__(self):
		self.parameters = []

	def add(self, name, value, min=None, max=None):
		param = self.Fitting_parameter(name, value, min, max)
		self.parameters.append(param)

	def get_parameter(self, name):
		for param in self.parameters:
			if param.name == name:
				return param.sympy_symbol

		raise ValueError(f"Parameter '{name}' not found")
	


class FourierModelFDTR:		

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

			self.integrand = Lintegrand.evalf(self.precision,subs={eta: 0.0})
			if self.backend == 'numpy':
				if self.fitting_params is None:
					self.lfunction = lambdify([eps,omega],self.integrand,'numpy')
				else:
					# If fitting parameters are provided, include them in the lambdify function
					# This allows for dynamic parameter updates during minimization
					self.lfunction = lambdify([eps,omega,*[param.sympy_symbol for param in self.fitting_params.parameters]],self.integrand,'numpy')
			elif self.backend == 'mpmath':
				if self.fitting_params is None:
					self.lfunction = lambdify([eps,omega],self.integrand,'mpmath')
				else:
					# If fitting parameters are provided, include them in the lambdify function
					# This allows for dynamic parameter updates during minimization
					self.lfunction = lambdify([eps,omega,*[param.sympy_symbol for param in self.fitting_params.parameters]],self.integrand,'mpmath')
			if self.use_jit:
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
				if self.fitting_params is None:
					self.lfunction = lambdify([eps,eta,omega],self.integrand,'numpy')
				else:
					self.lfunction = lambdify([eps,eta,omega,*[param.sympy_symbol for param in self.fitting_params.parameters]],self.integrand,'numpy')
			elif self.backend == 'mpmath':
				if self.fitting_params is None:
					self.lfunction = lambdify([eps,eta,omega],self.integrand,'mpmath')
				else:
					self.lfunction = lambdify([eps,eta,omega,*[param.sympy_symbol for param in self.fitting_params.parameters]],self.integrand,'mpmath')
			if self.use_jit:
				self.lfunction = njit(self.lfunction)  # Compile the function for better performance

	def __init__(self,domain,rpump,rprobe, beamoffset = 0, backend='numpy', precision=15, jit=True, fitting_params=None):
		self.precision = precision
		self.domain=domain   # Defined domain (layers + temperature + ..)
		self.rpump=rpump  	 # Pump beam radius 1/e2
		self.rprobe=rprobe   # Probe beam radius 1/e2
		self.beamoffset = beamoffset
		self.matrix = None
		self.topmatrix = None
		self.lfunction = None
		self.backend = backend  # Set backend for calculations
		self.use_jit = jit  # Use JIT compilation if True
		self.fitting_params = fitting_params
		self.lmfit_params = None  # Initialize lmfit parameters


		self.update()  # Update the model to calculate the transfer matrix and integrand function

	def tointegrate2D_mpmath(self, x,y):
		if self.lmfit_params is None:
			return self.lfunction(x, y, self.omega)
		else:
			return self.lfunction(x, y, self.omega, *[self.lmfit_params[key].value for key in self.lmfit_params.valuesdict().keys()])

	def tointegrate_mpmath(self, x):
		if self.lmfit_params is None:
			return self.lfunction(x, self.omega)
		else:
			# If fitting parameters are provided, include them in the function call
			# This allows for dynamic parameter updates during minimization
			return self.lfunction(x, self.omega,*[self.lmfit_params[key].value for key in self.lmfit_params.valuesdict().keys()])


	def tointegrate(self, x):
		if self.lmfit_params is None:
			return complex(self.lfunction(x, self.omega))
		else:
			return complex(self.lfunction(x, self.omega,*[self.lmfit_params[key].value for key in self.lmfit_params.valuesdict().keys()]))

	def tointegrate2D(self, x):
		if self.lmfit_params is None:
			return self.lfunction(x[0], x[1], self.omega)
		else:
			return self.lfunction(x[0], x[1], self.omega,*[self.lmfit_params[key].value for key in self.lmfit_params.valuesdict().keys()])


	def tointegrate2D_real(self, x,y):
		if self.lmfit_params is None:
			return float(np.real(self.lfunction(x,y,self.omega)))
		else:
			return float(np.real(self.lfunction(x,y,self.omega,*[self.lmfit_params[key].value for key in self.lmfit_params.valuesdict().keys()])))


	def tointegrate2D_imag(self, x,y):
		if self.lmfit_params is None:
			return float(np.imag(self.lfunction(x,y,self.omega)))
		else:
			return float(np.imag(self.lfunction(x,y,self.omega,*[self.lmfit_params[key].value for key in self.lmfit_params.valuesdict().keys()])))

	def get_phase(self,frequency):

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

	def minimize(self,experimental_points,method='differential_evolution',range=(0,-1),max_nfev=1000):
		"""
		Minimize the difference between the model and experimental data.
		"""
		parameter = lmfit.Parameters()
		for param in self.fitting_params.parameters:
			parameter.add(param.name, value=param.value, min=param.min, max=param.max)
		self.lmfit_params = parameter

		# Check if lmfit_params order matches fitting_params order
		lmfit_keys = list(self.lmfit_params.valuesdict().keys())
		fitting_param_names = [param.name for param in self.fitting_params.parameters]
		if lmfit_keys != fitting_param_names:
			raise ValueError(f"Order mismatch: lmfit_params keys {lmfit_keys} != fitting_params names {fitting_param_names}")

		#Here we define our error function, replace the parameters that you want to vary with params['name'].value
		def residuals(params, freq, measured):
			# Update the model's parameters with the current values from params
			for param in self.fitting_params.parameters:
				setattr(self, param.name, params[param.name].value)
				self.lmfit_params[param.name].value = params[param.name].value
			phase = []
			for i, f in enumerate(freq):
				phase.append(self.get_phase(f))
			return np.array(phase) - np.array(measured)

		out = lmfit.minimize(residuals, self.lmfit_params, args=(experimental_points[range[0]:range[1],0],experimental_points[range[0]:range[1],1]), method=method,max_nfev=max_nfev)
		
		return out
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