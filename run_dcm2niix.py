#!/usr/bin/env python3
"""
Standalone script to run dcm2niix on organized DICOM folders.
This script processes each folder separately to avoid dcm2niix issues.
"""

import sys
from pathlib import Path

# Import the function from process_dicom.py
sys.path.insert(0, str(Path(__file__).parent))
from process_dicom import run_dcm2niix_on_folders

if __name__ == '__main__':
    # Configuration - modify these paths
    # For Linux/WSL (mounted Windows drive):
    base_path = '/mnt/g/DIFFUSION_PG/PETIT_GROU_2019-08-02/02-AUGUST-2019/Petit_Grou_20190802_144609623'
    # For Windows native:
    # base_path = r'G:\DIFFUSION_PG\PETIT_GROU_2019-08-02\02-AUGUST-2019\Petit_Grou_20190802_144609623'
    
    # Path to dcm2niix executable
    # On Linux/Mac: usually 'dcm2niix' (if in PATH)
    # On Windows: might need full path like r'C:\path\to\dcm2niix.exe'
    dcm2niix_path = 'dcm2niix'
    
    # Enable parallel processing
    use_parallel = True
    
    print("dcm2niix Batch Converter")
    print("=" * 50)
    print(f"Base path: {base_path}")
    print(f"dcm2niix path: {dcm2niix_path}")
    print()
    
    run_dcm2niix_on_folders(base_path, dcm2niix_path=dcm2niix_path, use_parallel=use_parallel)

