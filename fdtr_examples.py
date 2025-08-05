#!/usr/bin/env python3
"""
Example script demonstrating how to use the FDTR library programmatically
This shows the same operations that can be performed through the GUI.
"""

import numpy as np
import matplotlib.pyplot as plt
from pyFDTR.domain import *
from pyFDTR.materials import *
from pyFDTR.fouriermodel import *
import lmfit

def example_basic_model():
    """Example: Basic FDTR model without parameter fitting"""
    print("=== Basic FDTR Model Example ===")
    
    # Create domain at 300K
    domain = Domain(300)
    print(f"Created domain at {domain.temperature}K")
    
    # Add sapphire substrate
    domain.add_substrate(sapphire)
    print("Added sapphire substrate")
    
    # Add 60nm gold layer
    domain.add_layer(60e-7, gold)
    print("Added 60nm gold layer")
    
    # Set interface thermal boundary conductance
    domain.set_interface_condu(1, 5e3)
    print("Set interface conductance to 5000 W/cm²K")
    
    # Create FDTR model
    model = FourierModelFDTR(domain, 4.05e-4, 4.05e-4, 0, backend='numpy')
    print("Created FDTR model")
    
    # Calculate phase response
    frequencies = np.logspace(3, 7, 50)  # 1 kHz to 10 MHz
    phases = []
    
    print("Calculating phase response...")
    for f in frequencies:
        phases.append(model.get_phase(f))
    
    # Plot results
    plt.figure(figsize=(10, 6))
    plt.semilogx(frequencies, phases, 'b-', linewidth=2, label='Au/Sapphire 300K')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Phase (rad)')
    plt.title('FDTR Phase Response')
    plt.grid(True)
    plt.legend()
    plt.show()
    
    print("Basic model calculation complete!")
    return domain, model, frequencies, phases

def example_parameter_fitting():
    """Example: Parameter fitting with experimental data"""
    print("\n=== Parameter Fitting Example ===")
    
    # Load experimental data (using one of the sample files)
    try:
        load = np.genfromtxt('./sampledata/sapphire-gold60nm_300K.txt', skip_header=2)
        exp_data = np.delete(load, 1, 1)  # Remove amplitude column
        print(f"Loaded experimental data: {len(exp_data)} points")
    except FileNotFoundError:
        print("Sample data file not found. Creating synthetic data for demonstration.")
        # Create synthetic data for demonstration
        freqs = np.logspace(3, 7, 20)
        phases = -0.5 * np.log10(freqs) + np.random.normal(0, 0.01, len(freqs))
        exp_data = np.column_stack((freqs, phases))
    
    # Create fitting parameters
    var_par = Fitting_parameters()
    var_par.add('kz', value=0.40, min=0.10, max=0.70)
    var_par.add('thick', value=60e-7, min=40e-7, max=80e-7)
    print("Added fitting parameters: kz and thickness")
    
    # Create domain and model for fitting
    domain = Domain(300)
    domain.add_substrate(sapphire)
    domain.add_layer(60e-7, gold)
    domain.set_interface_condu(1, 5e3)
    
    # Set layer parameters to use fitting parameters
    domain.set_layer_param(1, thickness=var_par.get_parameter('thick'),
                          kzz=var_par.get_parameter('kz'))
    
    # Create model with fitting parameters
    model = FourierModelFDTR(domain, 4.05e-4, 4.05e-4, 0, 
                           fitting_params=var_par, backend='numpy', jit=True)
    print("Created fitting model")
    
    # Perform fitting
    print("Starting parameter fitting...")
    out = model.minimize(exp_data, method='nelder')
    
    # Print results
    print("\nFitting Results:")
    print(lmfit.fit_report(out))
    
    # Calculate fitted curve
    fitted_phases = []
    for f in exp_data[:, 0]:
        fitted_phases.append(model.get_phase(f))
    
    # Plot comparison
    plt.figure(figsize=(10, 6))
    plt.semilogx(exp_data[:, 0], exp_data[:, 1], 'ro', markersize=6, label='Experimental')
    plt.semilogx(exp_data[:, 0], fitted_phases, 'b-', linewidth=2, label='Fitted')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Phase (rad)')
    plt.title('Parameter Fitting Results')
    plt.grid(True)
    plt.legend()
    plt.show()
    
    print("Parameter fitting complete!")
    return out

def example_sensitivity_analysis():
    """Example: Sensitivity analysis"""
    print("\n=== Sensitivity Analysis Example ===")
    
    # Create model with fitting parameters
    var_par = Fitting_parameters()
    var_par.add('kz', value=0.40, min=0.10, max=0.70)
    
    domain = Domain(300)
    domain.add_substrate(sapphire)
    domain.add_layer(60e-7, gold)
    domain.set_interface_condu(1, 5e3)
    domain.set_layer_param(1, kzz=var_par.get_parameter('kz'))
    
    model = FourierModelFDTR(domain, 4.05e-4, 4.05e-4, 0,
                           fitting_params=var_par, backend='numpy', jit=True)
    
    # Perform sensitivity analysis
    print("Calculating sensitivity to 'kz' parameter...")
    sensitivity = model.sensitivity_analysis('kz')
    freqs, sens_vals = sensitivity
    
    # Plot sensitivity
    plt.figure(figsize=(10, 6))
    plt.semilogx(freqs, sens_vals, 'r-', linewidth=2)
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Sensitivity')
    plt.title('Sensitivity Analysis for Thermal Conductivity (kz)')
    plt.grid(True)
    plt.show()
    
    print("Sensitivity analysis complete!")
    return freqs, sens_vals

def example_temperature_comparison():
    """Example: Compare models at different temperatures"""
    print("\n=== Temperature Comparison Example ===")
    
    temperatures = [80, 300]
    colors = ['blue', 'red']
    labels = ['80K', '300K']
    
    plt.figure(figsize=(10, 6))
    
    for temp, color, label in zip(temperatures, colors, labels):
        # Create domain at specific temperature
        domain = Domain(temp)
        domain.add_substrate(sapphire)
        domain.add_layer(60e-7, gold)
        
        # Different interface conductances for different temperatures
        if temp == 80:
            domain.set_interface_condu(1, 2e3)
        else:
            domain.set_interface_condu(1, 5e3)
        
        # Create model
        model = FourierModelFDTR(domain, 4.05e-4, 4.05e-4, 0, backend='numpy')
        
        # Calculate phase
        frequencies = np.logspace(3, 7, 50)
        phases = []
        for f in frequencies:
            phases.append(model.get_phase(f))
        
        # Plot
        plt.semilogx(frequencies, phases, color=color, linewidth=2, 
                    label=f'Au/Sapphire {label}')
        print(f"Calculated model for {temp}K")
    
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Phase (rad)')
    plt.title('FDTR Temperature Comparison')
    plt.grid(True)
    plt.legend()
    plt.show()
    
    print("Temperature comparison complete!")

def main():
    """Run all examples"""
    print("FDTR Library Examples")
    print("====================")
    
    try:
        # Run examples
        example_basic_model()
        example_parameter_fitting()
        example_sensitivity_analysis() 
        example_temperature_comparison()
        
        print("\n=== All Examples Complete! ===")
        print("You can now run the GUI with: python3 fdtr_gui.py")
        
    except Exception as e:
        print(f"Error running examples: {e}")
        print("Make sure all required packages are installed and the pyFDTR library is available.")

if __name__ == "__main__":
    main()
