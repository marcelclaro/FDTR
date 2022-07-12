from .util import Constants

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
	density = 3.97e6  #  Density g/m3
	mass_mol = 102.0  #  Molar mass in g/mol
	Tdebye = 1047     #  Debye temperature in K

	def set_temperature(self, temperature):
		self.temperature = temperature
		self.cp = polynomial(temperature,-1.6373e+06 , 24234.3 , -33.2459 , 0.0160457)
		self.kt = power(temperature,10.8225,4.94027e+07,-2.56139)   #   W/mK
		self.kp = self.kt   #   W/mK

	def __init__(self, temperature):
		self.temperature = temperature
		self.cp = polynomial(temperature,-1.6373e+06 , 24234.3 , -33.2459 , 0.0160457)
		self.kt = power(temperature,10.8225,4.94027e+07,-2.56139)   #   W/mK
		self.kp = self.kt   #   W/mK

class gold(material):
	materialname = 'Au'
	density = 19.3e6    #  Density g/m3
	mass_mol = 196.96   #  Molar mass in g/mol
	Tdebye = 180       #  Debye temperature in K

	def set_temperature(self, temperature):
		self.temperature = temperature
		self.cp = polynomial(temperature,1.21201e+06 , 13615.4, -60.5398, 0.136611, -0.000146641, 5.99102e-08)
		self.kt = polynomial(temperature,69.1593,-0.009147,-4.37555e-06)   #   W/mK
		self.kp = self.kt   #   W/mK

	def __init__(self, temperature):
		self.temperature = temperature
		self.cp = polynomial(temperature,1.21201e+06 , 13615.4, -60.5398, 0.136611, -0.000146641, 5.99102e-08)
		self.kt = polynomial(temperature,69.1593,-0.009147,-4.37555e-06)   #   W/mK
		self.kp = self.kt   #   W/mK

class default_material(material):
	materialname = 'default'
	density = 1e6    #  Density g/m3
	mass_mol = 100   #  Molar mass in g/mol
	Tdebye = 1000       #  Debye temperature in K

	def __init__(self, temperature):
		self.temperature = temperature
		self.cp = 1e6
		self.kt = 50   #   W/mK
		self.kp = 50   #   W/mK