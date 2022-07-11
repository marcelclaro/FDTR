from sympy import init_printing
from pyFDTR.domain import *

init_printing() 

testlayer = Layer(20e-9, 300, 'testmaterial')
print(testlayer.getFourier_Matrix())