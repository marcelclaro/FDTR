# FDTR Library

Frequency Domain Thermoreflectance (FDTR) Python Library

## Overview

The FDTR library provides tools for modeling, simulating, and analyzing frequency domain thermoreflectance experiments. It includes:
- Core domain and material classes
- Fourier model implementations
- A modern Tkinter GUI for interactive analysis
- Multi-model and multi-dataset support
- Sensitivity analysis and parameter fitting

## Main Components

- `pyFDTR/`: Core library modules
  - `domain.py`: Domain and layer management
  - `materials.py`: Material property definitions
  - `fouriermodel.py`: FDTR model implementations
  - `util.py`: Utility functions
- `fdtr_gui.py`: Interactive GUI for FDTR analysis
- `sampledata/`: Example experimental data files
- `FDTR_GUI_README.md`: GUI usage instructions
- `readme.md`: (This file) Library overview and usage

## Features

- Create and manage FDTR domains with arbitrary layers and substrates
- Define and use custom materials
- Add layers and interfaces, including top layers
- Fit model parameters to experimental data
- Perform sensitivity analysis
- Visualize results and model structure
- Multi-model and multi-dataset workflows

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/marcelclaro/FDTR.git
   cd FDTR
2. Install dependencies:
   ```bash
   pip install numpy matplotlib lmfit
(Other dependencies: tkinter, mpmath)

## Usage
GUI:
See FDTR_GUI_README.md for details.

Library:
Import and use the core library in your own scripts:
    ```bash
    from pyFDTR.domain import Domain
    from pyFDTR.materials import sapphire, gold
    from pyFDTR.fouriermodel import FourierModelFDTR

    domain = Domain(300)
    domain.add_substrate(sapphire)
    domain.add_layer(60e-7, gold)
    model = FourierModelFDTR(domain, 4.05e-4, 4.05e-4, 0)
    phase = model.get_phase(1e6)

Sample Data
Example data files are provided in the sampledata folder for testing and demonstration.

Documentation
FDTR_GUI_README.md: GUI usage and features
Inline docstrings in source files

## Contributing
Pull requests and issues are welcome! Please document your changes and follow best practices.

## License
MIT License

## Author
Marcel Claro and contributors