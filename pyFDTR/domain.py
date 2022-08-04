from sympy import *

from pyFDTR.materials import sapphire,default_material


class Domain:
	substrate_defined = False

	def __init__(self, temperature = 300):
		self.heat_path = []
		self.temperature = temperature


	def set_temperature(self, temperature):
		self.temperature = temperature
		for layers in self.heat_path:
			layers.set_temperature(temperature)
			layers.update()


	def add_substrate(self, material):
		if( not self.substrate_defined):
			if material == None: material=sapphire(self.temperature)
			self.heat_path.append(Layer(0.001,self.temperature,material(self.temperature)))
			self.substrate_defined = True
		else:
			print('Substrate already defined!')

	def add_layer(self, thickness, material):
		if material == None: material= default_material(self.temperature)
		self.heat_path.append(LayerInterface(self.temperature,self.heat_path[-1].material,material))
		self.heat_path.append(Layer(thickness,self.temperature,material(self.temperature)))

	def set_layer_param(self, index, thickness, cp, density, kt, kp):
		self.heat_path[index*2].thickness = thickness
		self.heat_path[index*2].cp = cp
		self.heat_path[index*2].density = density
		self.heat_path[index*2].kt = kt
		self.heat_path[index*2].kp = kp

	def set_layer_param(self, index, **parameter):
		if 'cp' in parameter: self.heat_path[index*2].cp = parameter['cp']
		if 'density' in parameter: self.heat_path[index*2].density = parameter['density']
		if 'kt' in parameter: self.heat_path[index*2].kt = parameter['kt']
		if 'kp' in parameter: self.heat_path[index*2].kp = parameter['kp']

	def set_interface_condu(self, index, g):
		self.heat_path[ (index * 2) - 1].g = g

	def calc_transfer_matrix(self):
		matrix = Matrix([ [1,0],
					      [0,1]])
		for layer_or_interface in self.heat_path:
			matrix *= layer_or_interface.getFourier_Matrix()
		self.matrix = matrix



class Heatpath:
	def getFourier_Matrix():
		return Matrix([[1,0],[0,1]])

class Layer(Heatpath):
	
	cp = 2.0e6  # Cp - Heat capacity 
	kt = 25 # kappa_trans - Heat conductivity transverse (normal) to the surface
	kp = 25  # kappa_parallel - Heat conductivity parallel to the surface
	density = 110.0  #Material density
	
	def set_layer_param(self, cp, density, kt, kp):
		self.cp = cp
		self.density = density
		self.kt = kt
		self.kp = kp

	def set_temperature(self, temperature):
		self.material.set_temperature(temperature)

	def update(self):
		self.cp = self.material.cp
		self.density = self.material.density
		self.kt = self.material.kt
		self.kp = self.material.kp


	def set_layer_param(self, **parameter):
		if 'cp' in parameter: self.cp = parameter['cp']
		if 'density' in parameter: self.density = parameter['density']
		if 'kt' in parameter: self.kt = parameter['kt']
		if 'kp' in parameter: self.kp = parameter['kp']
		if 'thickness' in parameter: self.thickness = parameter['thickness']


	def getFourier_Matrix(self):
		chi = symbols('chi')
		omega = symbols('omega')
		mu = sqrt( (self.kp*chi*chi+complex(0,1)*self.cp*omega)/self.kt )
		return Matrix([[cosh(mu*self.thickness),-(1/(self.kt*mu))*sinh(mu*self.thickness)],
					   [-(self.kt*mu)*sinh(mu*self.thickness),cosh(mu*self.thickness)]])

	def __init__(self, thickness, temperature, material):
		self.thickness = thickness
		self.temperature = temperature
		self.material = material
		self.cp = self.material.cp
		self.density = self.material.density
		self.kt = self.material.kt
		self.kp = self.material.kp


class LayerInterface(Heatpath):
	g = 1e6 # Interface heat conductivity

	def getFourier_Matrix(self):
		return Matrix([ [ 1 , -1/self.g ],
					    [ 0 , 1 ]])

	def set_conductance(self, g):
		self.g = g

	def update(self):
		pass

	def set_temperature(self, temperature):
		pass
	
	def __init__(self, temperature, material_1, material_2):
		self.temperature = temperature
		self.materialname_1 = material_1.materialname
		self.materialname_2 = material_2.materialname

