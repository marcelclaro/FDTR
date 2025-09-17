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
    import itertools
except ImportError as e:
    print(f"Error importing pyFDTR: {e}")
    print("Please ensure pyFDTR is properly installed and in your Python path")


class FDTRGui:
    def __init__(self, root):
        self.root = root
        self.root.title("FDTR Interactive Interface")
        self.root.geometry("1200x900")
        
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

        # Initialize top_layer_num for transparent layer management
        self.top_layer_num = 0
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.setup_domain_model_tab()
        self.setup_fitting_tab()
        self.setup_sensitivity_tab()
        
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
        # Add editable combobox for model name and update button at the top
        top_frame = ttk.Frame(self.main_frame)
        top_frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(top_frame, text="Model Name:").pack(side='left')
        self.model_name_var = tk.StringVar()
        self.model_name_combo = ttk.Combobox(top_frame, textvariable=self.model_name_var, width=25)
        self.model_name_combo.pack(side='left', padx=5)
        self.model_name_combo['values'] = list(self.models.keys())
        self.model_name_combo.bind('<<ComboboxSelected>>', self.on_model_name_selected)
        #ttk.Button(top_frame, text="Update Model Parameters", command=self.update_model_parameters).pack(side='left', padx=10)
            
        # Domain Setup Section
        domain_frame = ttk.LabelFrame(self.main_frame, text="Domain Setup", padding=10)
        domain_frame.pack(fill='x', padx=5, pady=5)
        
        # Temperature
        temp_frame = ttk.Frame(domain_frame)
        temp_frame.pack(fill='x', pady=2)
        
        ttk.Label(temp_frame, text="Temperature (K):").pack(side='left')
        self.temp_var = tk.StringVar(value="300")
        ttk.Entry(temp_frame, textvariable=self.temp_var, width=10).pack(side='left', padx=(5,10))
        self.temp_var.trace_add("write", lambda *args: self.load_substrate_defaults())
        self.temp_var.trace_add("write", lambda *args: self.load_layer_defaults())

        # Substrate
        substrate_frame = ttk.Frame(domain_frame)
        substrate_frame.pack(fill='x', pady=3)
        
        ttk.Label(substrate_frame, text="Substrate Material:").pack(side='left')
        self.substrate_var = tk.StringVar(value="Sapphire")
        substrate_combo = ttk.Combobox(substrate_frame, textvariable=self.substrate_var, 
                    values=list(self.materials.keys()), width=15)
        substrate_combo.pack(side='left', padx=(5,10))
        substrate_combo.bind('<<ComboboxSelected>>', self.on_substrate_material_change)
        ttk.Button(substrate_frame, text="Add Substrate", command=self.add_substrate).pack(side='left')

        # Substrate Properties Section
        substrate_props_frame = ttk.LabelFrame(substrate_frame, text="Substrate Properties", padding=10)
        substrate_props_frame.pack(fill='x', padx=5, pady=5)
        
        sub_props_frame = ttk.Frame(substrate_props_frame)
        sub_props_frame.pack(fill='x', pady=5)
        
        # Substrate thermal conductivity kz
        ttk.Label(sub_props_frame, text="Substrate kz (W/cmK):").grid(row=0, column=0, sticky='w')
        self.sub_kz_var = tk.StringVar()
        ttk.Entry(sub_props_frame, textvariable=self.sub_kz_var, width=15).grid(row=0, column=1, padx=2)
        self.sub_kz_is_fitting = tk.BooleanVar()
        def sub_kz_fit_callback(*args):
            if self.sub_kz_is_fitting.get():
                try:
                    val = float(self.sub_kz_var.get())
                    self.sub_kz_min_var.set(str(val * 0.9))
                    self.sub_kz_max_var.set(str(val * 1.1))
                except Exception:
                    pass
        self.sub_kz_is_fitting.trace_add('write', sub_kz_fit_callback)
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
        def sub_kxx_fit_callback(*args):
            if self.sub_kxx_is_fitting.get():
                try:
                    val = float(self.sub_kxx_var.get())
                    self.sub_kxx_min_var.set(str(val * 0.9))
                    self.sub_kxx_max_var.set(str(val * 1.1))
                except Exception:
                    pass
        self.sub_kxx_is_fitting.trace_add('write', sub_kxx_fit_callback)
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
        def sub_cp_fit_callback(*args):
            if self.sub_cp_is_fitting.get():
                try:
                    val = float(self.sub_cp_var.get())
                    self.sub_cp_min_var.set(str(val * 0.9))
                    self.sub_cp_max_var.set(str(val * 1.1))
                except Exception:
                    pass
        self.sub_cp_is_fitting.trace_add('write', sub_cp_fit_callback)
        ttk.Checkbutton(sub_props_frame, text="Fit", variable=self.sub_cp_is_fitting).grid(row=2, column=2, padx=2)
        
        ttk.Label(sub_props_frame, text="Min:").grid(row=2, column=3, sticky='w', padx=(10,2))
        self.sub_cp_min_var = tk.StringVar()
        ttk.Entry(sub_props_frame, textvariable=self.sub_cp_min_var, width=10).grid(row=2, column=4, padx=2)
        
        ttk.Label(sub_props_frame, text="Max:").grid(row=2, column=5, sticky='w', padx=(5,2))
        self.sub_cp_max_var = tk.StringVar()
        
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
        def thickness_fit_callback(*args):
            if self.thickness_is_fitting.get():
                try:
                    val = float(eval(self.thickness_var.get()))
                    self.thickness_min_var.set(str(val * 0.9))
                    self.thickness_max_var.set(str(val * 1.1))
                except Exception:
                    pass
        self.thickness_is_fitting.trace_add('write', thickness_fit_callback)
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
        def interface_fit_callback(*args):
            if self.interface_is_fitting.get():
                try:
                    val = float(eval(self.interface_cond_var.get()))
                    self.interface_min_var.set(str(val * 0.9))
                    self.interface_max_var.set(str(val * 1.1))
                except Exception:
                    pass
        self.interface_is_fitting.trace_add('write', interface_fit_callback)
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
        
        ttk.Entry(sub_props_frame, textvariable=self.sub_cp_max_var, width=10).grid(row=2, column=6, padx=2)
        
        # Layer Properties Section
        layer_props_frame = ttk.LabelFrame(layer_frame, text="Layer Properties", padding=10)
        layer_props_frame.pack(fill='x', padx=5, pady=5)
        
        layer_props_inner_frame = ttk.Frame(layer_props_frame)
        layer_props_inner_frame.pack(fill='x', pady=5)
        
        # Layer thermal conductivity kz
        ttk.Label(layer_props_inner_frame, text="Layer kz (W/cmK):").grid(row=0, column=0, sticky='w')
        self.layer_kz_var = tk.StringVar()
        ttk.Entry(layer_props_inner_frame, textvariable=self.layer_kz_var, width=15).grid(row=0, column=1, padx=2)
        self.layer_kz_is_fitting = tk.BooleanVar()
        def layer_kz_fit_callback(*args):
            if self.layer_kz_is_fitting.get():
                try:
                    val = float(self.layer_kz_var.get())
                    self.layer_kz_min_var.set(str(val * 0.9))
                    self.layer_kz_max_var.set(str(val * 1.1))
                except Exception:
                    pass
        self.layer_kz_is_fitting.trace_add('write', layer_kz_fit_callback)
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
        def layer_kxx_fit_callback(*args):
            if self.layer_kxx_is_fitting.get():
                try:
                    val = float(self.layer_kxx_var.get())
                    self.layer_kxx_min_var.set(str(val * 0.9))
                    self.layer_kxx_max_var.set(str(val * 1.1))
                except Exception:
                    pass
        self.layer_kxx_is_fitting.trace_add('write', layer_kxx_fit_callback)
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
        def layer_cp_fit_callback(*args):
            if self.layer_cp_is_fitting.get():
                try:
                    val = float(self.layer_cp_var.get())
                    self.layer_cp_min_var.set(str(val * 0.9))
                    self.layer_cp_max_var.set(str(val * 1.1))
                except Exception:
                    pass
        self.layer_cp_is_fitting.trace_add('write', layer_cp_fit_callback)
        ttk.Checkbutton(layer_props_inner_frame, text="Fit", variable=self.layer_cp_is_fitting).grid(row=2, column=2, padx=2)
        
        ttk.Label(layer_props_inner_frame, text="Min:").grid(row=2, column=3, sticky='w', padx=(10,2))
        self.layer_cp_min_var = tk.StringVar()
        ttk.Entry(layer_props_inner_frame, textvariable=self.layer_cp_min_var, width=10).grid(row=2, column=4, padx=2)
        
        ttk.Label(layer_props_inner_frame, text="Max:").grid(row=2, column=5, sticky='w', padx=(5,2))
        self.layer_cp_max_var = tk.StringVar()
        ttk.Entry(layer_props_inner_frame, textvariable=self.layer_cp_max_var, width=10).grid(row=2, column=6, padx=2)
        
        # Add as Top Layer checkbox
        self.add_top_layer_var = tk.BooleanVar()
        ttk.Checkbutton(layer_input_frame, text="Add as Top Transparent Layer", variable=self.add_top_layer_var).grid(row=3, column=2, padx=10)
        
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
        def pump_radius_fit_callback(*args):
            if self.pump_radius_is_fitting.get():
                try:
                    val = float(eval(self.pump_radius_var.get()))
                    self.pump_radius_min_var.set(str(val * 0.9))
                    self.pump_radius_max_var.set(str(val * 1.1))
                except Exception:
                    pass
        self.pump_radius_is_fitting.trace_add('write', pump_radius_fit_callback)
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
        def probe_radius_fit_callback(*args):
            if self.probe_radius_is_fitting.get():
                try:
                    val = float(eval(self.probe_radius_var.get()))
                    self.probe_radius_min_var.set(str(val * 0.9))
                    self.probe_radius_max_var.set(str(val * 1.1))
                except Exception:
                    pass
        self.probe_radius_is_fitting.trace_add('write', probe_radius_fit_callback)
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
        def beam_offset_fit_callback(*args):
            if self.beam_offset_is_fitting.get():
                try:
                    val = float(eval(self.beam_offset_var.get()))
                    self.beam_offset_min_var.set(str(val * 0.9))
                    self.beam_offset_max_var.set(str(val * 1.1))
                except Exception:
                    pass
        self.beam_offset_is_fitting.trace_add('write', beam_offset_fit_callback)
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
               
        # Analysis controls (without fitting controls)
        analysis_frame = ttk.Frame(model_frame)
        analysis_frame.pack(fill='x', pady=5)
        
        ttk.Button(analysis_frame, text="Create Model", command=self.create_model).pack(side='left', padx=5)
        
        # Model status
        self.model_status_var = tk.StringVar(value="No model created")
        ttk.Label(model_frame, textvariable=self.model_status_var).pack(pady=5)
        
        # # Current Structure Display
        # structure_frame = ttk.LabelFrame(self.main_frame, text="Current Structure", padding=10)
        # structure_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # self.structure_text = tk.Text(structure_frame, height=8, width=50)
        # scrollbar = ttk.Scrollbar(structure_frame, orient="vertical", command=self.structure_text.yview)
        # self.structure_text.configure(yscrollcommand=scrollbar.set)
        
        # self.structure_text.pack(side="left", fill="both", expand=True)
        # scrollbar.pack(side="right", fill="y")
        
        # Initialize material properties with default values
        self.load_material_defaults()
        
    def setup_fitting_tab(self):
        """Setup the parameter fitting tab with multi-model support"""
        self.fitting_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.fitting_frame, text="Multi-Model Fitting")
        
        # Create main layout - single column for better organization
        main_frame = ttk.Frame(self.fitting_frame)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # All fitting parameters section - top panel
        params_frame = ttk.LabelFrame(main_frame, text="All Fitting Parameters", padding=10)
        params_frame.pack(fill='both', expand=True, pady=(0,10))
        
        # Parameters listbox with scrollbar
        params_list_frame = ttk.Frame(params_frame)
        params_list_frame.pack(fill='both', expand=True)
        
        self.params_listbox = tk.Listbox(params_list_frame, selectmode='single')
        params_scrollbar = ttk.Scrollbar(params_list_frame, orient="vertical", command=self.params_listbox.yview)
        self.params_listbox.configure(yscrollcommand=params_scrollbar.set)
        
        self.params_listbox.pack(side="left", fill="both", expand=True)
        params_scrollbar.pack(side="right", fill="y")
        
        # Parameter controls
        params_controls = ttk.Frame(params_frame)
        params_controls.pack(fill='x', pady=(5,0))
        
        ttk.Button(params_controls, text="Modify Parameter", command=self.modify_parameter).pack(side='left', padx=5)
        
        # Fitting controls section - bottom panel
        fitting_frame = ttk.LabelFrame(main_frame, text="Model-Dataset Management & Fitting", padding=10)
        fitting_frame.pack(fill='x', pady=(0,0))
        
        # Model-Dataset pairs management
        pairs_frame = ttk.LabelFrame(fitting_frame, text="Model-Dataset Pairing", padding=5)
        pairs_frame.pack(fill='x', pady=(0,10))
        
        # Selection controls for current model/dataset
        selection_frame = ttk.Frame(pairs_frame)
        selection_frame.pack(fill='x', pady=5)
        
        ttk.Label(selection_frame, text="Model:").grid(row=0, column=0, sticky='w', padx=(0,5))
        self.model_combo = ttk.Combobox(selection_frame, width=20, state='readonly')
        self.model_combo.grid(row=0, column=1, padx=5)
        
        ttk.Label(selection_frame, text="Dataset:").grid(row=0, column=2, sticky='w', padx=(10,5))
        self.dataset_combo = ttk.Combobox(selection_frame, width=20, state='readonly')
        self.dataset_combo.grid(row=0, column=3, padx=5)
        
        # Management buttons for selected model/dataset
        mgmt_buttons_frame = ttk.Frame(pairs_frame)
        mgmt_buttons_frame.pack(fill='x', pady=5)
        
        ttk.Button(mgmt_buttons_frame, text="Load Dataset", command=self.load_dataset).pack(side='left', padx=(0,5))
        ttk.Button(mgmt_buttons_frame, text="Delete Model", command=self.delete_selected_model).pack(side='left', padx=5)
        ttk.Button(mgmt_buttons_frame, text="Delete Dataset", command=self.delete_selected_dataset).pack(side='left', padx=5)
        ttk.Button(mgmt_buttons_frame, text="View Model Info", command=self.view_selected_model_info).pack(side='left', padx=5)
        ttk.Button(mgmt_buttons_frame, text="View Dataset Info", command=self.view_selected_dataset_info).pack(side='left', padx=5)
        
        # Current pairs listbox
        pairs_list_frame = ttk.Frame(pairs_frame)
        pairs_list_frame.pack(fill='x', pady=5)
        
        ttk.Label(pairs_list_frame, text="Current Model-Dataset Pairs:").pack(anchor='w')
        self.pairs_listbox = tk.Listbox(pairs_list_frame, height=4)
        self.pairs_listbox.pack(fill='x', pady=2)
        
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
        self.fitting_method_var = tk.StringVar(value="leastsq")
        method_combo = ttk.Combobox(fitting_controls_frame, textvariable=self.fitting_method_var,
                                  values=["nelder", "differential_evolution", "leastsq"], width=20)
        method_combo.pack(side='left', padx=(5,10))
        
        ttk.Button(fitting_controls_frame, text="Start Multi-Model Fitting", command=self.start_multimodel_fitting).pack(side='left', padx=5)
        
        # Fitting status
        self.fitting_status_var = tk.StringVar(value="Ready for fitting")
        ttk.Label(fitting_frame, textvariable=self.fitting_status_var).pack(pady=5)
        
        # Initialize model-dataset pairs list
        self.model_dataset_pairs = []

    def setup_sensitivity_tab(self):

        """Setup the model analysis tab"""
        self.sensitivity_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.sensitivity_frame, text="Model Analysis")
        
        # Main layout
        main_frame = ttk.Frame(self.sensitivity_frame)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Model selection
        model_frame = ttk.LabelFrame(main_frame, text="Select Model", padding=10)
        model_frame.pack(fill='x', pady=(0,10))
        
        ttk.Label(model_frame, text="Model:").pack(side='left')
        self.sens_model_combo = ttk.Combobox(model_frame, width=30, state='readonly')
        self.sens_model_combo.pack(side='left', padx=5)

        # Add button to plot phase in specified frequency range
        plot_phase_btn = ttk.Button(model_frame, text="Plot Phase in Frequency Range", command=self.plot_phase_in_freq_range)
        plot_phase_btn.pack(side='left', padx=10)



        # Frequency range
        freq_frame = ttk.Frame(self.sensitivity_frame)
        freq_frame.pack(fill='x', pady=5)
        
        ttk.Label(freq_frame, text="Freq Start (Hz):").grid(row=0, column=0, sticky='w')
        self.freq_start_var = tk.StringVar(value="1e3")
        ttk.Entry(freq_frame, textvariable=self.freq_start_var, width=15).grid(row=0, column=1, padx=5)
        
        ttk.Label(freq_frame, text="Freq End (Hz):").grid(row=0, column=2, sticky='w', padx=(10,0))
        self.freq_end_var = tk.StringVar(value="40e6")
        ttk.Entry(freq_frame, textvariable=self.freq_end_var, width=15).grid(row=0, column=3, padx=5)
        
        ttk.Label(freq_frame, text="Points:").grid(row=1, column=0, sticky='w')
        self.freq_step_var = tk.StringVar(value="200")
        ttk.Entry(freq_frame, textvariable=self.freq_step_var, width=15).grid(row=1, column=1, padx=5)
 

        # Bind model combobox selection to update parameter list
        self.sens_model_combo.bind('<<ComboboxSelected>>', self.on_sens_model_selected)
        
        # Parameter selection
        param_frame = ttk.LabelFrame(main_frame, text="Select Parameter", padding=10)
        param_frame.pack(fill='both', expand=True, pady=(0,10))
        
        self.sens_param_listbox = tk.Listbox(param_frame, height=8, selectmode='multiple')
        self.sens_param_listbox.pack(side='left', fill='both', expand=True)
        
        param_scrollbar = ttk.Scrollbar(param_frame, orient="vertical", command=self.sens_param_listbox.yview)
        self.sens_param_listbox.configure(yscrollcommand=param_scrollbar.set)
        param_scrollbar.pack(side='right', fill='y')
        
        # Sensitivity analysis controls
        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(fill='x', pady=5)
        
        ttk.Button(controls_frame, text="Run Sensitivity Analysis", command=self.run_sensitivity_analysis).pack(side='left', padx=5)
        
        # Sensitivity analysis status
        self.sens_status_var = tk.StringVar(value="Select a model and parameter to analyze")
        ttk.Label(main_frame, textvariable=self.sens_status_var).pack(pady=5)

    def plot_phase_in_freq_range(self):
        """Plot phase vs frequency for selected model in specified range"""
        model_name = self.sens_model_combo.get()
        if not model_name or model_name not in self.models:
            messagebox.showerror("Error", "Please select a valid model to plot.")
            return
        try:
            freq_start = float(eval(self.freq_start_var.get()))
            freq_end = float(eval(self.freq_end_var.get()))
            points = int(float(eval(self.freq_step_var.get())))
            freqs = np.logspace(np.log10(freq_start), np.log10(freq_end), points)
            model = self.models[model_name]
            phases = [model.get_phase(f) for f in freqs]
            # Show plot in a new window
            plot_window = tk.Toplevel(self.root)
            plot_window.title(f"Phase vs Frequency - {model_name}")
            plot_window.geometry("900x700")
            fig = Figure(figsize=(10, 7), dpi=100)
            ax = fig.add_subplot(111)
            ax.semilogx(freqs, phases, 'b-', label='Phase')
            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('Phase (rad)')
            ax.set_title(f'Phase vs Frequency - {model_name}')
            ax.grid(True)
            ax.legend()
            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, plot_window)
            canvas.draw()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        except Exception as e:
            messagebox.showerror("Error", f"Error plotting phase: {str(e)}")

    def on_sens_model_selected(self, event):
        """Update parameter listbox when a model is selected in sensitivity tab"""
        model_name = self.sens_model_combo.get()
        self.sens_param_listbox.delete(0, tk.END)
        if model_name and model_name in self.models:
            model = self.models[model_name]
            if hasattr(model, 'fitting_params') and hasattr(model.fitting_params, 'parameters'):
                for param in model.fitting_params.parameters:
                    self.sens_param_listbox.insert(tk.END, param.name)

    def run_sensitivity_analysis(self):
        """Run sensitivity analysis on selected model and parameter"""
        model_name = self.sens_model_combo.get()
        param_name = self.sens_param_listbox.get(tk.ACTIVE)
        import matplotlib.pyplot as plt
        selected_indices = self.sens_param_listbox.curselection()
        if not model_name or not selected_indices:
            messagebox.showerror("Error", "Please select both a model and at least one parameter for sensitivity analysis.")
            return
        model = self.models.get(model_name, None)
        if model is None:
            messagebox.showerror("Error", f"Model '{model_name}' not found.")
            return
        param_names = [self.sens_param_listbox.get(i) for i in selected_indices]
        try:
            # Perform sensitivity analysis for all selected parameters
            sensitivities_dict = {}
            for param_name in param_names:
                sensitivities = model.sensitivity_analysis(param_name,freq_range=(float(eval(self.freq_start_var.get())),
                                                                           float(eval(self.freq_end_var.get()))),steps=int(eval(self.freq_step_var.get())))
                sensitivities_dict[param_name] = sensitivities
            # Display results in a new window with all curves
            result_window = tk.Toplevel(self.root)
            result_window.title(f"Sensitivity Analysis - {model_name}")
            result_window.geometry("900x700")
            # Only show curves in the result window
            fig = Figure(figsize=(10, 7), dpi=100)
            ax = fig.add_subplot(111)
            import matplotlib.pyplot as plt
            colors = plt.cm.tab10.colors
            for idx, (param_name, sensitivities) in enumerate(sensitivities_dict.items()):
                freqs = sensitivities[0]
                sens_vals = sensitivities[1]
                ax.semilogx(freqs, sens_vals, label=param_name, color=colors[idx % len(colors)])
            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('Sensitivity')
            ax.set_title(f'Sensitivity Analysis - {model_name}')
            ax.grid(True)
            ax.legend()
            fig.tight_layout()
            canvas = FigureCanvasTkAgg(fig, result_window)
            canvas.draw()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        except Exception as e:
            messagebox.showerror("Error", f"Error during sensitivity analysis: {str(e)}")

    def add_substrate(self):
        
        """Create a new domain with specified temperature"""
        try:
            temperature = float(self.temp_var.get())
            self.domain = Domain(temperature)
            #self.update_structure_display()

        except ValueError:
            messagebox.showerror("Error", "Invalid temperature value")
        except Exception as e:
            messagebox.showerror("Error", f"Error creating domain: {str(e)}")
        
        """Add substrate to the domain"""
        if self.domain is None:
            messagebox.showerror("Error", "Please create a domain first")
            return
            
        try:
            material_name = self.substrate_var.get()
            material_class = self.materials[material_name]
            self.domain.add_substrate(material_class)

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
                    # Only add if parameter does not exist yet
                    if not hasattr(self.fitting_params, 'param_names') or param_name not in self.fitting_params.param_names:
                        self.fitting_params.add(param_name, kz_value, min_val, max_val)
                    # Apply to substrate (index 0 in heat_path)
                    if len(self.domain.heat_path) > 0:
                        self.domain.set_layer_param(0, kzz=self.fitting_params.get_parameter(param_name))
            
            if self.sub_kxx_is_fitting.get() and self.sub_kxx_var.get():
                kxx_value = float(eval(self.sub_kxx_var.get()))
                default_name = "sub_kxx"
                param_name = simpledialog.askstring("Parameter Name", 
                                                   f"Enter name for substrate kxx parameter:", 
                                                   initialvalue=default_name)
                if param_name:
                    min_val = float(eval(self.sub_kxx_min_var.get())) if self.sub_kxx_min_var.get() else None
                    max_val = float(eval(self.sub_kxx_max_var.get())) if self.sub_kxx_max_var.get() else None
                    if not hasattr(self.fitting_params, 'param_names') or param_name not in self.fitting_params.param_names:
                        self.fitting_params.add(param_name, kxx_value, min_val, max_val)
                    if len(self.domain.heat_path) > 0:
                        self.domain.set_layer_param(0, kxx=self.fitting_params.get_parameter(param_name))
            
            if self.sub_cp_is_fitting.get() and self.sub_cp_var.get():
                cp_value = float(eval(self.sub_cp_var.get()))
                default_name = "sub_cp"
                param_name = simpledialog.askstring("Parameter Name", 
                                                   f"Enter name for substrate cp parameter:", 
                                                   initialvalue=default_name)
                if param_name:
                    min_val = float(eval(self.sub_cp_min_var.get())) if self.sub_cp_min_var.get() else None
                    max_val = float(eval(self.sub_cp_max_var.get())) if self.sub_cp_max_var.get() else None
                    if not hasattr(self.fitting_params, 'param_names') or param_name not in self.fitting_params.param_names:
                        self.fitting_params.add(param_name, cp_value, min_val, max_val)
                    if len(self.domain.heat_path) > 0:
                        self.domain.set_layer_param(0, cp=self.fitting_params.get_parameter(param_name))
            
            
            #self.update_structure_display()
            self.sub_cp_is_fitting.set(False)
            self.sub_kz_is_fitting.set(False)
            self.sub_kxx_is_fitting.set(False)
            #messagebox.showinfo("Success", f"Added {material_name} substrate")
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
            # Check if adding as top layer
            if self.add_top_layer_var.get():
                self.top_layer_num += 1
                # Use domain.add_toplayer and set_top_interface_condu
                self.domain.add_toplayer(thickness, material_class)
                self.domain.set_top_interface_condu(self.top_layer_num, conductance)
            else:
                # Add the layer (this automatically creates an interface)
                self.domain.add_layer(thickness, material_class)
                # Get the interface number (number of layers added so far)
                layer_num = len(self.domain.heat_path) // 2  # Each layer addition adds 2 entries (layer + interface)
                # Set the interface conductance for the newly created interface
                self.domain.set_interface_condu(layer_num, conductance)


            # Initialize fitting parameters if needed
            if self.fitting_params is None:
                self.fitting_params = Fitting_parameters()
            
            # Add fitting parameters if checkboxes are checked
            
            if self.thickness_is_fitting.get():
                # Get custom parameter name or use default
                default_name = f"thick_{layer_num}"
                param_name = simpledialog.askstring("Parameter Name", 
                                                   f"Enter name for thickness parameter:", 
                                                   initialvalue=default_name)
                if param_name:
                    min_val = float(eval(self.thickness_min_var.get())) if self.thickness_min_var.get() else None
                    max_val = float(eval(self.thickness_max_var.get())) if self.thickness_max_var.get() else None
                    if not hasattr(self.fitting_params, 'param_names') or param_name not in self.fitting_params.param_names:
                        self.fitting_params.add(param_name, thickness, min_val, max_val)
                    # Set layer parameter to use fitting parameter (correct index)
                    self.domain.set_layer_param(layer_num, thickness=self.fitting_params.get_parameter(param_name))
            
            if self.interface_is_fitting.get():
                # Get custom parameter name or use default
                default_name = f"interface_{layer_num}"
                param_name = simpledialog.askstring("Parameter Name", 
                                                   f"Enter name for interface conductance parameter:", 
                                                   initialvalue=default_name)
                if param_name:
                    min_val = float(eval(self.interface_min_var.get())) if self.interface_min_var.get() else None
                    max_val = float(eval(self.interface_max_var.get())) if self.interface_max_var.get() else None
                    if not hasattr(self.fitting_params, 'param_names') or param_name not in self.fitting_params.param_names:
                        self.fitting_params.add(param_name, conductance, min_val, max_val)
                    # Set interface conductance to use fitting parameter
                    self.domain.set_interface_condu(layer_num, self.fitting_params.get_parameter(param_name))

            if self.layer_kz_is_fitting.get() and self.layer_kz_var.get():
                kz_value = float(eval(self.layer_kz_var.get()))
                default_name = "layer_kz"
                param_name = simpledialog.askstring("Parameter Name", 
                                                   f"Enter name for layer kz parameter:", 
                                                   initialvalue=default_name)
                if param_name:
                    min_val = float(eval(self.layer_kz_min_var.get())) if self.layer_kz_min_var.get() else None
                    max_val = float(eval(self.layer_kz_max_var.get())) if self.layer_kz_max_var.get() else None
                    if not hasattr(self.fitting_params, 'param_names') or param_name not in self.fitting_params.param_names:
                        self.fitting_params.add(param_name, kz_value, min_val, max_val)
                    # Apply to last layer
                    self.domain.set_layer_param(layer_num, kzz=self.fitting_params.get_parameter(param_name))
            
            if self.layer_kxx_is_fitting.get() and self.layer_kxx_var.get():
                kxx_value = float(eval(self.layer_kxx_var.get()))
                default_name = "layer_kxx"
                param_name = simpledialog.askstring("Parameter Name", 
                                                   f"Enter name for layer kxx parameter:", 
                                                   initialvalue=default_name)
                if param_name:
                    min_val = float(eval(self.layer_kxx_min_var.get())) if self.layer_kxx_min_var.get() else None
                    max_val = float(eval(self.layer_kxx_max_var.get())) if self.layer_kxx_max_var.get() else None
                    if not hasattr(self.fitting_params, 'param_names') or param_name not in self.fitting_params.param_names:
                        self.fitting_params.add(param_name, kxx_value, min_val, max_val)
                    self.domain.set_layer_param(layer_num, kxx=self.fitting_params.get_parameter(param_name))
            
            if self.layer_cp_is_fitting.get() and self.layer_cp_var.get():
                cp_value = float(eval(self.layer_cp_var.get()))
                default_name = "layer_cp"
                param_name = simpledialog.askstring("Parameter Name", 
                                                   f"Enter name for layer cp parameter:", 
                                                   initialvalue=default_name)
                if param_name:
                    min_val = float(eval(self.layer_cp_min_var.get())) if self.layer_cp_min_var.get() else None
                    max_val = float(eval(self.layer_cp_max_var.get())) if self.layer_cp_max_var.get() else None
                    if not hasattr(self.fitting_params, 'param_names') or param_name not in self.fitting_params.param_names:
                        self.fitting_params.add(param_name, cp_value, min_val, max_val)
                    self.domain.set_layer_param(layer_num, cp=self.fitting_params.get_parameter(param_name))
            
            #self.update_structure_display()
            self.update_fitting_parameters()
            #messagebox.showinfo("Success", f"Added {material_name} layer ({thickness} cm) with interface conductance {conductance} W/cm²K")
            # Clear fitting bounds for next layer
            # self.thickness_min_var.set("")
            # self.thickness_max_var.set("")
            # self.interface_min_var.set("")
            # self.interface_max_var.set("")
            self.thickness_is_fitting.set(False)
            self.interface_is_fitting.set(False)
            self.layer_kz_is_fitting.set(False)
            self.layer_kxx_is_fitting.set(False)
            self.layer_cp_is_fitting.set(False)
        except Exception as e:
            messagebox.showerror("Error", f"Error adding layer: {str(e)}")
            
    # def update_structure_display(self):
    #     """Update the structure display text"""
    #     if self.domain is None:
    #         self.structure_text.delete(1.0, tk.END)
    #         self.structure_text.insert(tk.END, "No domain created")
    #         return
            
    #     self.structure_text.delete(1.0, tk.END)
    #     self.structure_text.insert(tk.END, f"Domain Temperature: {self.domain.temperature}K\n\n")
        
    #     if hasattr(self.domain, 'heat_path') and self.domain.heat_path:
    #         self.structure_text.insert(tk.END, "Heat Path Structure:\n")
    #         for i, layer in enumerate(self.domain.heat_path):
    #             if hasattr(layer, 'thickness'):
    #                 material_name = getattr(layer.material, 'materialname', 'Unknown')
    #                 self.structure_text.insert(tk.END, f"Layer {i//2}: {material_name} ({layer.thickness} cm)\n")
    #             else:
    #                 self.structure_text.insert(tk.END, f"Interface {i//2}: Conductance = {getattr(layer, 'tbc', 'Not set')}\n")
                    
    def create_model(self):
        """Create the FDTR model with fitting parameters"""
        if self.domain is None:
            messagebox.showerror("Error", "Please create a domain first")
            return
            
        try:
            # Initialize fitting parameters if needed
            if self.fitting_params is None:
                self.fitting_params = Fitting_parameters()
           
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
                    if not hasattr(self.fitting_params, 'param_names') or param_name not in self.fitting_params.param_names:
                        self.fitting_params.add(param_name, pump_radius, min_val, max_val)
                    pump_radius = self.fitting_params.get_parameter(param_name)
            
            if self.probe_radius_is_fitting.get():
                default_name = "probe_radius"
                param_name = simpledialog.askstring("Parameter Name", 
                                                   f"Enter name for probe radius parameter:", 
                                                   initialvalue=default_name)
                if param_name:
                    min_val = float(eval(self.probe_radius_min_var.get())) if self.probe_radius_min_var.get() else None
                    max_val = float(eval(self.probe_radius_max_var.get())) if self.probe_radius_max_var.get() else None
                    if not hasattr(self.fitting_params, 'param_names') or param_name not in self.fitting_params.param_names:
                        self.fitting_params.add(param_name, probe_radius, min_val, max_val)
                    probe_radius = self.fitting_params.get_parameter(param_name)
            
            if self.beam_offset_is_fitting.get():
                default_name = "beam_offset"
                param_name = simpledialog.askstring("Parameter Name", 
                                                   f"Enter name for beam offset parameter:", 
                                                   initialvalue=default_name)
                if param_name:
                    min_val = float(eval(self.beam_offset_min_var.get())) if self.beam_offset_min_var.get() else None
                    max_val = float(eval(self.beam_offset_max_var.get())) if self.beam_offset_max_var.get() else None
                    if not hasattr(self.fitting_params, 'param_names') or param_name not in self.fitting_params.param_names:
                        self.fitting_params.add(param_name, beam_offset, min_val, max_val)
                    beam_offset = self.fitting_params.get_parameter(param_name)
            
            backend = self.backend_var.get()
            
            self.model = FourierModelFDTR(self.domain, pump_radius, probe_radius, beam_offset, 
                                        fitting_params=self.fitting_params, backend=backend)
            
            # Get model name from combobox (editable)
            model_name = self.model_name_var.get().strip()
            if not model_name:
                model_name = f"Model_{self.model_counter}"
                self.model_name_var.set(model_name)
            self.models[model_name] = self.model
            if model_name not in self.model_name_combo['values']:
                self.model_name_combo['values'] = list(self.models.keys())
            self.model_counter += 1
            self.model_status_var.set(f"Model '{model_name}' created with {backend} backend")
            messagebox.showinfo("Success", f"FDTR model '{model_name}' created successfully")
            self.update_combo_boxes()
            self.update_fitting_parameters()
            self.domain = None  # Reset domain to force new creation for next model
            self.fitting_params = None  # Reset fitting parameters for next model
            self.model_name_combo.set('')
        except Exception as e:
            messagebox.showerror("Error", f"Error creating model: {str(e)}")
            self.model = None
            return
    
    def on_model_name_selected(self, event):
        """Load parameters when an existing model is selected in the combobox"""
        model_name = self.model_name_var.get()
        if model_name in self.models:
            model = self.models[model_name]
            # Load beam parameters if available
            if hasattr(model, 'pump_radius'):
                self.pump_radius_var.set(str(model.pump_radius))
            if hasattr(model, 'probe_radius'):
                self.probe_radius_var.set(str(model.probe_radius))
            if hasattr(model, 'beam_offset'):
                self.beam_offset_var.set(str(model.beam_offset))
            if hasattr(model, 'backend'):
                self.backend_var.set(str(model.backend))

    # def update_model_parameters(self):
    #     """Update the parameters of the currently selected model with modified values"""
    #     model_name = self.model_name_var.get()
    #     if model_name not in self.models:
    #         messagebox.showerror("Error", "No model selected to update.")
    #         return
    #     try:
    #         model = self.models[model_name]
    #         # Update domain if changed
    #         if self.domain is not None:
    #             model.domain = self.domain
    #         # Update fitting parameters if changed
    #         if self.fitting_params is not None:
    #             model.fitting_params = self.fitting_params
    #         # Update beam parameters
    #         model.pump_radius = float(eval(self.pump_radius_var.get()))
    #         model.probe_radius = float(eval(self.probe_radius_var.get()))
    #         model.beam_offset = float(eval(self.beam_offset_var.get()))
    #         model.backend = self.backend_var.get()
    #         messagebox.showinfo("Success", f"Model '{model_name}' parameters updated.")
    #         # Update fitting info display
    #         self.update_model_list()
    #         self.update_fitting_parameters()
    #         self.domain = None  # Reset domain to force new creation for next model
    #         self.fitting_params = None  # Reset fitting parameters for next model
    #         self.update_structure_display()
    #         self.pump_radius_is_fitting.set(False)
    #         self.probe_radius_is_fitting.set(False)
    #         self.beam_offset_is_fitting.set(False)
    #     except Exception as e:
    #         messagebox.showerror("Error", f"Error updating model parameters: {str(e)}")

    def update_fitting_parameters(self):
        """Update the fitting parameters display"""
        self.params_listbox.delete(0, tk.END)
        # Collect all fitting parameters from all models
        param_models = {}
        for model_name, model in self.models.items():
            if hasattr(model, 'fitting_params') and hasattr(model.fitting_params, 'parameters'):
                for param in model.fitting_params.parameters:
                    if param.name not in param_models:
                        param_models[param.name] = {'param': param, 'models': []}
                    param_models[param.name]['models'].append(model_name)
        if param_models:
            self.params_listbox.delete(0, tk.END)
            for name, info in param_models.items():
                param = info['param']
                models = ", ".join(info['models'])
                self.params_listbox.insert(
                    tk.END,
                    f"{name} = {getattr(param, 'value', param)} [{getattr(param, 'min', 'None')}, {getattr(param, 'max', 'None')}] | Models: {models}"
                )
        else:
            self.params_listbox.delete(0, tk.END)
            self.params_listbox.insert(tk.END, "No fitting parameters found in any model")
            
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
                   color='red', label='Experimental', alpha=0.7, s=20)
        
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
                self.layer_cp_var.set(str(temp_material.cp))
                    
        except Exception as e:
            print(f"Note: Could not load all layer properties for {material_name}: {str(e)}")
            
    def load_material_defaults(self):
        """Load default material properties for both substrate and layer"""
        self.load_substrate_defaults()
        self.load_layer_defaults()
            
    def update_model_list(self):
        """Update the model list display and combo boxes"""
        self.update_combo_boxes()
    
    def update_dataset_list(self):
        """Update the dataset list display and combo boxes"""
        self.update_combo_boxes()
    

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
    
    # Old methods that used deleted listboxes have been removed and replaced with combobox-based methods
    
    def delete_selected_model(self):
        """Delete the currently selected model in the combobox"""
        model_name = self.model_combo.get()
        if not model_name:
            messagebox.showwarning("Warning", "No model selected")
            return
            
        if model_name not in self.models:
            messagebox.showerror("Error", f"Model '{model_name}' not found")
            return
            
        if messagebox.askyesno("Confirm", f"Delete model '{model_name}'?"):
            del self.models[model_name]
            # Remove any pairs containing this model
            self.model_dataset_pairs = [(m, d) for m, d in self.model_dataset_pairs if m != model_name]
            self.update_model_list()
            self.update_pairs_display()
            messagebox.showinfo("Success", f"Model '{model_name}' deleted")
    
    def delete_selected_dataset(self):
        """Delete the currently selected dataset in the combobox"""
        dataset_name = self.dataset_combo.get()
        if not dataset_name:
            messagebox.showwarning("Warning", "No dataset selected")
            return
            
        if dataset_name not in self.datasets:
            messagebox.showerror("Error", f"Dataset '{dataset_name}' not found")
            return
            
        if messagebox.askyesno("Confirm", f"Delete dataset '{dataset_name}'?"):
            del self.datasets[dataset_name]
            # Remove any pairs containing this dataset
            self.model_dataset_pairs = [(m, d) for m, d in self.model_dataset_pairs if d != dataset_name]
            self.update_dataset_list()
            self.update_pairs_display()
            messagebox.showinfo("Success", f"Dataset '{dataset_name}' deleted")
    
    def view_selected_model_info(self):
        """View information about the currently selected model in the combobox"""
        model_name = self.model_combo.get()
        if not model_name:
            messagebox.showwarning("Warning", "No model selected")
            return
            
        if model_name not in self.models:
            messagebox.showerror("Error", f"Model '{model_name}' not found")
            return
        
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
        info_text.insert(tk.END, f"Backend: {getattr(model, 'backend', 'Unknown')}\n")

        info_text.insert(tk.END, f"Added Layers (last is top reflective layer):\n")
        for layer in model.domain.heat_path:
            
            if hasattr(layer, 'thickness'):
                material_name = getattr(layer.material, 'materialname', 'Unknown')
                info_text.insert(tk.END, f"Layer: {material_name}, Thickness: {layer.thickness} cm\n")
                info_text.insert(tk.END, f"  kzz: {getattr(layer, 'kzz', 'Not set')} W/cmK, kxx: {getattr(layer, 'kxx', 'Not set')} W/cmK, cp: {getattr(layer, 'cp', 'Not set')} J/cm³K\n")
            else:
                info_text.insert(tk.END, f"Interface: Conductance = {getattr(layer, 'g', 'Not set')} W/cm²K\n")
            info_text.insert(tk.END, f"----------------\n")

        info_text.insert(tk.END, f"Transparent top Layers:\n")
        for layer in model.domain.top_heat_path:
            if hasattr(layer, 'thickness'):
                material_name = getattr(layer.material, 'materialname', 'Unknown')
                info_text.insert(tk.END, f"Layer: {material_name}, Thickness: {layer.thickness} cm\n")
                info_text.insert(tk.END, f"  kzz: {getattr(layer, 'kzz', 'Not set')} W/cmK, kxx: {getattr(layer, 'kxx', 'Not set')} W/cmK, cp: {getattr(layer, 'cp', 'Not set')} J/cm³K\n")
            else:
                info_text.insert(tk.END, f"Interface: Conductance = {getattr(layer, 'g', 'Not set')} W/cm²K\n")
        
            info_text.insert(tk.END, f"----------------\n")
            
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
    
    def view_selected_dataset_info(self):
        """View information about the currently selected dataset in the combobox"""
        dataset_name = self.dataset_combo.get()
        if not dataset_name:
            messagebox.showwarning("Warning", "No dataset selected")
            return
            
        if dataset_name not in self.datasets:
            messagebox.showerror("Error", f"Dataset '{dataset_name}' not found")
            return
        
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
    
    def modify_parameter(self):
        """Modify parameter bounds or value"""
        selected = self.params_listbox.curselection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a parameter to modify")
            return
        
        param_display = self.params_listbox.get(selected[0])
        
        if param_display == "No fitting parameters found in any model":
            messagebox.showinfo("Parameter Modification", "No fitting parameters available to modify")
            return
        
        # Parse the parameter name from the display string
        try:
            param_name = param_display.split(' = ')[0]
            
            # Collect all models that use this parameter
            models_with_param = []
            for model_name, model in self.models.items():
                if hasattr(model, 'fitting_params') and model.fitting_params:
                    for param in model.fitting_params.parameters:
                        if param.name == param_name:
                            models_with_param.append((model_name, model))

            if not models_with_param:
                messagebox.showinfo("Parameter Modification", f"No models found using parameter '{param_name}'")
                return

            # Get current values from the first model
            param_obj = models_with_param[0][1].fitting_params.get_value(param_name)
            current_value = getattr(param_obj, 'value', param_obj)
            current_min = getattr(param_obj, 'min', '')
            current_max = getattr(param_obj, 'max', '')

            # Dialog to edit values
            edit_window = tk.Toplevel(self.root)
            edit_window.title(f"Edit Parameter: {param_name}")
            edit_window.geometry("350x220")
            ttk.Label(edit_window, text=f"Edit '{param_name}' for all models:").pack(pady=8)

            frame = ttk.Frame(edit_window)
            frame.pack(pady=5, padx=10, fill='x')

            ttk.Label(frame, text="Default Value:").grid(row=0, column=0, sticky='w')
            value_var = tk.StringVar(value=str(current_value))
            ttk.Entry(frame, textvariable=value_var, width=18).grid(row=0, column=1, padx=5)

            ttk.Label(frame, text="Lower Bound:").grid(row=1, column=0, sticky='w')
            min_var = tk.StringVar(value=str(current_min))
            ttk.Entry(frame, textvariable=min_var, width=18).grid(row=1, column=1, padx=5)

            ttk.Label(frame, text="Upper Bound:").grid(row=2, column=0, sticky='w')
            max_var = tk.StringVar(value=str(current_max))
            ttk.Entry(frame, textvariable=max_var, width=18).grid(row=2, column=1, padx=5)

            def apply_changes():
                try:
                    new_value = float(eval(value_var.get()))
                except Exception:
                    messagebox.showerror("Error", "Invalid default value")
                    return
                try:
                    new_min = float(eval(min_var.get())) if min_var.get() else None
                except Exception:
                    messagebox.showerror("Error", "Invalid lower bound")
                    return
                try:
                    new_max = float(eval(max_var.get())) if max_var.get() else None
                except Exception:
                    messagebox.showerror("Error", "Invalid upper bound")
                    return

                # Update parameter in all models
                for model_name, model in models_with_param:
                    for param in model.fitting_params.parameters:
                        if param.name == param_name:
                            if hasattr(param, 'value'):
                                param.value = new_value
                            if hasattr(param, 'min'):
                                param.min = new_min
                            if hasattr(param, 'max'):
                                param.max = new_max
                self.update_fitting_parameters()
                messagebox.showinfo("Success", f"Parameter '{param_name}' updated for all models")
                edit_window.destroy()

            ttk.Button(edit_window, text="Apply", command=apply_changes).pack(pady=12)
            ttk.Button(edit_window, text="Cancel", command=edit_window.destroy).pack()
            self.update_fitting_parameters()
        except Exception as e:
            messagebox.showerror("Error", f"Error parsing parameter name: {str(e)}")
    
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
                


            # Perform fitting                # Prepare models and datasets for multimodel fitting
            multimodels = []
            multidatasets = []
            for mname, dname in self.model_dataset_pairs:
                multimodels.append(self.models[mname])
                multidatasets.append(self.datasets[dname])
            result = multimodel_fitting(multimodels, multidatasets, method=method)
            # Store the result for all pairs
            for mname, dname in self.model_dataset_pairs:
                results[f"{mname}_{dname}"] = result
                break
            
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
            # results_text.insert(tk.END, f"{'='*50}\n")
            # results_text.insert(tk.END, f"Results for {result_name}\n")
            # results_text.insert(tk.END, f"{'='*50}\n")
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
        
        # Plot all model-dataset pairs in the same plot, one color per pair
        ax = fig.add_subplot(111)
        colors = itertools.cycle(plt.cm.tab10.colors)
        for model_name, dataset_name in zip(model_names, dataset_names):
            color = next(colors)
            model = self.models[model_name]
            data = self.datasets[dataset_name]
            # Plot experimental data
            ax.scatter(data[:, 0], data[:, 1], color=color, label=f'Exp: {dataset_name}', alpha=0.7, s=20, marker='o')
            # Plot fitted curve
            phases_fitted = [model.get_phase(f) for f in data[:, 0]]
            ax.semilogx(data[:, 0], phases_fitted, color=color, label=f'Fitted: {model_name}', linewidth=2)
        ax.set_xlabel('Frequency (Hz)')
        ax.set_ylabel('Phase (rad)')
        ax.set_title('Multi-Model Fitting Results')
        ax.grid(True)
        ax.legend()
        
        fig.tight_layout()
        canvas.draw()

    def update_combo_boxes(self):
        """Update the model and dataset combo boxes"""
        # Update model combo box
        model_names = list(self.models.keys())
        self.model_combo['values'] = model_names
        self.sens_model_combo['values'] = model_names
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
