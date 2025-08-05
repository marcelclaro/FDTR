# FDTR GUI - Interactive Interface

This GUI provides an interactive interface for the pyFDTR (Frequency Domain Thermoreflectance) library, allowing users to:

- Create thermal domains with different temperatures
- Add substrates and layers with various materials
- Set interface thermal boundary conductances
- Create FDTR models with customizable beam parameters
- Fit parameters to experimental data
- Perform sensitivity analysis
- Plot and save results

## Installation and Requirements

Before running the GUI, ensure you have the following Python packages installed:

```bash
pip install numpy matplotlib scipy sympy mpmath lmfit numba tkinter
```

Note: `tkinter` usually comes pre-installed with Python.

## Running the GUI

To start the GUI, run:

```bash
python3 fdtr_gui.py
```

## Usage Guide

### 1. Domain Setup Tab

**Create Domain:**
1. Enter the temperature in Kelvin (default: 300K)
2. Click "Create Domain"

**Add Substrate:**
1. Select a material from the dropdown (default: Sapphire)
2. Click "Add Substrate"

**Add Layers:**
1. Enter layer thickness in cm (e.g., 60e-7 for 60 nm)
2. Select layer material from dropdown
3. Click "Add Layer"

**Set Interface Conductance:**
1. Enter interface number (starting from 1)
2. Enter thermal boundary conductance in W/cm²K
3. Click "Set Interface"

The current structure will be displayed in the text area below.

### 2. Model Setup Tab

**Configure Beam Parameters:**
1. Set pump radius (cm)
2. Set probe radius (cm) 
3. Set beam offset (cm, 0 for no offset)
4. Choose backend (numpy for speed, mpmath for precision)
5. Click "Create Model"

**Set Frequency Range:**
1. Enter start frequency (Hz)
2. Enter end frequency (Hz)
3. Enter step size (Hz)
4. Click "Calculate Phase" to compute the model response

### 3. Parameter Fitting Tab

**Load Experimental Data:**
1. Click "Load Data File"
2. Select a text file with frequency and phase data
3. The file should have headers on the first 2 lines

**Add Fitting Parameters:**
1. Enter parameter name (e.g., 'kz', 'thick')
2. Enter initial value
3. Enter minimum and maximum bounds (optional)
4. Click "Add Parameter"

**Start Fitting:**
1. Select fitting method (nelder, differential_evolution, leastsq)
2. Click "Start Fitting"
3. Results will appear in the text area below

### 4. Results Tab

**Plotting:**
- "Plot Results": Shows experimental data vs calculated/fitted results
- "Sensitivity Analysis": Analyzes parameter sensitivity (enter parameter name when prompted)
- "Save Results": Export calculated data to text file
- "Clear Plot": Clear the current plot

## Available Materials

The GUI includes the following predefined materials:
- Sapphire
- Alumina  
- Gold
- STO (Strontium Titanate)
- Air
- Water
- IPA (Isopropyl Alcohol)
- Glass
- In2Se3 (Indium Selenide)
- Default (generic material)

## Example Workflow

1. **Domain Setup Tab:**
   - Create domain at 300K
   - Add Sapphire substrate
   - Add Gold layer (60e-7 cm thick)
   - Set interface 1 conductance to 5e3 W/cm²K

2. **Model Setup Tab:**
   - Set pump/probe radii to 4.05e-4 cm
   - Set beam offset to 0
   - Choose numpy backend
   - Create model
   - Set frequency range 1e3 to 40e6 Hz with 10e3 step
   - Calculate phase

3. **Parameter Fitting Tab:**
   - Load experimental data file
   - Add fitting parameter 'kz' with value 0.40, min 0.10, max 0.70
   - Start fitting with 'nelder' method

4. **Results Tab:**
   - Plot results to compare experimental vs fitted data
   - Perform sensitivity analysis on 'kz' parameter
   - Save results to file

## File Format for Experimental Data

Experimental data files should be text files with:
- First 2 lines: headers (will be skipped)
- Column 1: Frequency (Hz)
- Column 2: Amplitude (ignored)
- Column 3: Phase (radians)

Example:
```
# Frequency  Amplitude  Phase
# Hz         V          rad
1000        0.1        -0.5
5000        0.2        -0.8
...
```

## Tips

- Use scientific notation for small values (e.g., 60e-7 instead of 0.0000006)
- For numerical stability, the library uses cm units for thermal conductivity (W/cmK)
- The mpmath backend is slower but more numerically stable for complex models
- Always create the domain before adding layers or creating models
- Interface numbers start from 1 and count from bottom to top

## Troubleshooting

**"Please create a domain first"**: Make sure to create a domain in the Domain Setup tab before proceeding to other operations.

**Import errors**: Ensure all required packages are installed and the pyFDTR library is in your Python path.

**Numerical issues**: Try using the mpmath backend for better numerical precision, especially for complex multilayer structures.

**Fitting doesn't converge**: Try different initial parameter values or bounds, or use a different fitting method.
