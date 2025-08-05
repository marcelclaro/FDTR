#!/usr/bin/env python3
"""
FDTR GUI Launcher Script

This script checks dependencies and launches the FDTR GUI interface.
"""

import sys
import subprocess
import importlib

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'numpy', 'matplotlib', 'scipy', 'sympy', 'mpmath', 'lmfit', 'numba'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} (missing)")
            missing_packages.append(package)
    
    return missing_packages

def install_packages(packages):
    """Install missing packages"""
    if not packages:
        return True
    
    print(f"\nMissing packages: {', '.join(packages)}")
    response = input("Do you want to install them? (y/n): ")
    
    if response.lower() in ['y', 'yes']:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + packages)
            print("✓ Packages installed successfully!")
            return True
        except subprocess.CalledProcessError:
            print("✗ Failed to install packages. Please install manually:")
            print(f"pip install {' '.join(packages)}")
            return False
    return False

def check_pyfdtr():
    """Check if pyFDTR library is available"""
    try:
        from pyFDTR.domain import Domain
        from pyFDTR.materials import sapphire
        from pyFDTR.fouriermodel import FourierModelFDTR
        print("✓ pyFDTR library")
        return True
    except ImportError:
        print("✗ pyFDTR library (not found)")
        print("Make sure the pyFDTR folder is in the same directory as this script")
        return False

def launch_gui():
    """Launch the FDTR GUI"""
    try:
        import fdtr_gui
        print("\nLaunching FDTR GUI...")
        fdtr_gui.main()
    except Exception as e:
        print(f"Error launching GUI: {e}")
        return False
    return True

def main():
    """Main launcher function"""
    print("FDTR GUI Launcher")
    print("================")
    
    print("\nChecking dependencies...")
    missing = check_dependencies()
    
    if missing:
        if not install_packages(missing):
            print("\nCannot proceed without required packages.")
            sys.exit(1)
    
    print("\nChecking pyFDTR library...")
    if not check_pyfdtr():
        print("\nCannot proceed without pyFDTR library.")
        sys.exit(1)
    
    print("\n✓ All dependencies satisfied!")
    
    # Offer to run examples first
    response = input("\nDo you want to run examples first? (y/n): ")
    if response.lower() in ['y', 'yes']:
        try:
            import fdtr_examples
            fdtr_examples.main()
        except Exception as e:
            print(f"Error running examples: {e}")
    
    # Launch GUI
    response = input("\nLaunch FDTR GUI? (y/n): ")
    if response.lower() in ['y', 'yes']:
        launch_gui()
    
    print("\nGoodbye!")

if __name__ == "__main__":
    main()
