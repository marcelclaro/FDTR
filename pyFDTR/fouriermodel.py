from sympy import *
from .domain import *
from pyFDTR.util import complex_quadrature

class FourierModelFDTR:

	precision = 7

	def __init__(self,domain,rpump,rprobe):
		self.domain=domain
		self.rpump=rpump
		self.rprobe=rprobe

	def tointegrate(self, chi_var,frequency=200):
		chi = symbols('chi')
		omega = symbols('omega')
		matrix = self.domain.matrix
		Lintegrand =  (1 / (2 * pi) ) * chi * exp( -( (self.rprobe**2 + self.rpump **2) * chi ** 2 ) / (8) ) * ( - matrix[1,1] / matrix[1,0] )
		complex(Lintegrand.subs(chi,chi_var).subs(omega,frequency).evalf(self.precision))


	def get_phase(self,frequency=200):
		upperbound = 2 / sqrt(self.rpump ** 2 + self.rprobe ** 2)
		result = complex_quadrature(self.tointegrate,0,upperbound)[0]



def get_L_zero_one(c,d,rzero,rone):
	chi = symbols('chi')
	upperbound = 2 / sqrt(rzero ** 2 + rone ** 2)
	Lintegrand =  (1 / (2 * pi) ) * chi * exp( -( (rzero**2 + rone**2) * chi ** 2 ) / (8) ) * ( - d / c )
	return Lintegrand #integrate(Lintegrand, (chi, 0, upperbound))

