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
# FDTR GUI

This GUI provides an interactive interface for Frequency Domain Thermoreflectance (FDTR) analysis using the pyFDTR library.

## Features

- Create domains with different temperatures (autocomplete values)
- Add layers and substrates with various materials
- Set interface thermal boundary conductances
- Fit parameters to experimental data
- Plot results and sensitivity analysis
- Multi-model and multi-dataset management

## Usage

### 1. Domain & Model Setup Tab
- Set temperature, substrate, and layer properties
- Add substrate and layers to the domain
- Set interface conductance and material properties
- Use the editable combobox to enter a model name
- Click "Create Model" to create a new model

### 2. Multi-Model Fitting Tab
- Manage multiple models and datasets
- Pair models with datasets for fitting
- Start fitting using different methods

### 3. Model Analysis Tab
- Select a model and parameters for sensitivity analysis
- Plot phase vs frequency and sensitivity curves

## Notes

- The GUI supports multiple models and datasets

## Requirements

- Python 3.x
- pyFDTR library
- tkinter, matplotlib, numpy

## Running

```bash
python3 fdtr_gui.py
```

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
   - Add Sapphire substrate
   - Add Gold layer (60e-7 cm thick)
   - Set interface 1 conductance to 5e3 W/cm²K

2. **Model Setup Tab:**
   - Set pump/probe radii to 4.05e-4 cm
   - Set beam offset to 0
   - Choose numpy backend
   - Create model


3. **Parameter Fitting Tab:**
   - Load experimental data file
   - (Optional) Edit fitting parameter 'kz' with value 0.40, min 0.10, max 0.70
   - Start fitting with 'nelder' method

4. **Results Tab:**
   - Plot model curve
   - Perform sensitivity analysis on 'kz' parameter


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
- The mpmath backend is slower but could be more numerically stable for complex models
- Always create the domain before adding layers or creating models
- Interface numbers start from 1 and count from bottom to top

## Troubleshooting

**"Please create a domain first"**: Make sure to create a domain in the Domain Setup tab before proceeding to other operations.

**Import errors**: Ensure all required packages are installed and the pyFDTR library is in your Python path.

**Numerical issues**: Try using the mpmath backend for better numerical precision, especially for complex multilayer structures.

**Fitting doesn't converge**: Try different initial parameter values or bounds, or use a different fitting method.
