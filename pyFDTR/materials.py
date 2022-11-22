from .util import Constants

'''
Important!!!!!

Use cm instead of meter to prevent overflow

'''


class material:
	pass

def polynomial(x,*coef):
	sum = 0.0
	for index,c in enumerate(coef):
		sum += c * (x ** index)
	return sum

def power(x,a,b,c):
	return a + b * (x ** c) 

class sapphire(material):
	materialname = 'Sapphire'
	density = 3.97  #  Density g/cm
	mass_mol = 102.0  #  Molar mass in g/mol
	Tdebye = 1047     #  Debye temperature in K

	def set_temperature(self, temperature):
		self.temperature = temperature
		self.cp = 1.0e-6*polynomial(temperature,-1.6373e+06 , 24234.3 , -33.2459 , 0.0160457)
		self.kxx = 1.0e-2*power(temperature,10.8225,4.94027e+07,-2.56139)   #   W/cmK
		self.kyy = self.kxx    #   W/cmK
		self.kxy = 0  #   W/cmK
		self.kzz = self.kxx   #   W/cmK

	def __init__(self, temperature):
		self.temperature = temperature
		self.cp = 1.0e-6*polynomial(temperature,-1.6373e+06 , 24234.3 , -33.2459 , 0.0160457)
		self.kxx = 1.0e-2*power(temperature,10.8225,4.94027e+07,-2.56139)   #   W/cmK
		self.kyy = self.kxx    #   W/cmK
		self.kxy = 0  #   W/cmK
		self.kzz = self.kxx   #   W/cmK

class alumina(material):
	materialname = 'Alumina'
	density = 3.15  #  Density g/cm3
	mass_mol = 102.0  #  Molar mass in g/mol
	Tdebye = 1047     #  Debye temperature in K

	def set_temperature(self, temperature):
		self.temperature = temperature
		self.cp = 1.0e-6*2.15 
		self.kxx = 1.0e-2 * 1   #   W/cmK
		self.kyy = 1.0e-2 * 1   #   W/cmK
		self.kxy = 0  #   W/cmK
		self.kzz = 1.0e-2 * 1   #   W/cmK

	def __init__(self, temperature):
		self.temperature = temperature
		self.cp = 1.0e-6*2.15 
		self.kxx = 1.0e-2 * 1   #   W/cmK
		self.kyy = 1.0e-2 * 1   #   W/cmK
		self.kxy = 0  #   W/cmK
		self.kzz = 1.0e-2 * 1   #   W/cmK

class in2se3(material):
	materialname = 'In2Se3'
	density = 5.67  #  Density g/m3
	mass_mol = 466  #  Molar mass in g/mol
	Tdebye = 1047     #  Debye temperature in K

	def set_temperature(self, temperature):
		self.temperature = temperature
		self.cp = 1.0e-6*2.55
		self.kxx = 1.0e-2 * 10   #   W/cmK
		self.kyy = 1.0e-2 * 10   #   W/cmK
		self.kxy = 0
		self.kzz = 1.0e-2 * 0.200   #   W/cmK

	def __init__(self, temperature):
		self.temperature = temperature
		self.cp = 1.0e-6*2.55
		self.kxx = 1.0e-2 * 10   #   W/cmK
		self.kyy = 1.0e-2 * 10   #   W/cmK
		self.kxy = 0
		self.kzz = 1.0e-2 * 0.200   #   W/cmK

class gold(material):
	materialname = 'Au'
	density = 19.3    #  Density g/cm3
	mass_mol = 196.96   #  Molar mass in g/mol
	Tdebye = 180       #  Debye temperature in K

	def set_temperature(self, temperature):
		self.temperature = temperature
		self.cp = 1.0e-6 *polynomial(temperature,1.21201e+06 , 13615.4, -60.5398, 0.136611, -0.000146641, 5.99102e-08)
		self.kxx = 1.0e-2 * polynomial(temperature,69.1593,-0.009147,-4.37555e-06)   #   W/mK
		self.kyy = self.kxx   #   W/mK
		self.kxy = 0   #   W/mK
		self.kzz = 1.0e-2 * polynomial(temperature,69.1593,-0.009147,-4.37555e-06)   #   W/mK

	def __init__(self, temperature):
		self.temperature = temperature
		self.cp = 1.0e-6 * polynomial(temperature,1.21201e+06 , 13615.4, -60.5398, 0.136611, -0.000146641, 5.99102e-08)
		self.kxx = 1.0e-2 * polynomial(temperature,69.1593,-0.009147,-4.37555e-06)   #   W/mK
		self.kyy = self.kxx   #   W/mK
		self.kxy = 0   #   W/mK
		self.kzz = 1.0e-2 * polynomial(temperature,69.1593,-0.009147,-4.37555e-06)   #   W/mK


class STO(material):
	materialname = 'STO'
	density = 5.11   #  Density g/cm3
	mass_mol = 183.49   #  Molar mass in g/mol
	Tdebye = 180      ### WRONG!!! #  Debye temperature in K

	def set_temperature(self, temperature):
		self.temperature = temperature
		self.cp = 2.72
		self.kxx = 1.0e-2 * 9.8   #   W/mK
		self.kyy = self.kxx   #   W/mK
		self.kxy = 0   #   W/mK
		self.kzz = 1.0e-2 * 9.8   #   W/mK

	def __init__(self, temperature):
		self.temperature = temperature
		self.cp = 2.72
		self.kxx = 1.0e-2 * 9.8   #   W/mK
		self.kyy = self.kxx   #   W/mK
		self.kxy = 0   #   W/mK
		self.kzz = 1.0e-2 * 9.8   #   W/mK


class default_material(material):
	materialname = 'default'
	density = 1    #  Density g/m3
	mass_mol = 100   #  Molar mass in g/mol
	Tdebye = 1000       #  Debye temperature in K

	def __init__(self, temperature):
		self.temperature = temperature
		self.cp = 1.0
		self.kxx = 0.5   #   W/cmK
		self.kyy = 0.5   #   W/cmK
		self.kxy = 0     #   W/cmK
		self.kzz = 0.5   #   W/mK