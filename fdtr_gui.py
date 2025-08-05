#!/usr/bin/env python3
"""
FDTR GUI - Interactive Interface for Frequency Domain Thermoreflectance Analysis

This GUI provides an interactive interface for:
- Creating domains with different temperatures
- Adding layers and substrates with various materials
- Setting interface thermal boundary conductances
- Fitting parameters to experimental data
- Plotting results and sensitivity analysis

Author: Auto-generated GUI for pyFDTR library
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import json
import os

# Import the FDTR library
try:
    from pyFDTR.domain import *
    from pyFDTR.materials import *
    from pyFDTR.fouriermodel import *
    import lmfit
except ImportError as e:
    print(f"Error importing pyFDTR: {e}")
    print("Please ensure pyFDTR is properly installed and in your Python path")


class FDTRGui:
    def __init__(self, root):
        self.root = root
        self.root.title("FDTR Interactive Interface")
        self.root.geometry("1200x800")
        
        # Initialize variables
        self.domain = None
        self.model = None
        self.fitting_params = None
        self.experimental_data = None
        self.frequencies = None
        
        # Multi-model support
        self.models = {}  # Dictionary to store multiple models {name: model}
        self.datasets = {}  # Dictionary to store multiple datasets {name: data}
        self.model_counter = 1
        self.dataset_counter = 1
        
        # Available materials dictionary
        self.materials = {
            'Sapphire': sapphire,
            'Alumina': alumina,
            'Gold': gold,
            'STO': STO,
            'Air': Air,
            'Water': Water,
            'IPA': IPA,
            'Glass': glass,
            'In2Se3': in2se3,
            'Default': default_material
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.setup_domain_model_tab()
        self.setup_fitting_tab()
        
    def setup_domain_model_tab(self):
        """Setup the combined domain and model configuration tab"""
        self.domain_model_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.domain_model_frame, text="Domain & Model Setup")
        
        # Setup the unified interface in this tab
        self.setup_unified_interface()
        
    def setup_unified_interface(self):
        """Setup the unified interface without tabs"""
        
        # Use the domain_model_frame as the main frame
        self.main_frame = self.domain_model_frame
        
        # Domain Setup Section
        domain_frame = ttk.LabelFrame(self.main_frame, text="Domain Setup", padding=10)
        domain_frame.pack(fill='x', padx=5, pady=5)
        
        # Temperature
        temp_frame = ttk.Frame(domain_frame)
        temp_frame.pack(fill='x', pady=2)
        
        ttk.Label(temp_frame, text="Temperature (K):").pack(side='left')
        self.temp_var = tk.StringVar(value="300")
        ttk.Entry(temp_frame, textvariable=self.temp_var, width=10).pack(side='left', padx=(5,10))
        ttk.Button(temp_frame, text="Create Domain", command=self.create_domain).pack(side='left')
        
        # Substrate
        substrate_frame = ttk.Frame(domain_frame)
        substrate_frame.pack(fill='x', pady=2)
        
        ttk.Label(substrate_frame, text="Substrate Material:").pack(side='left')
        self.substrate_var = tk.StringVar(value="Sapphire")
        substrate_combo = ttk.Combobox(substrate_frame, textvariable=self.substrate_var, 
                    values=list(self.materials.keys()), width=15)
        substrate_combo.pack(side='left', padx=(5,10))
        substrate_combo.bind('<<ComboboxSelected>>', self.on_substrate_material_change)
        ttk.Button(substrate_frame, text="Add Substrate", command=self.add_substrate).pack(side='left')
        
        # Layer Management Section
        layer_frame = ttk.LabelFrame(self.main_frame, text="Layer Management", padding=10)
        layer_frame.pack(fill='x', padx=5, pady=5)
        
        # Layer input with parameter type selection
        layer_input_frame = ttk.Frame(layer_frame)
        layer_input_frame.pack(fill='x', pady=5)
        
        # Thickness
        ttk.Label(layer_input_frame, text="Thickness (cm):").grid(row=0, column=0, sticky='w')
        self.thickness_var = tk.StringVar(value="60e-7")
        ttk.Entry(layer_input_frame, textvariable=self.thickness_var, width=15).grid(row=0, column=1, padx=2)
        self.thickness_is_fitting = tk.BooleanVar()
        ttk.Checkbutton(layer_input_frame, text="Fit", variable=self.thickness_is_fitting).grid(row=0, column=2, padx=2)
        
        # Thickness fitting bounds
        ttk.Label(layer_input_frame, text="Min:").grid(row=0, column=3, sticky='w', padx=(10,2))
        self.thickness_min_var = tk.StringVar()
        thickness_min_entry = ttk.Entry(layer_input_frame, textvariable=self.thickness_min_var, width=10)
        thickness_min_entry.grid(row=0, column=4, padx=2)
        
        ttk.Label(layer_input_frame, text="Max:").grid(row=0, column=5, sticky='w', padx=(5,2))
        self.thickness_max_var = tk.StringVar()
        thickness_max_entry = ttk.Entry(layer_input_frame, textvariable=self.thickness_max_var, width=10)
        thickness_max_entry.grid(row=0, column=6, padx=2)
        
        # Material
        ttk.Label(layer_input_frame, text="Material:").grid(row=1, column=0, sticky='w')
        self.layer_material_var = tk.StringVar(value="Gold")
        layer_material_combo = ttk.Combobox(layer_input_frame, textvariable=self.layer_material_var, 
                    values=list(self.materials.keys()), width=15)
        layer_material_combo.grid(row=1, column=1, padx=2)
        layer_material_combo.bind('<<ComboboxSelected>>', self.on_layer_material_change)
        
        # Interface Conductance
        ttk.Label(layer_input_frame, text="Interface Cond. (W/cm²K):").grid(row=2, column=0, sticky='w')
        self.interface_cond_var = tk.StringVar(value="5e3")
        ttk.Entry(layer_input_frame, textvariable=self.interface_cond_var, width=15).grid(row=2, column=1, padx=2)
        self.interface_is_fitting = tk.BooleanVar()
        ttk.Checkbutton(layer_input_frame, text="Fit", variable=self.interface_is_fitting).grid(row=2, column=2, padx=2)
        
        # Interface fitting bounds
        ttk.Label(layer_input_frame, text="Min:").grid(row=2, column=3, sticky='w', padx=(10,2))
        self.interface_min_var = tk.StringVar()
        ttk.Entry(layer_input_frame, textvariable=self.interface_min_var, width=10).grid(row=2, column=4, padx=2)
        
        ttk.Label(layer_input_frame, text="Max:").grid(row=2, column=5, sticky='w', padx=(5,2))
        self.interface_max_var = tk.StringVar()
        ttk.Entry(layer_input_frame, textvariable=self.interface_max_var, width=10).grid(row=2, column=6, padx=2)
        
        # Add Layer button
        ttk.Button(layer_input_frame, text="Add Layer", command=self.add_layer).grid(row=3, column=0, columnspan=2, pady=10, sticky='w')
        
        # Substrate Properties Section
        substrate_props_frame = ttk.LabelFrame(self.main_frame, text="Substrate Properties (for fitting)", padding=10)
        substrate_props_frame.pack(fill='x', padx=5, pady=5)
        
        sub_props_frame = ttk.Frame(substrate_props_frame)
        sub_props_frame.pack(fill='x', pady=5)
        
        # Substrate thermal conductivity kz
        ttk.Label(sub_props_frame, text="Substrate kz (W/cmK):").grid(row=0, column=0, sticky='w')
        self.sub_kz_var = tk.StringVar()
        ttk.Entry(sub_props_frame, textvariable=self.sub_kz_var, width=15).grid(row=0, column=1, padx=2)
        self.sub_kz_is_fitting = tk.BooleanVar()
        ttk.Checkbutton(sub_props_frame, text="Fit", variable=self.sub_kz_is_fitting).grid(row=0, column=2, padx=2)
        
        ttk.Label(sub_props_frame, text="Min:").grid(row=0, column=3, sticky='w', padx=(10,2))
        self.sub_kz_min_var = tk.StringVar()
        ttk.Entry(sub_props_frame, textvariable=self.sub_kz_min_var, width=10).grid(row=0, column=4, padx=2)
        
        ttk.Label(sub_props_frame, text="Max:").grid(row=0, column=5, sticky='w', padx=(5,2))
        self.sub_kz_max_var = tk.StringVar()
        ttk.Entry(sub_props_frame, textvariable=self.sub_kz_max_var, width=10).grid(row=0, column=6, padx=2)
        
        # Substrate thermal conductivity kxx
        ttk.Label(sub_props_frame, text="Substrate kxx (W/cmK):").grid(row=1, column=0, sticky='w')
        self.sub_kxx_var = tk.StringVar()
        ttk.Entry(sub_props_frame, textvariable=self.sub_kxx_var, width=15).grid(row=1, column=1, padx=2)
        self.sub_kxx_is_fitting = tk.BooleanVar()
        ttk.Checkbutton(sub_props_frame, text="Fit", variable=self.sub_kxx_is_fitting).grid(row=1, column=2, padx=2)
        
        ttk.Label(sub_props_frame, text="Min:").grid(row=1, column=3, sticky='w', padx=(10,2))
        self.sub_kxx_min_var = tk.StringVar()
        ttk.Entry(sub_props_frame, textvariable=self.sub_kxx_min_var, width=10).grid(row=1, column=4, padx=2)
        
        ttk.Label(sub_props_frame, text="Max:").grid(row=1, column=5, sticky='w', padx=(5,2))
        self.sub_kxx_max_var = tk.StringVar()
        ttk.Entry(sub_props_frame, textvariable=self.sub_kxx_max_var, width=10).grid(row=1, column=6, padx=2)
        
        # Substrate heat capacity
        ttk.Label(sub_props_frame, text="Substrate Cp (J/cm³K):").grid(row=2, column=0, sticky='w')
        self.sub_cp_var = tk.StringVar()
        ttk.Entry(sub_props_frame, textvariable=self.sub_cp_var, width=15).grid(row=2, column=1, padx=2)
        self.sub_cp_is_fitting = tk.BooleanVar()
        ttk.Checkbutton(sub_props_frame, text="Fit", variable=self.sub_cp_is_fitting).grid(row=2, column=2, padx=2)
        
        ttk.Label(sub_props_frame, text="Min:").grid(row=2, column=3, sticky='w', padx=(10,2))
        self.sub_cp_min_var = tk.StringVar()
        ttk.Entry(sub_props_frame, textvariable=self.sub_cp_min_var, width=10).grid(row=2, column=4, padx=2)
        
        ttk.Label(sub_props_frame, text="Max:").grid(row=2, column=5, sticky='w', padx=(5,2))
        self.sub_cp_max_var = tk.StringVar()
        ttk.Entry(sub_props_frame, textvariable=self.sub_cp_max_var, width=10).grid(row=2, column=6, padx=2)
        
        # Layer Properties Section
        layer_props_frame = ttk.LabelFrame(self.main_frame, text="Layer Properties (for fitting)", padding=10)
        layer_props_frame.pack(fill='x', padx=5, pady=5)
        
        layer_props_inner_frame = ttk.Frame(layer_props_frame)
        layer_props_inner_frame.pack(fill='x', pady=5)
        
        # Layer thermal conductivity kz
        ttk.Label(layer_props_inner_frame, text="Layer kz (W/cmK):").grid(row=0, column=0, sticky='w')
        self.layer_kz_var = tk.StringVar()
        ttk.Entry(layer_props_inner_frame, textvariable=self.layer_kz_var, width=15).grid(row=0, column=1, padx=2)
        self.layer_kz_is_fitting = tk.BooleanVar()
        ttk.Checkbutton(layer_props_inner_frame, text="Fit", variable=self.layer_kz_is_fitting).grid(row=0, column=2, padx=2)
        
        ttk.Label(layer_props_inner_frame, text="Min:").grid(row=0, column=3, sticky='w', padx=(10,2))
        self.layer_kz_min_var = tk.StringVar()
        ttk.Entry(layer_props_inner_frame, textvariable=self.layer_kz_min_var, width=10).grid(row=0, column=4, padx=2)
        
        ttk.Label(layer_props_inner_frame, text="Max:").grid(row=0, column=5, sticky='w', padx=(5,2))
        self.layer_kz_max_var = tk.StringVar()
        ttk.Entry(layer_props_inner_frame, textvariable=self.layer_kz_max_var, width=10).grid(row=0, column=6, padx=2)
        
        # Layer thermal conductivity kxx
        ttk.Label(layer_props_inner_frame, text="Layer kxx (W/cmK):").grid(row=1, column=0, sticky='w')
        self.layer_kxx_var = tk.StringVar()
        ttk.Entry(layer_props_inner_frame, textvariable=self.layer_kxx_var, width=15).grid(row=1, column=1, padx=2)
        self.layer_kxx_is_fitting = tk.BooleanVar()
        ttk.Checkbutton(layer_props_inner_frame, text="Fit", variable=self.layer_kxx_is_fitting).grid(row=1, column=2, padx=2)
        
        ttk.Label(layer_props_inner_frame, text="Min:").grid(row=1, column=3, sticky='w', padx=(10,2))
        self.layer_kxx_min_var = tk.StringVar()
        ttk.Entry(layer_props_inner_frame, textvariable=self.layer_kxx_min_var, width=10).grid(row=1, column=4, padx=2)
        
        ttk.Label(layer_props_inner_frame, text="Max:").grid(row=1, column=5, sticky='w', padx=(5,2))
        self.layer_kxx_max_var = tk.StringVar()
        ttk.Entry(layer_props_inner_frame, textvariable=self.layer_kxx_max_var, width=10).grid(row=1, column=6, padx=2)
        
        # Layer heat capacity
        ttk.Label(layer_props_inner_frame, text="Layer Cp (J/cm³K):").grid(row=2, column=0, sticky='w')
        self.layer_cp_var = tk.StringVar()
        ttk.Entry(layer_props_inner_frame, textvariable=self.layer_cp_var, width=15).grid(row=2, column=1, padx=2)
        self.layer_cp_is_fitting = tk.BooleanVar()
        ttk.Checkbutton(layer_props_inner_frame, text="Fit", variable=self.layer_cp_is_fitting).grid(row=2, column=2, padx=2)
        
        ttk.Label(layer_props_inner_frame, text="Min:").grid(row=2, column=3, sticky='w', padx=(10,2))
        self.layer_cp_min_var = tk.StringVar()
        ttk.Entry(layer_props_inner_frame, textvariable=self.layer_cp_min_var, width=10).grid(row=2, column=4, padx=2)
        
        ttk.Label(layer_props_inner_frame, text="Max:").grid(row=2, column=5, sticky='w', padx=(5,2))
        self.layer_cp_max_var = tk.StringVar()
        ttk.Entry(layer_props_inner_frame, textvariable=self.layer_cp_max_var, width=10).grid(row=2, column=6, padx=2)
        
        # Model Parameters Section
        model_frame = ttk.LabelFrame(self.main_frame, text="Model Parameters", padding=10)
        model_frame.pack(fill='x', padx=5, pady=5)
        
        # Beam parameters
        beam_frame = ttk.Frame(model_frame)
        beam_frame.pack(fill='x', pady=5)
        
        ttk.Label(beam_frame, text="Pump radius (cm):").grid(row=0, column=0, sticky='w')
        self.pump_radius_var = tk.StringVar(value="4.05e-4")
        ttk.Entry(beam_frame, textvariable=self.pump_radius_var, width=15).grid(row=0, column=1, padx=2)
        self.pump_radius_is_fitting = tk.BooleanVar()
        ttk.Checkbutton(beam_frame, text="Fit", variable=self.pump_radius_is_fitting).grid(row=0, column=2, padx=2)
        
        ttk.Label(beam_frame, text="Min:").grid(row=0, column=3, sticky='w', padx=(10,2))
        self.pump_radius_min_var = tk.StringVar()
        ttk.Entry(beam_frame, textvariable=self.pump_radius_min_var, width=10).grid(row=0, column=4, padx=2)
        
        ttk.Label(beam_frame, text="Max:").grid(row=0, column=5, sticky='w', padx=(5,2))
        self.pump_radius_max_var = tk.StringVar()
        ttk.Entry(beam_frame, textvariable=self.pump_radius_max_var, width=10).grid(row=0, column=6, padx=2)
        
        ttk.Label(beam_frame, text="Probe radius (cm):").grid(row=1, column=0, sticky='w')
        self.probe_radius_var = tk.StringVar(value="4.05e-4")
        ttk.Entry(beam_frame, textvariable=self.probe_radius_var, width=15).grid(row=1, column=1, padx=2)
        self.probe_radius_is_fitting = tk.BooleanVar()
        ttk.Checkbutton(beam_frame, text="Fit", variable=self.probe_radius_is_fitting).grid(row=1, column=2, padx=2)
        
        ttk.Label(beam_frame, text="Min:").grid(row=1, column=3, sticky='w', padx=(10,2))
        self.probe_radius_min_var = tk.StringVar()
        ttk.Entry(beam_frame, textvariable=self.probe_radius_min_var, width=10).grid(row=1, column=4, padx=2)
        
        ttk.Label(beam_frame, text="Max:").grid(row=1, column=5, sticky='w', padx=(5,2))
        self.probe_radius_max_var = tk.StringVar()
        ttk.Entry(beam_frame, textvariable=self.probe_radius_max_var, width=10).grid(row=1, column=6, padx=2)
        
        ttk.Label(beam_frame, text="Beam offset (cm):").grid(row=2, column=0, sticky='w')
        self.beam_offset_var = tk.StringVar(value="0")
        ttk.Entry(beam_frame, textvariable=self.beam_offset_var, width=15).grid(row=2, column=1, padx=2)
        self.beam_offset_is_fitting = tk.BooleanVar()
        ttk.Checkbutton(beam_frame, text="Fit", variable=self.beam_offset_is_fitting).grid(row=2, column=2, padx=2)
        
        ttk.Label(beam_frame, text="Min:").grid(row=2, column=3, sticky='w', padx=(10,2))
        self.beam_offset_min_var = tk.StringVar()
        ttk.Entry(beam_frame, textvariable=self.beam_offset_min_var, width=10).grid(row=2, column=4, padx=2)
        
        ttk.Label(beam_frame, text="Max:").grid(row=2, column=5, sticky='w', padx=(5,2))
        self.beam_offset_max_var = tk.StringVar()
        ttk.Entry(beam_frame, textvariable=self.beam_offset_max_var, width=10).grid(row=2, column=6, padx=2)
        
        ttk.Label(beam_frame, text="Backend:").grid(row=3, column=0, sticky='w')
        self.backend_var = tk.StringVar(value="numpy")
        ttk.Combobox(beam_frame, textvariable=self.backend_var, 
                    values=["numpy", "mpmath"], width=15).grid(row=3, column=1, padx=2)
        
        # Frequency range
        freq_frame = ttk.Frame(model_frame)
        freq_frame.pack(fill='x', pady=5)
        
        ttk.Label(freq_frame, text="Freq Start (Hz):").grid(row=0, column=0, sticky='w')
        self.freq_start_var = tk.StringVar(value="1e3")
        ttk.Entry(freq_frame, textvariable=self.freq_start_var, width=15).grid(row=0, column=1, padx=5)
        
        ttk.Label(freq_frame, text="Freq End (Hz):").grid(row=0, column=2, sticky='w', padx=(10,0))
        self.freq_end_var = tk.StringVar(value="40e6")
        ttk.Entry(freq_frame, textvariable=self.freq_end_var, width=15).grid(row=0, column=3, padx=5)
        
        ttk.Label(freq_frame, text="Freq Step (Hz):").grid(row=1, column=0, sticky='w')
        self.freq_step_var = tk.StringVar(value="10e3")
        ttk.Entry(freq_frame, textvariable=self.freq_step_var, width=15).grid(row=1, column=1, padx=5)
        
        # Analysis controls (without fitting controls)
        analysis_frame = ttk.Frame(model_frame)
        analysis_frame.pack(fill='x', pady=5)
        
        ttk.Button(analysis_frame, text="Create Model", command=self.create_model).pack(side='left', padx=5)
        ttk.Button(analysis_frame, text="Calculate Phase", command=self.calculate_phase).pack(side='left', padx=5)
        
        # Model status
        self.model_status_var = tk.StringVar(value="No model created")
        ttk.Label(model_frame, textvariable=self.model_status_var).pack(pady=5)
        
        # Current Structure Display
        structure_frame = ttk.LabelFrame(self.main_frame, text="Current Structure", padding=10)
        structure_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.structure_text = tk.Text(structure_frame, height=8, width=50)
        scrollbar = ttk.Scrollbar(structure_frame, orient="vertical", command=self.structure_text.yview)
        self.structure_text.configure(yscrollcommand=scrollbar.set)
        
        self.structure_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Initialize material properties with default values
        self.load_material_defaults()
        
    def setup_fitting_tab(self):
        """Setup the parameter fitting tab with multi-model support"""
        self.fitting_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.fitting_frame, text="Multi-Model Fitting")
        
        # Create left and right panels
        left_panel = ttk.Frame(self.fitting_frame)
        left_panel.pack(side='left', fill='both', expand=True, padx=(10,5), pady=10)
        
        right_panel = ttk.Frame(self.fitting_frame)
        right_panel.pack(side='right', fill='both', expand=True, padx=(5,10), pady=10)
        
        # Left Panel: Models and Datasets
        # Models section
        models_frame = ttk.LabelFrame(left_panel, text="Models", padding=10)
        models_frame.pack(fill='both', expand=True, pady=(0,5))
        
        # Model listbox with scrollbar
        models_list_frame = ttk.Frame(models_frame)
        models_list_frame.pack(fill='both', expand=True)
        
        self.models_listbox = tk.Listbox(models_list_frame, selectmode='multiple')
        models_scrollbar = ttk.Scrollbar(models_list_frame, orient="vertical", command=self.models_listbox.yview)
        self.models_listbox.configure(yscrollcommand=models_scrollbar.set)
        
        self.models_listbox.pack(side="left", fill="both", expand=True)
        models_scrollbar.pack(side="right", fill="y")
        
        # Model controls
        models_controls = ttk.Frame(models_frame)
        models_controls.pack(fill='x', pady=(5,0))
        
        ttk.Button(models_controls, text="Delete Model", command=self.delete_model).pack(side='left', padx=(0,5))
        ttk.Button(models_controls, text="View Model Info", command=self.view_model_info).pack(side='left', padx=5)
        
        # Datasets section
        datasets_frame = ttk.LabelFrame(left_panel, text="Datasets", padding=10)
        datasets_frame.pack(fill='both', expand=True, pady=(5,0))
        
        # Dataset listbox with scrollbar
        datasets_list_frame = ttk.Frame(datasets_frame)
        datasets_list_frame.pack(fill='both', expand=True)
        
        self.datasets_listbox = tk.Listbox(datasets_list_frame, selectmode='multiple')
        datasets_scrollbar = ttk.Scrollbar(datasets_list_frame, orient="vertical", command=self.datasets_listbox.yview)
        self.datasets_listbox.configure(yscrollcommand=datasets_scrollbar.set)
        
        self.datasets_listbox.pack(side="left", fill="both", expand=True)
        datasets_scrollbar.pack(side="right", fill="y")
        
        # Dataset controls
        datasets_controls = ttk.Frame(datasets_frame)
        datasets_controls.pack(fill='x', pady=(5,0))
        
        ttk.Button(datasets_controls, text="Load Dataset", command=self.load_dataset).pack(side='left', padx=(0,5))
        ttk.Button(datasets_controls, text="Delete Dataset", command=self.delete_dataset).pack(side='left', padx=5)
        ttk.Button(datasets_controls, text="View Dataset Info", command=self.view_dataset_info).pack(side='left', padx=5)
        
        # Right Panel: Parameters and Fitting
        # All fitting parameters section
        params_frame = ttk.LabelFrame(right_panel, text="All Fitting Parameters", padding=10)
        params_frame.pack(fill='both', expand=True, pady=(0,5))
        
        # Parameters listbox with scrollbar
        params_list_frame = ttk.Frame(params_frame)
        params_list_frame.pack(fill='both', expand=True)
        
        self.params_listbox = tk.Listbox(params_list_frame, selectmode='multiple')
        params_scrollbar = ttk.Scrollbar(params_list_frame, orient="vertical", command=self.params_listbox.yview)
        self.params_listbox.configure(yscrollcommand=params_scrollbar.set)
        
        self.params_listbox.pack(side="left", fill="both", expand=True)
        params_scrollbar.pack(side="right", fill="y")
        
        # Parameter controls
        params_controls = ttk.Frame(params_frame)
        params_controls.pack(fill='x', pady=(5,0))
        
        ttk.Button(params_controls, text="View Parameter Info", command=self.view_parameter_info).pack(side='left', padx=(0,5))
        ttk.Button(params_controls, text="Modify Parameter", command=self.modify_parameter).pack(side='left', padx=5)
        
        # Fitting controls section
        fitting_frame = ttk.LabelFrame(right_panel, text="Model-Dataset Pairing & Fitting", padding=10)
        fitting_frame.pack(fill='x', pady=(5,0))
        
        # Model-Dataset pairs management
        pairs_frame = ttk.LabelFrame(fitting_frame, text="Model-Dataset Pairs", padding=5)
        pairs_frame.pack(fill='x', pady=(0,10))
        
        # Current pairs listbox
        pairs_list_frame = ttk.Frame(pairs_frame)
        pairs_list_frame.pack(fill='x', pady=5)
        
        ttk.Label(pairs_list_frame, text="Current Pairs:").pack(anchor='w')
        self.pairs_listbox = tk.Listbox(pairs_list_frame, height=4)
        self.pairs_listbox.pack(fill='x', pady=2)
        
        # Add new pair controls
        add_pair_frame = ttk.Frame(pairs_frame)
        add_pair_frame.pack(fill='x', pady=5)
        
        ttk.Label(add_pair_frame, text="Model:").grid(row=0, column=0, sticky='w', padx=(0,5))
        self.model_combo = ttk.Combobox(add_pair_frame, width=15, state='readonly')
        self.model_combo.grid(row=0, column=1, padx=5)
        
        ttk.Label(add_pair_frame, text="Dataset:").grid(row=0, column=2, sticky='w', padx=(10,5))
        self.dataset_combo = ttk.Combobox(add_pair_frame, width=15, state='readonly')
        self.dataset_combo.grid(row=0, column=3, padx=5)
        
        # Pair management buttons
        pair_buttons_frame = ttk.Frame(pairs_frame)
        pair_buttons_frame.pack(fill='x', pady=5)
        
        ttk.Button(pair_buttons_frame, text="Add Pair", command=self.add_model_dataset_pair).pack(side='left', padx=(0,5))
        ttk.Button(pair_buttons_frame, text="Remove Pair", command=self.remove_model_dataset_pair).pack(side='left', padx=5)
        ttk.Button(pair_buttons_frame, text="Clear All", command=self.clear_all_pairs).pack(side='left', padx=5)
        
        # Fitting method and controls
        fitting_controls_frame = ttk.Frame(fitting_frame)
        fitting_controls_frame.pack(fill='x', pady=5)
        
        ttk.Label(fitting_controls_frame, text="Method:").pack(side='left')
        self.fitting_method_var = tk.StringVar(value="nelder")
        method_combo = ttk.Combobox(fitting_controls_frame, textvariable=self.fitting_method_var,
                                  values=["nelder", "differential_evolution", "leastsq"], width=20)
        method_combo.pack(side='left', padx=(5,10))
        
        ttk.Button(fitting_controls_frame, text="Start Multi-Model Fitting", command=self.start_multimodel_fitting).pack(side='left', padx=5)
        
        # Fitting status
        self.fitting_status_var = tk.StringVar(value="Ready for fitting")
        ttk.Label(fitting_frame, textvariable=self.fitting_status_var).pack(pady=5)
        
        # Initialize model-dataset pairs list
        self.model_dataset_pairs = []
        
        # Update combo boxes with any existing models/datasets
        self.update_combo_boxes()
        
    def open_results_window(self, title="FDTR Results", show_fitting_results=False):
        """Open a new window for displaying results"""
        results_window = tk.Toplevel(self.root)
        results_window.title(title)
        results_window.geometry("900x700")
        
        # Create matplotlib figure
        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        canvas = FigureCanvasTkAgg(fig, results_window)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
        # Controls frame
        controls_frame = ttk.Frame(results_window)
        controls_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(controls_frame, text="Plot Results", 
                  command=lambda: self.plot_results_in_window(ax, canvas)).pack(side='left', padx=5)
        ttk.Button(controls_frame, text="Sensitivity Analysis", 
                  command=lambda: self.sensitivity_analysis_in_window(ax, canvas)).pack(side='left', padx=5)
        ttk.Button(controls_frame, text="Save Results", command=self.save_results).pack(side='left', padx=5)
        ttk.Button(controls_frame, text="Clear Plot", 
                  command=lambda: self.clear_plot_in_window(ax, canvas)).pack(side='left', padx=5)
        
        # Results text area (only show if fitting results)
        if show_fitting_results:
            results_text_frame = ttk.LabelFrame(results_window, text="Fitting Results", padding=10)
            results_text_frame.pack(fill='x', padx=10, pady=5)
            
            results_text = tk.Text(results_text_frame, height=8)
            results_scrollbar = ttk.Scrollbar(results_text_frame, orient="vertical", command=results_text.yview)
            results_text.configure(yscrollcommand=results_scrollbar.set)
            
            results_text.pack(side="left", fill="both", expand=True)
            results_scrollbar.pack(side="right", fill="y")
            
            return results_window, ax, canvas, results_text
        
        return results_window, ax, canvas, None
        
    def create_domain(self):
        """Create a new domain with specified temperature"""
        try:
            temperature = float(self.temp_var.get())
            self.domain = Domain(temperature)
            self.update_structure_display()

        except ValueError:
            messagebox.showerror("Error", "Invalid temperature value")
        except Exception as e:
            messagebox.showerror("Error", f"Error creating domain: {str(e)}")
            
    def add_substrate(self):
        """Add substrate to the domain"""
        if self.domain is None:
            messagebox.showerror("Error", "Please create a domain first")
            return
            
        try:
            material_name = self.substrate_var.get()
            material_class = self.materials[material_name]
            self.domain.add_substrate(material_class)
            
            self.update_structure_display()
            messagebox.showinfo("Success", f"Added {material_name} substrate")
        except Exception as e:
            messagebox.showerror("Error", f"Error adding substrate: {str(e)}")
            
    def add_layer(self):
        """Add a layer to the domain with automatic interface conductance and fitting parameters"""
        if self.domain is None:
            messagebox.showerror("Error", "Please create a domain first")
            return
            
        try:
            thickness = float(eval(self.thickness_var.get()))
            material_name = self.layer_material_var.get()
            material_class = self.materials[material_name]
            conductance = float(eval(self.interface_cond_var.get()))
            
            # Add the layer (this automatically creates an interface)
            self.domain.add_layer(thickness, material_class)
            
            # Get the interface number (number of layers added so far)
            interface_num = len([layer for layer in self.domain.heat_path if hasattr(layer, 'thickness')])
            
            # Set the interface conductance for the newly created interface
            self.domain.set_interface_condu(interface_num-1, conductance)
            
            # Initialize fitting parameters if needed
            if self.fitting_params is None:
                self.fitting_params = Fitting_parameters()
            
            # Add fitting parameters if checkboxes are checked
            layer_index = interface_num - 1  # Current layer index
            
            if self.thickness_is_fitting.get():
                # Get custom parameter name or use default
                default_name = f"thick_{layer_index}"
                param_name = simpledialog.askstring("Parameter Name", 
                                                   f"Enter name for thickness parameter:", 
                                                   initialvalue=default_name)
                if param_name:
                    min_val = float(eval(self.thickness_min_var.get())) if self.thickness_min_var.get() else None
                    max_val = float(eval(self.thickness_max_var.get())) if self.thickness_max_var.get() else None
                    self.fitting_params.add(param_name, thickness, min_val, max_val)
                    # Set layer parameter to use fitting parameter
                    self.domain.set_layer_param(layer_index, thickness=self.fitting_params.get_parameter(param_name))
                    messagebox.showinfo("Info", f"Added thickness fitting parameter: {param_name}")
            
            if self.interface_is_fitting.get():
                # Get custom parameter name or use default
                default_name = f"interface_{layer_index}"
                param_name = simpledialog.askstring("Parameter Name", 
                                                   f"Enter name for interface conductance parameter:", 
                                                   initialvalue=default_name)
                if param_name:
                    min_val = float(eval(self.interface_min_var.get())) if self.interface_min_var.get() else None
                    max_val = float(eval(self.interface_max_var.get())) if self.interface_max_var.get() else None
                    self.fitting_params.add(param_name, conductance, min_val, max_val)
                    # Update interface with fitting parameter
                    # Note: This would need to be handled in the domain/model setup
                    messagebox.showinfo("Info", f"Added interface fitting parameter: {param_name}")
            
            self.update_structure_display()
            messagebox.showinfo("Success", f"Added {material_name} layer ({thickness} cm) with interface conductance {conductance} W/cm²K")
            
            # Clear fitting bounds for next layer
            self.thickness_min_var.set("")
            self.thickness_max_var.set("")
            self.interface_min_var.set("")
            self.interface_max_var.set("")
            self.thickness_is_fitting.set(False)
            self.interface_is_fitting.set(False)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error adding layer: {str(e)}")
            
    def update_structure_display(self):
        """Update the structure display text"""
        if self.domain is None:
            self.structure_text.delete(1.0, tk.END)
            self.structure_text.insert(tk.END, "No domain created")
            return
            
        self.structure_text.delete(1.0, tk.END)
        self.structure_text.insert(tk.END, f"Domain Temperature: {self.domain.temperature}K\n\n")
        
        if hasattr(self.domain, 'heat_path') and self.domain.heat_path:
            self.structure_text.insert(tk.END, "Heat Path Structure:\n")
            for i, layer in enumerate(self.domain.heat_path):
                if hasattr(layer, 'thickness'):
                    material_name = getattr(layer.material, 'materialname', 'Unknown')
                    self.structure_text.insert(tk.END, f"Layer {i//2}: {material_name} ({layer.thickness} cm)\n")
                else:
                    self.structure_text.insert(tk.END, f"Interface {i//2}: Conductance = {getattr(layer, 'tbc', 'Not set')}\n")
                    
    def create_model(self):
        """Create the FDTR model with fitting parameters"""
        if self.domain is None:
            messagebox.showerror("Error", "Please create a domain first")
            return
            
        try:
            # Initialize fitting parameters if needed
            if self.fitting_params is None:
                self.fitting_params = Fitting_parameters()
            
            # Add substrate property fitting parameters if selected
            if self.sub_kz_is_fitting.get() and self.sub_kz_var.get():
                kz_value = float(eval(self.sub_kz_var.get()))
                default_name = "sub_kz"
                param_name = simpledialog.askstring("Parameter Name", 
                                                   f"Enter name for substrate kz parameter:", 
                                                   initialvalue=default_name)
                if param_name:
                    min_val = float(eval(self.sub_kz_min_var.get())) if self.sub_kz_min_var.get() else None
                    max_val = float(eval(self.sub_kz_max_var.get())) if self.sub_kz_max_var.get() else None
                    self.fitting_params.add(param_name, kz_value, min_val, max_val)
                    # Apply to substrate (index 0 in heat_path)
                    if len(self.domain.heat_path) > 0:
                        self.domain.set_layer_param(0, kzz=self.fitting_params.get_parameter(param_name))
                    messagebox.showinfo("Info", f"Added substrate kz fitting parameter: {param_name}")
            
            if self.sub_kxx_is_fitting.get() and self.sub_kxx_var.get():
                kxx_value = float(eval(self.sub_kxx_var.get()))
                default_name = "sub_kxx"
                param_name = simpledialog.askstring("Parameter Name", 
                                                   f"Enter name for substrate kxx parameter:", 
                                                   initialvalue=default_name)
                if param_name:
                    min_val = float(eval(self.sub_kxx_min_var.get())) if self.sub_kxx_min_var.get() else None
                    max_val = float(eval(self.sub_kxx_max_var.get())) if self.sub_kxx_max_var.get() else None
                    self.fitting_params.add(param_name, kxx_value, min_val, max_val)
                    if len(self.domain.heat_path) > 0:
                        self.domain.set_layer_param(0, kxx=self.fitting_params.get_parameter(param_name))
                    messagebox.showinfo("Info", f"Added substrate kxx fitting parameter: {param_name}")
            
            if self.sub_cp_is_fitting.get() and self.sub_cp_var.get():
                cp_value = float(eval(self.sub_cp_var.get()))
                default_name = "sub_cp"
                param_name = simpledialog.askstring("Parameter Name", 
                                                   f"Enter name for substrate cp parameter:", 
                                                   initialvalue=default_name)
                if param_name:
                    min_val = float(eval(self.sub_cp_min_var.get())) if self.sub_cp_min_var.get() else None
                    max_val = float(eval(self.sub_cp_max_var.get())) if self.sub_cp_max_var.get() else None
                    self.fitting_params.add(param_name, cp_value, min_val, max_val)
                    if len(self.domain.heat_path) > 0:
                        self.domain.set_layer_param(0, cp=self.fitting_params.get_parameter(param_name))
                    messagebox.showinfo("Info", f"Added substrate cp fitting parameter: {param_name}")
            
            # Add layer property fitting parameters if selected
            layer_count = len([layer for layer in self.domain.heat_path if hasattr(layer, 'thickness')])
            
            if self.layer_kz_is_fitting.get() and self.layer_kz_var.get() and layer_count > 0:
                kz_value = float(eval(self.layer_kz_var.get()))
                default_name = "layer_kz"
                param_name = simpledialog.askstring("Parameter Name", 
                                                   f"Enter name for layer kz parameter:", 
                                                   initialvalue=default_name)
                if param_name:
                    min_val = float(eval(self.layer_kz_min_var.get())) if self.layer_kz_min_var.get() else None
                    max_val = float(eval(self.layer_kz_max_var.get())) if self.layer_kz_max_var.get() else None
                    self.fitting_params.add(param_name, kz_value, min_val, max_val)
                    # Apply to last layer
                    self.domain.set_layer_param(layer_count-1, kzz=self.fitting_params.get_parameter(param_name))
                    messagebox.showinfo("Info", f"Added layer kz fitting parameter: {param_name}")
            
            if self.layer_kxx_is_fitting.get() and self.layer_kxx_var.get() and layer_count > 0:
                kxx_value = float(eval(self.layer_kxx_var.get()))
                default_name = "layer_kxx"
                param_name = simpledialog.askstring("Parameter Name", 
                                                   f"Enter name for layer kxx parameter:", 
                                                   initialvalue=default_name)
                if param_name:
                    min_val = float(eval(self.layer_kxx_min_var.get())) if self.layer_kxx_min_var.get() else None
                    max_val = float(eval(self.layer_kxx_max_var.get())) if self.layer_kxx_max_var.get() else None
                    self.fitting_params.add(param_name, kxx_value, min_val, max_val)
                    self.domain.set_layer_param(layer_count-1, kxx=self.fitting_params.get_parameter(param_name))
                    messagebox.showinfo("Info", f"Added layer kxx fitting parameter: {param_name}")
            
            if self.layer_cp_is_fitting.get() and self.layer_cp_var.get() and layer_count > 0:
                cp_value = float(eval(self.layer_cp_var.get()))
                default_name = "layer_cp"
                param_name = simpledialog.askstring("Parameter Name", 
                                                   f"Enter name for layer cp parameter:", 
                                                   initialvalue=default_name)
                if param_name:
                    min_val = float(eval(self.layer_cp_min_var.get())) if self.layer_cp_min_var.get() else None
                    max_val = float(eval(self.layer_cp_max_var.get())) if self.layer_cp_max_var.get() else None
                    self.fitting_params.add(param_name, cp_value, min_val, max_val)
                    self.domain.set_layer_param(layer_count-1, cp=self.fitting_params.get_parameter(param_name))
                    messagebox.showinfo("Info", f"Added layer cp fitting parameter: {param_name}")
            
            # Handle beam parameter fitting
            pump_radius = float(eval(self.pump_radius_var.get()))
            probe_radius = float(eval(self.probe_radius_var.get()))
            beam_offset = float(eval(self.beam_offset_var.get()))
            
            if self.pump_radius_is_fitting.get():
                default_name = "pump_radius"
                param_name = simpledialog.askstring("Parameter Name", 
                                                   f"Enter name for pump radius parameter:", 
                                                   initialvalue=default_name)
                if param_name:
                    min_val = float(eval(self.pump_radius_min_var.get())) if self.pump_radius_min_var.get() else None
                    max_val = float(eval(self.pump_radius_max_var.get())) if self.pump_radius_max_var.get() else None
                    self.fitting_params.add(param_name, pump_radius, min_val, max_val)
                    pump_radius = self.fitting_params.get_parameter(param_name)
                    messagebox.showinfo("Info", f"Added pump radius fitting parameter: {param_name}")
            
            if self.probe_radius_is_fitting.get():
                default_name = "probe_radius"
                param_name = simpledialog.askstring("Parameter Name", 
                                                   f"Enter name for probe radius parameter:", 
                                                   initialvalue=default_name)
                if param_name:
                    min_val = float(eval(self.probe_radius_min_var.get())) if self.probe_radius_min_var.get() else None
                    max_val = float(eval(self.probe_radius_max_var.get())) if self.probe_radius_max_var.get() else None
                    self.fitting_params.add(param_name, probe_radius, min_val, max_val)
                    probe_radius = self.fitting_params.get_parameter(param_name)
                    messagebox.showinfo("Info", f"Added probe radius fitting parameter: {param_name}")
            
            if self.beam_offset_is_fitting.get():
                default_name = "beam_offset"
                param_name = simpledialog.askstring("Parameter Name", 
                                                   f"Enter name for beam offset parameter:", 
                                                   initialvalue=default_name)
                if param_name:
                    min_val = float(eval(self.beam_offset_min_var.get())) if self.beam_offset_min_var.get() else None
                    max_val = float(eval(self.beam_offset_max_var.get())) if self.beam_offset_max_var.get() else None
                    self.fitting_params.add(param_name, beam_offset, min_val, max_val)
                    beam_offset = self.fitting_params.get_parameter(param_name)
                    messagebox.showinfo("Info", f"Added beam offset fitting parameter: {param_name}")
            
            backend = self.backend_var.get()
            
            self.model = FourierModelFDTR(self.domain, pump_radius, probe_radius, beam_offset, 
                                        fitting_params=self.fitting_params, backend=backend)
            
            # Ask for model name and store it
            model_name = simpledialog.askstring("Model Name", 
                                               f"Enter name for this model:", 
                                               initialvalue=f"Model_{self.model_counter}")
            if model_name:
                self.models[model_name] = self.model
                self.model_counter += 1
                self.model_status_var.set(f"Model '{model_name}' created with {backend} backend")
                messagebox.showinfo("Success", f"FDTR model '{model_name}' created successfully")
            else:
                self.model_status_var.set(f"Model created with {backend} backend")
                messagebox.showinfo("Success", "FDTR model created successfully")
            
            # Update fitting info display
            self.update_model_list()
        except Exception as e:
            messagebox.showerror("Error", f"Error creating model: {str(e)}")
            
    def calculate_phase(self):
        """Calculate phase for the frequency range"""
        if self.model is None:
            messagebox.showerror("Error", "Please create a model first")
            return
            
        try:
            freq_start = float(eval(self.freq_start_var.get()))
            freq_end = float(eval(self.freq_end_var.get()))
            freq_step = float(eval(self.freq_step_var.get()))
            
            self.frequencies = np.arange(freq_start, freq_end, freq_step)
            
            # Calculate phases
            phases = []
            for f in self.frequencies:
                phases.append(self.model.get_phase(f))
                
            self.calculated_phases = np.array(phases)
            
            # Open results window and plot
            results_window, ax, canvas, _ = self.open_results_window("Phase Calculation Results")
            
            ax.semilogx(self.frequencies, self.calculated_phases, 'b-', label='Calculated')
            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('Phase (rad)')
            ax.set_title('FDTR Phase Response')
            ax.grid(True)
            ax.legend()
            canvas.draw()
            
            messagebox.showinfo("Success", f"Calculated phase for {len(self.frequencies)} frequencies")
        except Exception as e:
            messagebox.showerror("Error", f"Error calculating phase: {str(e)}")
            
    def load_experimental_data(self):
        """Load experimental data from file"""
        filename = filedialog.askopenfilename(
            title="Select experimental data file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                # Load data and skip header
                load = np.genfromtxt(filename, skip_header=2)
                # Keep only frequency and phase columns
                self.experimental_data = np.delete(load, 1, 1)
                
                self.data_status_var.set(f"Loaded {len(self.experimental_data)} data points")
                messagebox.showinfo("Success", f"Loaded experimental data from {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Error", f"Error loading data: {str(e)}")
            
    def start_fitting(self):
        """Start parameter fitting"""
        if self.model is None:
            messagebox.showerror("Error", "Please create a model first")
            return
            
        if self.experimental_data is None:
            messagebox.showerror("Error", "Please load experimental data first")
            return
            
        if self.fitting_params is None:
            messagebox.showerror("Error", "Please add fitting parameters first")
            return
            
        try:
            method = self.fitting_method_var.get()
            
            # Recreate model with fitting parameters
            pump_radius = float(eval(self.pump_radius_var.get()))
            probe_radius = float(eval(self.probe_radius_var.get()))
            beam_offset = float(eval(self.beam_offset_var.get()))
            backend = self.backend_var.get()
            
            self.model = FourierModelFDTR(self.domain, pump_radius, probe_radius, beam_offset,
                                        fitting_params=self.fitting_params, backend=backend, jit=True)
            
            # Perform fitting
            out = self.model.minimize(self.experimental_data, method=method)
            
            # Open results window with fitting results
            results_window, ax, canvas, results_text = self.open_results_window("Parameter Fitting Results", show_fitting_results=True)
            
            # Display fitting results in text area
            results_text.delete(1.0, tk.END)
            results_text.insert(tk.END, lmfit.fit_report(out))
            
            # Plot comparison
            ax.scatter(self.experimental_data[:, 0], self.experimental_data[:, 1], 
                      color='red', label='Experimental', alpha=0.7)
            
            # Calculate fitted curve
            phases_fitted = []
            for f in self.experimental_data[:, 0]:
                phases_fitted.append(self.model.get_phase(f))
            ax.semilogx(self.experimental_data[:, 0], phases_fitted, 'g-', label='Fitted')
            
            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('Phase (rad)')
            ax.set_title('Parameter Fitting Results')
            ax.grid(True)
            ax.legend()
            canvas.draw()
            
            messagebox.showinfo("Success", "Parameter fitting completed")
        except Exception as e:
            messagebox.showerror("Error", f"Error during fitting: {str(e)}")
            
    def plot_results_in_window(self, ax, canvas):
        """Plot experimental data and fitted results in the window"""
        if self.experimental_data is None:
            messagebox.showerror("Error", "No experimental data loaded")
            return
            
        ax.clear()
        
        # Plot experimental data
        ax.scatter(self.experimental_data[:, 0], self.experimental_data[:, 1], 
                   color='red', label='Experimental', alpha=0.7)
        
        # Plot calculated data if available
        if hasattr(self, 'calculated_phases') and self.frequencies is not None:
            ax.semilogx(self.frequencies, self.calculated_phases, 'b-', label='Calculated')
            
        # If model exists, calculate phases for experimental frequencies
        if self.model is not None:
            phases_fitted = []
            for f in self.experimental_data[:, 0]:
                phases_fitted.append(self.model.get_phase(f))
            ax.semilogx(self.experimental_data[:, 0], phases_fitted, 'g-', label='Fitted')
        
        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('Phase (rad)')
        ax.set_title('FDTR Results')
        ax.grid(True)
        ax.legend()
        canvas.draw()
        
    def sensitivity_analysis_in_window(self, ax, canvas):
        """Perform sensitivity analysis in the window"""
        if self.model is None or self.fitting_params is None:
            messagebox.showerror("Error", "Please create a model with fitting parameters first")
            return
            
        try:
            # Get parameter name for sensitivity analysis
            param_name = simpledialog.askstring("Sensitivity Analysis", 
                                               "Enter parameter name for sensitivity analysis:")
            if not param_name:
                return
                
            sensitivity = self.model.sensitivity_analysis(param_name)
            freqs, sens_vals = sensitivity
            
            ax.clear()
            ax.semilogx(freqs, sens_vals, 'r-', label=f'Sensitivity to {param_name}')
            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('Sensitivity')
            ax.set_title(f'Sensitivity Analysis for {param_name}')
            ax.grid(True)
            ax.legend()
            canvas.draw()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error in sensitivity analysis: {str(e)}")
            
    def clear_plot_in_window(self, ax, canvas):
        """Clear the plot in the window"""
        ax.clear()
        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('Phase (rad)')
        ax.set_title('FDTR Results')
        ax.grid(True)
        canvas.draw()

    def save_results(self):
        """Save results to file"""
        if not hasattr(self, 'calculated_phases'):
            messagebox.showerror("Error", "No calculated results to save")
            return
            
        filename = filedialog.asksaveasfilename(
            title="Save results",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                data = np.column_stack((self.frequencies, self.calculated_phases))
                np.savetxt(filename, data, header="Frequency(Hz)\tPhase(rad)", delimiter='\t')
                messagebox.showinfo("Success", f"Results saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Error saving results: {str(e)}")
                
    def on_substrate_material_change(self, event=None):
        """Handle substrate material selection change"""
        self.load_substrate_defaults()
        
    def on_layer_material_change(self, event=None):
        """Handle layer material selection change"""
        self.load_layer_defaults()
        
    def load_substrate_defaults(self):
        """Load default substrate material properties"""
        try:
            material_name = self.substrate_var.get()
            if material_name not in self.materials:
                return
                
            # Create a temporary instance to get default values
            material_class = self.materials[material_name]
            temp_material = material_class(float(self.temp_var.get()) if self.temp_var.get() else 300)
            
            # Load substrate thermal properties
            if hasattr(temp_material, 'kzz'):
                self.sub_kz_var.set(str(temp_material.kzz))
            elif hasattr(temp_material, 'kxx'):
                self.sub_kz_var.set(str(temp_material.kxx))
                
            if hasattr(temp_material, 'kxx'):
                self.sub_kxx_var.set(str(temp_material.kxx))
                
            if hasattr(temp_material, 'cp'):
                # Convert cp to J/cm³K (cp is usually in J/gK, multiply by density)
                if hasattr(temp_material, 'density'):
                    cp_volumetric = temp_material.cp * temp_material.density
                    self.sub_cp_var.set(str(cp_volumetric))
                else:
                    self.sub_cp_var.set(str(temp_material.cp))
                    
        except Exception as e:
            print(f"Note: Could not load all substrate properties for {material_name}: {str(e)}")
            
    def load_layer_defaults(self):
        """Load default layer material properties"""
        try:
            material_name = self.layer_material_var.get()
            if material_name not in self.materials:
                return
                
            # Create a temporary instance to get default values
            material_class = self.materials[material_name]
            temp_material = material_class(float(self.temp_var.get()) if self.temp_var.get() else 300)
            
            # Load layer thermal properties
            if hasattr(temp_material, 'kzz'):
                self.layer_kz_var.set(str(temp_material.kzz))
            elif hasattr(temp_material, 'kxx'):
                self.layer_kz_var.set(str(temp_material.kxx))
                
            if hasattr(temp_material, 'kxx'):
                self.layer_kxx_var.set(str(temp_material.kxx))
                
            if hasattr(temp_material, 'cp'):
                # Convert cp to J/cm³K (cp is usually in J/gK, multiply by density)
                if hasattr(temp_material, 'density'):
                    cp_volumetric = temp_material.cp * temp_material.density
                    self.layer_cp_var.set(str(cp_volumetric))
                else:
                    self.layer_cp_var.set(str(temp_material.cp))
                    
        except Exception as e:
            print(f"Note: Could not load all layer properties for {material_name}: {str(e)}")
            
    def load_material_defaults(self):
        """Load default material properties for both substrate and layer"""
        self.load_substrate_defaults()
        self.load_layer_defaults()
            
    def update_model_list(self):
        """Update the model list display"""
        if hasattr(self, 'models_listbox'):
            self.models_listbox.delete(0, tk.END)
            for model_name in self.models.keys():
                self.models_listbox.insert(tk.END, model_name)
            self.update_parameter_list()
            self.update_combo_boxes()
    
    def update_dataset_list(self):
        """Update the dataset list display"""
        if hasattr(self, 'datasets_listbox'):
            self.datasets_listbox.delete(0, tk.END)
            for dataset_name in self.datasets.keys():
                self.datasets_listbox.insert(tk.END, dataset_name)
            self.update_combo_boxes()
    
    def update_parameter_list(self):
        """Update the parameter list display with all parameters from all models"""
        if hasattr(self, 'params_listbox'):
            self.params_listbox.delete(0, tk.END)
            all_params = set()
            
            # Collect all parameter names from all models
            for model_name, model in self.models.items():
                if hasattr(model, 'fitting_params') and model.fitting_params:
                    try:
                        # Try different ways to get parameter names
                        if hasattr(model.fitting_params, 'params'):
                            # lmfit Parameters object
                            for param_name in model.fitting_params.params.keys():
                                all_params.add(f"{model_name}:{param_name}")
                        elif hasattr(model.fitting_params, 'param_names'):
                            # Custom param_names attribute
                            for param in model.fitting_params.param_names:
                                all_params.add(f"{model_name}:{param}")
                        elif hasattr(model.fitting_params, '__dict__'):
                            # Check object attributes
                            for attr_name, attr_value in model.fitting_params.__dict__.items():
                                if not attr_name.startswith('_'):
                                    all_params.add(f"{model_name}:{attr_name}")
                    except Exception as e:
                        print(f"Could not access parameters for model {model_name}: {e}")
            
            # Add parameters to listbox
            for param in sorted(all_params):
                self.params_listbox.insert(tk.END, param)
    
    def load_dataset(self):
        """Load a dataset and store it with a name"""
        filename = filedialog.askopenfilename(
            title="Select experimental data file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                # Load data and skip header
                load = np.genfromtxt(filename, skip_header=2)
                # Keep only frequency and phase columns
                data = np.delete(load, 1, 1)
                
                # Ask for dataset name
                dataset_name = simpledialog.askstring("Dataset Name", 
                                                     f"Enter name for this dataset:", 
                                                     initialvalue=f"Dataset_{self.dataset_counter}")
                if dataset_name:
                    self.datasets[dataset_name] = data
                    self.dataset_counter += 1
                    self.update_dataset_list()
                    messagebox.showinfo("Success", f"Loaded dataset '{dataset_name}' with {len(data)} data points")
                    
                    # Also update the old experimental_data for backward compatibility
                    self.experimental_data = data
                    if hasattr(self, 'data_status_var'):
                        self.data_status_var.set(f"Loaded {len(data)} data points")
                        
            except Exception as e:
                messagebox.showerror("Error", f"Error loading data: {str(e)}")
    
    def delete_model(self):
        """Delete selected model(s)"""
        selected = self.models_listbox.curselection()
        if not selected:
            messagebox.showwarning("Warning", "Please select model(s) to delete")
            return
            
        for index in reversed(selected):  # Delete in reverse order to maintain indices
            model_name = self.models_listbox.get(index)
            if messagebox.askyesno("Confirm", f"Delete model '{model_name}'?"):
                del self.models[model_name]
        
        self.update_model_list()
    
    def delete_dataset(self):
        """Delete selected dataset(s)"""
        selected = self.datasets_listbox.curselection()
        if not selected:
            messagebox.showwarning("Warning", "Please select dataset(s) to delete")
            return
            
        for index in reversed(selected):  # Delete in reverse order to maintain indices
            dataset_name = self.datasets_listbox.get(index)
            if messagebox.askyesno("Confirm", f"Delete dataset '{dataset_name}'?"):
                del self.datasets[dataset_name]
        
        self.update_dataset_list()
    
    def view_model_info(self):
        """View information about selected model"""
        selected = self.models_listbox.curselection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a model to view")
            return
        
        model_name = self.models_listbox.get(selected[0])
        model = self.models[model_name]
        
        info_window = tk.Toplevel(self.root)
        info_window.title(f"Model Info: {model_name}")
        info_window.geometry("600x400")
        
        info_text = tk.Text(info_window, height=20, width=60)
        info_scrollbar = ttk.Scrollbar(info_window, orient="vertical", command=info_text.yview)
        info_text.configure(yscrollcommand=info_scrollbar.set)
        
        info_text.pack(side="left", fill="both", expand=True)
        info_scrollbar.pack(side="right", fill="y")
        
        # Display model information
        info_text.insert(tk.END, f"Model Name: {model_name}\n")
        info_text.insert(tk.END, f"Model Type: {type(model).__name__}\n")
        info_text.insert(tk.END, f"Backend: {getattr(model, 'backend', 'Unknown')}\n")
        
        if hasattr(model, 'domain') and model.domain:
            info_text.insert(tk.END, f"Domain Temperature: {model.domain.temperature}K\n")
            
        if hasattr(model, 'fitting_params') and model.fitting_params:
            info_text.insert(tk.END, "\nFitting Parameters:\n")
            try:
                param_names = getattr(model.fitting_params, 'param_names', [])
                for param in param_names:
                    param_obj = model.fitting_params.get_parameter(param)
                    info_text.insert(tk.END, f"  {param}: {param_obj}\n")
            except Exception as e:
                info_text.insert(tk.END, f"  Error accessing parameters: {str(e)}\n")
    
    def view_dataset_info(self):
        """View information about selected dataset"""
        selected = self.datasets_listbox.curselection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a dataset to view")
            return
        
        dataset_name = self.datasets_listbox.get(selected[0])
        data = self.datasets[dataset_name]
        
        info_window = tk.Toplevel(self.root)
        info_window.title(f"Dataset Info: {dataset_name}")
        info_window.geometry("400x300")
        
        info_text = tk.Text(info_window, height=15, width=50)
        info_scrollbar = ttk.Scrollbar(info_window, orient="vertical", command=info_text.yview)
        info_text.configure(yscrollcommand=info_scrollbar.set)
        
        info_text.pack(side="left", fill="both", expand=True)
        info_scrollbar.pack(side="right", fill="y")
        
        # Display dataset information
        info_text.insert(tk.END, f"Dataset Name: {dataset_name}\n")
        info_text.insert(tk.END, f"Data Points: {len(data)}\n")
        info_text.insert(tk.END, f"Frequency Range: {data[:, 0].min():.2e} - {data[:, 0].max():.2e} Hz\n")
        info_text.insert(tk.END, f"Phase Range: {data[:, 1].min():.4f} - {data[:, 1].max():.4f} rad\n")
        
        info_text.insert(tk.END, "\nFirst 10 data points:\n")
        info_text.insert(tk.END, "Frequency (Hz)\tPhase (rad)\n")
        for i in range(min(10, len(data))):
            info_text.insert(tk.END, f"{data[i, 0]:.2e}\t{data[i, 1]:.6f}\n")
    
    def view_parameter_info(self):
        """View information about selected parameter"""
        selected = self.params_listbox.curselection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a parameter to view")
            return
        
        param_full_name = self.params_listbox.get(selected[0])
        model_name, param_name = param_full_name.split(':', 1)
        
        if model_name in self.models:
            model = self.models[model_name]
            if hasattr(model, 'fitting_params') and model.fitting_params:
                try:
                    # Try different ways to get parameter info
                    if hasattr(model.fitting_params, 'params') and param_name in model.fitting_params.params:
                        param_obj = model.fitting_params.params[param_name]
                        info_text = f"Model: {model_name}\nParameter: {param_name}\nValue: {param_obj.value}\nMin: {param_obj.min}\nMax: {param_obj.max}\nVary: {param_obj.vary}"
                    elif hasattr(model.fitting_params, 'get_parameter'):
                        param_obj = model.fitting_params.get_parameter(param_name)
                        info_text = f"Model: {model_name}\nParameter: {param_name}\nValue/Object: {param_obj}"
                    else:
                        param_obj = getattr(model.fitting_params, param_name, "Not found")
                        info_text = f"Model: {model_name}\nParameter: {param_name}\nValue/Object: {param_obj}"
                    
                    messagebox.showinfo("Parameter Info", info_text)
                except Exception as e:
                    messagebox.showerror("Error", f"Cannot access parameter: {str(e)}")
    
    def modify_parameter(self):
        """Modify parameter bounds or value"""
        selected = self.params_listbox.curselection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a parameter to modify")
            return
        
        param_full_name = self.params_listbox.get(selected[0])
        model_name, param_name = param_full_name.split(':', 1)
        
        messagebox.showinfo("Feature Not Implemented", 
                          f"Parameter modification for {param_full_name} is not yet implemented.\n"
                          "You can modify parameters by recreating the model with new settings.")
    
    def start_multimodel_fitting(self):
        """Start multi-model fitting with defined model-dataset pairs"""
        # Check if we have pairs defined
        if not self.model_dataset_pairs:
            messagebox.showwarning("Warning", "Please add at least one model-dataset pair")
            return
        
        try:
            method = self.fitting_method_var.get()
            self.fitting_status_var.set("Fitting in progress...")
            
            # Perform fitting for each model-dataset pair
            results = {}
            
            for model_name, dataset_name in self.model_dataset_pairs:
                if model_name not in self.models:
                    messagebox.showerror("Error", f"Model '{model_name}' not found")
                    continue
                    
                if dataset_name not in self.datasets:
                    messagebox.showerror("Error", f"Dataset '{dataset_name}' not found")
                    continue
                
                model = self.models[model_name]
                data = self.datasets[dataset_name]
                
                # Perform fitting
                result = model.minimize(data, method=method)
                results[f"{model_name}_{dataset_name}"] = result
            
            if results:
                # Display results
                selected_models = [pair[0] for pair in self.model_dataset_pairs]
                selected_datasets = [pair[1] for pair in self.model_dataset_pairs]
                self.show_multimodel_results(results, selected_models, selected_datasets)
                
                self.fitting_status_var.set("Multi-model fitting completed")
                messagebox.showinfo("Success", "Multi-model fitting completed successfully")
            else:
                self.fitting_status_var.set("Fitting failed - no valid pairs")
                messagebox.showerror("Error", "No valid model-dataset pairs found for fitting")
            
        except Exception as e:
            self.fitting_status_var.set("Fitting failed")
            messagebox.showerror("Error", f"Error during multi-model fitting: {str(e)}")
    
    def show_multimodel_results(self, results, model_names, dataset_names):
        """Show results from multi-model fitting"""
        results_window = tk.Toplevel(self.root)
        results_window.title("Multi-Model Fitting Results")
        results_window.geometry("1000x700")
        
        # Create notebook for different result views
        results_notebook = ttk.Notebook(results_window)
        results_notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Text results tab
        text_frame = ttk.Frame(results_notebook)
        results_notebook.add(text_frame, text="Fitting Reports")
        
        results_text = tk.Text(text_frame, height=25, width=80)
        text_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=results_text.yview)
        results_text.configure(yscrollcommand=text_scrollbar.set)
        
        results_text.pack(side="left", fill="both", expand=True)
        text_scrollbar.pack(side="right", fill="y")
        
        # Display fitting results
        for result_name, result in results.items():
            results_text.insert(tk.END, f"{'='*50}\n")
            results_text.insert(tk.END, f"Results for {result_name}\n")
            results_text.insert(tk.END, f"{'='*50}\n")
            results_text.insert(tk.END, lmfit.fit_report(result))
            results_text.insert(tk.END, f"\n\n")
        
        # Plot results tab
        plot_frame = ttk.Frame(results_notebook)
        results_notebook.add(plot_frame, text="Plots")
        
        # Create matplotlib figure
        fig = Figure(figsize=(12, 8), dpi=100)
        
        canvas = FigureCanvasTkAgg(fig, plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
        # Plot comparison for each model-dataset pair
        for i, (model_name, dataset_name) in enumerate(zip(model_names, dataset_names)):
            ax = fig.add_subplot(len(model_names), 1, i+1)
            
            model = self.models[model_name]
            data = self.datasets[dataset_name]
            
            # Plot experimental data
            ax.scatter(data[:, 0], data[:, 1], color='red', label=f'Exp: {dataset_name}', alpha=0.7, s=20)
            
            # Plot fitted curve
            phases_fitted = []
            for f in data[:, 0]:
                phases_fitted.append(model.get_phase(f))
            ax.semilogx(data[:, 0], phases_fitted, 'g-', label=f'Fitted: {model_name}', linewidth=2)
            
            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('Phase (rad)')
            ax.set_title(f'{model_name} vs {dataset_name}')
            ax.grid(True)
            ax.legend()
        
        fig.tight_layout()
        canvas.draw()
    
    # Update the old methods to maintain backward compatibility
    def load_experimental_data(self):
        """Load experimental data from file (backward compatibility)"""
        self.load_dataset()
    
    def start_fitting(self):
        """Start parameter fitting (backward compatibility - single model)"""
        if self.model is None:
            messagebox.showerror("Error", "Please create a model first")
            return
            
        if self.experimental_data is None:
            messagebox.showerror("Error", "Please load experimental data first")
            return
            
        if self.fitting_params is None:
            messagebox.showerror("Error", "Please add fitting parameters first")
            return
            
        try:
            method = self.fitting_method_var.get()
            
            # Recreate model with fitting parameters
            pump_radius = float(eval(self.pump_radius_var.get()))
            probe_radius = float(eval(self.probe_radius_var.get()))
            beam_offset = float(eval(self.beam_offset_var.get()))
            backend = self.backend_var.get()
            
            self.model = FourierModelFDTR(self.domain, pump_radius, probe_radius, beam_offset,
                                        fitting_params=self.fitting_params, backend=backend, jit=True)
            
            # Perform fitting
            out = self.model.minimize(self.experimental_data, method=method)
            
            # Open results window with fitting results
            results_window, ax, canvas, results_text = self.open_results_window("Parameter Fitting Results", show_fitting_results=True)
            
            # Display fitting results in text area
            results_text.delete(1.0, tk.END)
            results_text.insert(tk.END, lmfit.fit_report(out))
            
            # Plot comparison
            ax.scatter(self.experimental_data[:, 0], self.experimental_data[:, 1], 
                      color='red', label='Experimental', alpha=0.7)
            
            # Calculate fitted curve
            phases_fitted = []
            for f in self.experimental_data[:, 0]:
                phases_fitted.append(self.model.get_phase(f))
            ax.semilogx(self.experimental_data[:, 0], phases_fitted, 'g-', label='Fitted')
            
            ax.set_xlabel('Frequency (Hz)')

            ax.set_ylabel('Phase (rad)')
            ax.set_title('Parameter Fitting Results')
            ax.grid(True)
            ax.legend()
            canvas.draw()
            
            messagebox.showinfo("Success", "Parameter fitting completed")
        except Exception as e:
            messagebox.showerror("Error", f"Error during fitting: {str(e)}")

    def update_combo_boxes(self):
        """Update the model and dataset combo boxes"""
        # Update model combo box
        model_names = list(self.models.keys())
        self.model_combo['values'] = model_names
        if model_names and not self.model_combo.get():
            self.model_combo.set(model_names[0])
        
        # Update dataset combo box  
        dataset_names = list(self.datasets.keys())
        self.dataset_combo['values'] = dataset_names
        if dataset_names and not self.dataset_combo.get():
            self.dataset_combo.set(dataset_names[0])
    
    def add_model_dataset_pair(self):
        """Add a new model-dataset pair"""
        model_name = self.model_combo.get()
        dataset_name = self.dataset_combo.get()
        
        if not model_name:
            messagebox.showwarning("Warning", "Please select a model")
            return
        
        if not dataset_name:
            messagebox.showwarning("Warning", "Please select a dataset")
            return
        
        # Check if pair already exists
        pair = (model_name, dataset_name)
        if pair in self.model_dataset_pairs:
            messagebox.showwarning("Warning", f"Pair '{model_name}' - '{dataset_name}' already exists")
            return
        
        # Add the pair
        self.model_dataset_pairs.append(pair)
        self.update_pairs_display()
        
        messagebox.showinfo("Success", f"Added pair: {model_name} - {dataset_name}")
    
    def remove_model_dataset_pair(self):
        """Remove selected model-dataset pair"""
        selected = self.pairs_listbox.curselection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a pair to remove")
            return
        
        # Remove selected pairs (in reverse order to maintain indices)
        for index in reversed(selected):
            del self.model_dataset_pairs[index]
        
        self.update_pairs_display()
    
    def clear_all_pairs(self):
        """Clear all model-dataset pairs"""
        if self.model_dataset_pairs:
            if messagebox.askyesno("Confirm", "Clear all model-dataset pairs?"):
                self.model_dataset_pairs.clear()
                self.update_pairs_display()
    
    def update_pairs_display(self):
        """Update the pairs listbox display"""
        self.pairs_listbox.delete(0, tk.END)
        for model_name, dataset_name in self.model_dataset_pairs:
            self.pairs_listbox.insert(tk.END, f"{model_name} ← → {dataset_name}")


def main():
    """Main function to run the FDTR GUI"""
    root = tk.Tk()
    app = FDTRGui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
