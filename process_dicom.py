#!/usr/bin/env python3
"""
DICOM Info Gatherer - Python Version
This script processes DICOM files without requiring MATLAB Image Processing Toolbox.
Requires: pip install pydicom pandas
"""

import os
import sys
import re
from pathlib import Path
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import multiprocessing as mp
import subprocess
import argparse
import threading

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext
    GUI_AVAILABLE = True
    # Try to import CustomTkinter for modern UI
    # Allow disabling via environment variable to avoid segfaults
    import os
    FORCE_DISABLE_CTK = os.environ.get('DISABLE_CUSTOMTKINTER', '').lower() in ('1', 'true', 'yes')
    
    CUSTOM_TKINTER_AVAILABLE = False
    if not FORCE_DISABLE_CTK:
        try:
            import customtkinter as ctk
            # Test if CustomTkinter works by trying to set appearance mode
            # This helps catch initialization issues early
            try:
                ctk.set_appearance_mode("dark")
                CUSTOM_TKINTER_AVAILABLE = True
            except Exception:
                # CustomTkinter imported but initialization failed
                CUSTOM_TKINTER_AVAILABLE = False
                import tkinter.ttk as ttk
        except (ImportError, Exception):
            CUSTOM_TKINTER_AVAILABLE = False
            import tkinter.ttk as ttk
    else:
        import tkinter.ttk as ttk
        print("CustomTkinter disabled via DISABLE_CUSTOMTKINTER environment variable")
except ImportError:
    GUI_AVAILABLE = False
    CUSTOM_TKINTER_AVAILABLE = False

try:
    import pydicom
    from pydicom.errors import InvalidDicomError
except ImportError:
    print("ERROR: pydicom is not installed.")
    print("Please install it using: pip install pydicom pandas")
    sys.exit(1)

# Determine number of workers (use CPU count, but leave one core free)
MAX_WORKERS = max(1, mp.cpu_count() - 1)


def sanitize_folder_name(name):
    """Remove invalid characters from folder name for Windows"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    name = name.strip(' .')
    if len(name) > 200:
        name = name[:200]
    return name


def is_dicom_file(file_path):
    """Check if file is a DICOM file"""
    try:
        # Check file size
        if os.path.getsize(file_path) < 1024:
            return False
        
        # Try to read as DICOM
        pydicom.dcmread(file_path, stop_before_pixels=True)
        return True
    except (InvalidDicomError, Exception):
        return False


def find_dicom_files(directory, use_parallel=True):
    """Find all DICOM files in directory"""
    dicom_files = []
    print(f"  Scanning directory: {directory}")
    
    if not os.path.exists(directory):
        print(f"  ERROR: Directory does not exist!")
        return dicom_files
    
    all_files = list(Path(directory).iterdir())
    file_items = [f for f in all_files if f.is_file()]
    
    print(f"  Found {len(file_items)} files to check")
    
    if len(file_items) == 0:
        return dicom_files
    
    # Show sample file names
    for i, file_path in enumerate(file_items[:3], 1):
        print(f"    Sample file {i}: {file_path.name}")
    if len(file_items) > 3:
        print(f"    ... and {len(file_items) - 3} more files")
    
    # Use parallel processing for large file counts
    if use_parallel and len(file_items) > 10:
        print(f"  Using parallel processing with {MAX_WORKERS} workers...")
        file_paths = [str(f) for f in file_items]
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            results = list(executor.map(is_dicom_file, file_paths))
        
        dicom_files = [file_paths[i] for i, is_dicom in enumerate(results) if is_dicom]
        dicom_count = len(dicom_files)
    else:
        # Sequential processing
        dicom_count = 0
        for file_path in file_items:
            if is_dicom_file(str(file_path)):
                dicom_files.append(str(file_path))
                dicom_count += 1
                if dicom_count <= 3:
                    print(f"      -> DICOM file detected: {file_path.name}")
    
    print(f"  Summary: {len(file_items)} files checked, {dicom_count} DICOM files found")
    return dicom_files


def _process_single_file_for_organization(args):
    """Helper function for parallel file organization"""
    file_path, _ = args  # base_path not needed here, only for folder creation later
    try:
        ds = pydicom.dcmread(file_path, stop_before_pixels=True)
        
        # Get SeriesNumber and SeriesDescription
        series_num = str(getattr(ds, 'SeriesNumber', 'Unknown'))
        series_desc = str(getattr(ds, 'SeriesDescription', 'Unknown'))
        
        folder_name = f"{series_num}_{series_desc}"
        folder_name = sanitize_folder_name(folder_name)
        
        return (file_path, folder_name, None)
    except Exception as e:
        return (file_path, None, str(e))


def check_if_files_organized(base_path):
    """Check if DICOM files are already organized into folders"""
    base_path_obj = Path(base_path)
    
    if not base_path_obj.exists():
        return False
    
    # Get all items in base_path
    items = list(base_path_obj.iterdir())
    
    if not items:
        return False
    
    # Check if there are any DICOM files directly in base_path (only files, not subdirectories)
    file_items = [f for f in items if f.is_file()]
    dicom_files_in_root = []
    for file_path in file_items[:10]:  # Sample first 10 files for speed
        if is_dicom_file(str(file_path)):
            dicom_files_in_root.append(file_path)
    
    # Check if there are organized folders (subdirectories with DICOM files)
    organized_folders = []
    dir_items = [f for f in items if f.is_dir()]
    
    for item in dir_items:
        # Check if this folder contains DICOM files
        try:
            folder_files = [f for f in item.iterdir() if f.is_file()]
            for file_path in folder_files[:5]:  # Sample first 5 files
                if is_dicom_file(str(file_path)):
                    organized_folders.append(item)
                    break
        except PermissionError:
            # Skip folders we can't access
            continue
    
    # Decision logic:
    # 1. If there are DICOM files in root, files are NOT organized
    if dicom_files_in_root:
        return False
    
    # 2. If there are organized folders with DICOM files, files ARE organized
    if organized_folders:
        return True
    
    # 3. If no DICOM files found anywhere, return False (need to search recursively)
    return False


def organize_dicom_files(dicom_files, base_path, use_parallel=True):
    """Organize DICOM files into folders based on SeriesNumber and SeriesDescription"""
    print(f"  Organizing {len(dicom_files)} DICOM files...")
    
    if use_parallel and len(dicom_files) > 10:
        print(f"  Using parallel processing with {MAX_WORKERS} workers...")
        # Process files in parallel to get folder names
        args_list = [(file_path, base_path) for file_path in dicom_files]
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            results = list(executor.map(_process_single_file_for_organization, args_list))
        
        # Move files sequentially to avoid race conditions
        for file_path, folder_name, error in results:
            if error:
                print(f"  Warning: Error processing {file_path}: {error}")
                continue
            
            if folder_name:
                new_folder = os.path.join(base_path, folder_name)
                os.makedirs(new_folder, exist_ok=True)
                
                # Move file
                file_name = os.path.basename(file_path)
                new_file_path = os.path.join(new_folder, file_name)
                try:
                    os.rename(file_path, new_file_path)
                except Exception as e:
                    print(f"  Warning: Error moving {file_path}: {e}")
    else:
        # Sequential processing
        for file_path in dicom_files:
            try:
                ds = pydicom.dcmread(file_path, stop_before_pixels=True)
                
                # Get SeriesNumber and SeriesDescription
                series_num = str(getattr(ds, 'SeriesNumber', 'Unknown'))
                series_desc = str(getattr(ds, 'SeriesDescription', 'Unknown'))
                
                folder_name = f"{series_num}_{series_desc}"
                folder_name = sanitize_folder_name(folder_name)
                
                new_folder = os.path.join(base_path, folder_name)
                os.makedirs(new_folder, exist_ok=True)
                
                # Move file
                file_name = os.path.basename(file_path)
                new_file_path = os.path.join(new_folder, file_name)
                os.rename(file_path, new_file_path)
                
            except Exception as e:
                print(f"  Warning: Error processing {file_path}: {e}")


class DICOMCache:
    """Cache for DICOM files to avoid repeated reads"""
    def __init__(self):
        self._cache = {}
    
    def get_dicom(self, file_path):
        """Get DICOM file, use cache if available"""
        if file_path not in self._cache:
            try:
                self._cache[file_path] = pydicom.dcmread(file_path, stop_before_pixels=True)
            except:
                return None
        return self._cache.get(file_path)
    
    def clear(self):
        """Clear cache"""
        self._cache.clear()


def gather_info(dicom_files, folder_name, output_path):
    """Extract DICOM information and save to CSV"""
    if not dicom_files:
        return
    
    # Create cache for DICOM files
    cache = DICOMCache()
    
    try:
        # Read first DICOM file to get structure
        ds = cache.get_dicom(dicom_files[0])
        if ds is None:
            print(f"    Error: Could not read first DICOM file: {dicom_files[0]}")
            return
        
        # Extract information
        series_number = getattr(ds, 'SeriesNumber', None)
        series_description = getattr(ds, 'SeriesDescription', '')
        
        # Get dimensions (from first DICOM file - should be consistent across all files in a series)
        rows = getattr(ds, 'Rows', None)
        columns = getattr(ds, 'Columns', None)
        
        # CRITICAL: Check for MOSAIC format (Siemens multi-slice format)
        # MOSAIC images have multiple slices tiled into one large image
        # We need to extract the REAL acquisition matrix, not the mosaic matrix
        image_type = getattr(ds, 'ImageType', [])
        
        # Convert to list if it's a pydicom MultiValue object
        if hasattr(image_type, '__iter__') and not isinstance(image_type, str):
            image_type_list = list(image_type)
        else:
            image_type_list = [image_type] if image_type else []
        
        # Check for MOSAIC in the image type
        is_mosaic = any('MOSAIC' in str(item).upper() for item in image_type_list)
        
        if is_mosaic:
            print(f"    -> Detected MOSAIC format (Siemens multi-slice)")
            print(f"       ImageType: {image_type_list}")
            
            # Get actual acquisition matrix from DICOM tags
            acq_matrix = getattr(ds, 'AcquisitionMatrix', None)
            if acq_matrix and len(acq_matrix) >= 4:
                print(f"       AcquisitionMatrix: {list(acq_matrix)}")
                # AcquisitionMatrix format: [freq_rows, freq_cols, phase_rows, phase_cols]
                # Non-zero values indicate the actual acquisition size
                original_rows, original_cols = rows, columns
                
                if acq_matrix[0] > 0:
                    rows = acq_matrix[0]
                    columns = acq_matrix[3] if acq_matrix[3] > 0 else acq_matrix[0]
                elif acq_matrix[1] > 0:
                    rows = acq_matrix[2] if acq_matrix[2] > 0 else acq_matrix[1]
                    columns = acq_matrix[1]
                
                print(f"    -> CORRECTED dimensions from {original_rows}x{original_cols} (MOSAIC) to {rows}x{columns} (actual)")
            else:
                # Fallback: try to extract from Siemens private tags
                if (0x0051, 0x100b) in ds:  # Siemens matrix size
                    matrix_str = ds[0x0051, 0x100b].value
                    print(f"       Siemens MatrixSize tag: {matrix_str}")
                    # Format is typically like "160p*160"
                    if 'p*' in str(matrix_str):
                        try:
                            parts = str(matrix_str).replace('p', '').split('*')
                            if len(parts) == 2:
                                original_rows, original_cols = rows, columns
                                rows = int(parts[0])
                                columns = int(parts[1])
                                print(f"    -> CORRECTED dimensions from {original_rows}x{original_cols} (MOSAIC) to {rows}x{columns} (Siemens tag)")
                        except Exception as e:
                            print(f"       Warning: Could not parse Siemens matrix size: {e}")
        
        # Intelligent dimension detection: sample multiple files and use statistical method
        # CRITICAL: Skip sampling if MOSAIC was detected - MOSAIC correction is authoritative
        # If we sample after MOSAIC correction, we'll read 800x800 and overwrite the correct 160x160!
        if not is_mosaic:
            print(f"    -> Running intelligent dimension detection...")
            # INCREASED sampling: use 20% of files, at least 10, at most 100
            # More sampling = better chance of finding correct dimensions
            sample_size = max(10, min(100, len(dicom_files) // 5))
            
            # Better sampling strategy: evenly spaced indices across the entire dataset
            if sample_size >= len(dicom_files):
                # Sample all files if dataset is small
                sample_indices = list(range(len(dicom_files)))
            else:
                # Evenly spaced samples
                step = len(dicom_files) / sample_size
                sample_indices = [int(i * step) for i in range(sample_size)]
            
            dimension_counts = {}  # {(rows, cols): count}
            all_dimensions = []  # List of all valid dimensions found
            
            # DEBUG: Print sampling info
            print(f"       Sampling {len(sample_indices)} files out of {len(dicom_files)} for dimension detection")
            
            for idx in sample_indices:
                if idx >= len(dicom_files):
                    continue
                ds_check = cache.get_dicom(dicom_files[idx])
                if ds_check:
                    rows_check = getattr(ds_check, 'Rows', None)
                    cols_check = getattr(ds_check, 'Columns', None)
                    if rows_check and cols_check:
                        # Dynamic threshold: use reasonable range based on typical MRI dimensions
                        # Most MRI images are between 64-2048 pixels, but allow wider range
                        # Check if dimensions are within reasonable bounds (not hard-coded)
                        is_reasonable = (
                            rows_check >= 32 and rows_check <= 8192 and
                            cols_check >= 32 and cols_check <= 8192
                        )
                        
                        if is_reasonable:
                            dim_key = (rows_check, cols_check)
                            dimension_counts[dim_key] = dimension_counts.get(dim_key, 0) + 1
                            all_dimensions.append(dim_key)
            
            # DEBUG: Print all found dimensions
            if dimension_counts:
                print(f"       Found dimensions: {dict(dimension_counts)}")
            
            # Determine dimensions using statistical method (mode/consensus)
            if dimension_counts:
                # Find the most common dimension (mode/consensus)
                most_common_dim = max(dimension_counts.items(), key=lambda x: x[1])[0]
                most_common_count = dimension_counts[most_common_dim]
                consensus_ratio = most_common_count / len(all_dimensions) if all_dimensions else 0
                
                # ALWAYS use the most common dimension if we have any valid dimensions
                # This ensures we don't use outlier values like 800x800
                rows, columns = most_common_dim
                original_dim = (getattr(ds, 'Rows', None), getattr(ds, 'Columns', None))
                if (rows, columns) != original_dim:
                    print(f"    -> Using consensus dimensions: {rows} x {columns} (found in {most_common_count}/{len(all_dimensions)} sampled files, {consensus_ratio*100:.1f}%)")
                    print(f"    -> Rejected first file dimensions: {original_dim}")
                else:
                    print(f"    -> Using dimensions from first file: {rows} x {columns} (confirmed by sampling)")
            else:
                # No valid dimensions found in sample - check if first file is reasonable
                if rows and columns:
                    if rows < 32 or rows > 8192 or columns < 32 or columns > 8192:
                        print(f"    Warning: Dimensions {rows} x {columns} are outside typical range, but no alternatives found in sampled files")
                    else:
                        print(f"    -> Using dimensions from first file: {rows} x {columns} (no sampling data)")
                else:
                    print(f"    Warning: Could not determine dimensions from sampled files")
        else:
            # MOSAIC format detected - trust the MOSAIC correction, skip sampling
            print(f"    -> Skipping dimension sampling (MOSAIC correction is authoritative: {rows}x{columns})")
        
        # Calculate Z_Dim (number of slices per volume) correctly - OPTIMIZED: single pass with cache
        # SPECIAL CASE: For MOSAIC format, Z_Dim = NumberOfImagesInMosaic
        # Because each MOSAIC file contains multiple slices tiled into one image
        z_dim = None
        
        if is_mosaic and (0x0019, 0x100A) in ds:
            # For MOSAIC: NumberOfImagesInMosaic tells us how many slices per volume
            z_dim = ds[0x0019, 0x100A].value
            print(f"    -> MOSAIC Z_Dim from NumberOfImagesInMosaic: {z_dim} slices per volume")
        slice_positions = set()
        instance_numbers = set()
        temporal_positions = set()
        bvalue_to_files = {}  # {bvalue: set of files}
        
        # Single pass: collect all needed information at once
        sample_size = min(500, len(dicom_files))
        sample_indices = [i * len(dicom_files) // sample_size for i in range(sample_size)] if sample_size > 0 else [0]
        
        try:
            for idx in sample_indices:
                if idx >= len(dicom_files):
                    continue
                ds_sample = cache.get_dicom(dicom_files[idx])
                if ds_sample is None:
                    continue
                
                # Collect slice positions
                img_pos = getattr(ds_sample, 'ImagePositionPatient', None)
                if img_pos and len(img_pos) >= 3:
                    slice_positions.add(round(float(img_pos[2]), 2))
                
                # Collect instance numbers
                instance_num = getattr(ds_sample, 'InstanceNumber', None)
                if instance_num is not None:
                    instance_numbers.add(instance_num)
                
                # Collect temporal positions
                if (0x0020, 0x9128) in ds_sample:
                    temporal_pos = ds_sample[0x0020, 0x9128].value
                    if temporal_pos is not None:
                        temporal_positions.add(temporal_pos)
                
                # Collect b-values (for volume detection)
                bval = None
                if hasattr(ds_sample, 'DiffusionBValue'):
                    bval = getattr(ds_sample, 'DiffusionBValue', None)
                elif (0x0018, 0x9087) in ds_sample:
                    bval = ds_sample[0x0018, 0x9087].value
                elif (0x0019, 0x100c) in ds_sample:
                    bval = ds_sample[0x0019, 0x100c].value
                
                if bval is not None:
                    try:
                        bval_float = float(bval)
                        if bval_float not in bvalue_to_files:
                            bvalue_to_files[bval_float] = set()
                        bvalue_to_files[bval_float].add(dicom_files[idx])
                    except:
                        pass
            
            # Determine Z_Dim from collected data
            # BUT: For MOSAIC, Z_Dim was already set from NumberOfImagesInMosaic, don't overwrite!
            if z_dim is None:  # Only calculate if not already set (e.g., not MOSAIC)
                if len(slice_positions) > 0:
                    z_dim = len(slice_positions)
                elif len(instance_numbers) > 0 and len(instance_numbers) <= len(dicom_files):
                    z_dim = len(instance_numbers)
                else:
                    z_dim = len(dicom_files)  # Fallback (will be corrected later if volumes known)
                
        except Exception as e:
            print(f"    Warning: Error calculating Z_Dim: {e}")
            # Fallback: but don't overwrite MOSAIC z_dim!
            if z_dim is None:
                z_dim = len(dicom_files)  # Fallback
        
        # Get pixel spacing
        pixel_spacing = getattr(ds, 'PixelSpacing', None)
        x_voxel = pixel_spacing[0] if pixel_spacing and len(pixel_spacing) >= 2 else None
        y_voxel = pixel_spacing[1] if pixel_spacing and len(pixel_spacing) >= 2 else None
        z_voxel = getattr(ds, 'SliceThickness', None)
        
        # Other fields
        mr_acq_type = str(getattr(ds, 'MRAcquisitionType', ''))
        slice_gap = getattr(ds, 'SpacingBetweenSlices', None)
        
        inversion_time = getattr(ds, 'InversionTime', None)
        echo_time = getattr(ds, 'EchoTime', None)
        repetition_time = getattr(ds, 'RepetitionTime', None)
        flip_angle = getattr(ds, 'FlipAngle', None)
        
        # Multiband factor extraction (slice/through-plane acceleration)
        # IMPORTANT: Multiband (SMS) is DIFFERENT from in-plane acceleration (iPAT/GRAPPA)
        # - Multiband/SMS: simultaneously excites multiple slices (reduces TR)
        # - iPAT/GRAPPA: parallel imaging within a single slice (reduces phase encoding steps)
        multiband_factor = None
        try:
            # PRIORITY 1: Siemens CSA Header - ucMultiSliceMode (most accurate!)
            # This is the ACTUAL multiband/SMS factor used by dcm2niix
            if (0x0029, 0x1020) in ds:  # CSA Series Header Info
                try:
                    csa_data = ds[0x0029, 0x1020].value
                    if isinstance(csa_data, bytes):
                        csa_str = csa_data.decode('latin-1', errors='ignore')
                        
                        # Try ucMultiSliceMode first (most reliable for SMS/Multiband)
                        match = re.search(r'sKSpace\.ucMultiSliceMode\s*=\s*[\t]+(\d+)', csa_str)
                        if match:
                            val = int(match.group(1))
                            if val >= 1:  # ucMultiSliceMode represents the actual MB factor
                                multiband_factor = float(val)
                                if val > 1:
                                    print(f"    -> Multiband from ucMultiSliceMode: {multiband_factor}")
                        
                        # Fallback: try lMultiBandFactor (older/alternative field)
                        if multiband_factor is None:
                            match = re.search(r'sSliceAcceleration\.lMultiBandFactor\s*=\s*[\t]+(\d+)', csa_str)
                            if match:
                                val = int(match.group(1))
                                if val >= 1:
                                    multiband_factor = float(val)
                                    if val > 1:
                                        print(f"    -> Multiband from lMultiBandFactor: {multiband_factor}")
                except:
                    pass
            
            # PRIORITY 2: Standard DICOM tag for ParallelReductionFactorOutOfPlane (multiband)
            if multiband_factor is None and (0x0018, 0x9159) in ds:
                val = ds[0x0018, 0x9159].value
                if isinstance(val, (int, float)) and val >= 1:
                    multiband_factor = float(val)
            
            # PRIORITY 3: Siemens PATModeText for SLICE acceleration (multiband/SMS)
            # Format: "s2", "s3", etc. ('s' = slice acceleration)
            # NOTE: 'p' prefix is in-plane (iPAT), NOT multiband!
            if multiband_factor is None and (0x0051, 0x1011) in ds:
                pat_text = str(ds[0x0051, 0x1011].value)
                # Only extract if it starts with 's' (slice acceleration = multiband)
                if pat_text.startswith('s') and len(pat_text) > 1:
                    try:
                        val = int(pat_text[1:])
                        if val >= 1:
                            multiband_factor = float(val)
                    except:
                        pass
            
            # PRIORITY 4: GE private tag (0043,10B6) - Multiband Parameters
            if multiband_factor is None and (0x0043, 0x10B6) in ds:
                mb_params = ds[0x0043, 0x10B6].value
                if mb_params:
                    try:
                        if isinstance(mb_params, (list, tuple)) and len(mb_params) > 0:
                            val = mb_params[0]
                        else:
                            val = mb_params
                        if isinstance(val, (int, float)) and val >= 1:
                            multiband_factor = float(val)
                    except:
                        pass
        except:
            pass
        
        # In-plane acceleration factor (ParallelReductionFactorInPlane)
        inplane_accel_factor = None
        try:
            # PRIORITY 1: Siemens PATModeText (0051,1011) - most reliable for Siemens
            # Format: "p2", "p3", "p4", etc. or "s2", "s3" for slice acceleration
            if (0x0051, 0x1011) in ds:
                pat_text = str(ds[0x0051, 0x1011].value)
                # Parse "p3" -> 3, "p2" -> 2, etc.
                # 'p' prefix indicates in-plane acceleration
                if pat_text.startswith('p') and len(pat_text) > 1:
                    try:
                        val = int(pat_text[1:])
                        if 1 <= val <= 16:
                            inplane_accel_factor = float(val)
                    except:
                        pass
            
            # PRIORITY 2: Standard DICOM tag for ParallelReductionFactorInPlane
            if inplane_accel_factor is None and (0x0018, 0x9158) in ds:
                val = ds[0x0018, 0x9158].value
                # Validate: inplane acceleration factor is typically 1-8, rarely up to 16
                if isinstance(val, (int, float)) and 1 <= val <= 16:
                    inplane_accel_factor = float(val)
            
            # PRIORITY 3: Siemens private tags for iPAT/GRAPPA
            # WARNING: (0019,100A) is NumberOfImagesInMosaic for MOSAIC format, NOT iPAT!
            # Only use if NOT a MOSAIC image
            if inplane_accel_factor is None and not is_mosaic:
                if (0x0019, 0x100A) in ds:  # Siemens iPAT factor (but NOT for MOSAIC!)
                    val = ds[0x0019, 0x100A].value
                    if isinstance(val, (int, float)) and 1 <= val <= 16:
                        inplane_accel_factor = float(val)
                elif (0x0019, 0x100B) in ds:  # Alternative Siemens tag
                    val = ds[0x0019, 0x100B].value
                    if isinstance(val, (int, float)) and 1 <= val <= 16:
                        inplane_accel_factor = float(val)
            
            # PRIORITY 4: GE ASSET/ARC factor
            if inplane_accel_factor is None and (0x0043, 0x1083) in ds:
                val = ds[0x0043, 0x1083].value
                if isinstance(val, (int, float)) and 1 <= val <= 16:
                    inplane_accel_factor = float(val)
            
            # PRIORITY 5: Philips SENSE factor
            if inplane_accel_factor is None and (0x2001, 0x1008) in ds:
                val = ds[0x2001, 0x1008].value
                if isinstance(val, (int, float)) and 1 <= val <= 16:
                    inplane_accel_factor = float(val)
        except:
            pass
        
        # Additional useful fields
        # Phase encoding direction
        phase_encoding_direction = None
        try:
            if (0x0018, 0x1312) in ds:  # InPlanePhaseEncodingDirection
                phase_encoding_direction = str(ds[0x0018, 0x1312].value)
        except:
            pass
        
        # Number of averages
        number_of_averages = getattr(ds, 'NumberOfAverages', None)
        
        # Bandwidth
        bandwidth = getattr(ds, 'PixelBandwidth', None)
        
        # Coil information
        coil_name = getattr(ds, 'ReceivingCoilName', None)
        
        # Slice orientation
        slice_orientation = None
        try:
            if (0x0018, 0x5100) in ds:  # PatientPosition
                slice_orientation = str(ds[0x0018, 0x5100].value)
        except:
            pass
        
        # Magnetic field strength
        magnetic_field_strength = getattr(ds, 'MagneticFieldStrength', None)
        
        # Percent phase field of view
        percent_phase_fov = None
        try:
            if (0x0018, 0x0094) in ds:  # PercentPhaseFieldOfView
                percent_phase_fov = ds[0x0018, 0x0094].value
        except:
            pass
        
        # Percent sampling
        percent_sampling = None
        try:
            if (0x0018, 0x0093) in ds:  # PercentSampling
                percent_sampling = ds[0x0018, 0x0093].value
        except:
            pass
        
        # Position
        img_pos = getattr(ds, 'ImagePositionPatient', None)
        position = ''
        if img_pos and len(img_pos) >= 3:
            position = f"{img_pos[0]:.4f},{img_pos[1]:.4f},{img_pos[2]:.4f}"
        
        # Study info
        study_desc = str(getattr(ds, 'StudyDescription', ''))
        
        # Format datetime
        series_date = getattr(ds, 'SeriesDate', '')
        series_time = getattr(ds, 'SeriesTime', '')
        
        def format_datetime(date_str, time_str):
            if date_str and time_str:
                try:
                    date_part = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                    time_part = f"{time_str[:2]}:{time_str[2:4]}"
                    return f"{date_part}-{time_part}"
                except:
                    return ''
            return ''
        
        series_acq_time = format_datetime(series_date, series_time)
        
        # ===== Diffusion MRI and multi-volume sequences =====
        # Try to get diffusion b-value (standard tag 0018,9087)
        diffusion_bvalue = None
        is_diffusion_mri = False
        num_volumes = None  # Total number of volumes (temporal dimension)
        num_b0s = None      # Number of b0 volumes (only for diffusion MRI)
        
        try:
            # Standard DICOM tag for b-value (0018,9087)
            if hasattr(ds, 'DiffusionBValue'):
                diffusion_bvalue = getattr(ds, 'DiffusionBValue', None)
            # Try accessing via tag
            elif (0x0018, 0x9087) in ds:
                diffusion_bvalue = ds[0x0018, 0x9087].value
            # Alternative private tags (vendor specific)
            elif (0x0019, 0x100c) in ds:  # Siemens
                diffusion_bvalue = ds[0x0019, 0x100c].value
        except:
            pass
        
        # Check for .bval file first (most reliable for diffusion MRI volume counting)
        bval_file = None
        folder_path_obj = Path(dicom_files[0]).parent if dicom_files else None
        
        if folder_path_obj and folder_path_obj.exists():
            # Look for .bval file in the folder
            for bval_candidate in folder_path_obj.glob('*.bval'):
                bval_file = bval_candidate
                break
        
        # Try to read volumes from .bval file (most accurate for diffusion MRI)
        if bval_file and bval_file.exists():
            try:
                with open(bval_file, 'r') as f:
                    bval_content = f.read().strip()
                    bval_values = [float(x) for x in bval_content.split() if x.strip()]
                    num_volumes = len(bval_values)
                    num_b0s = len([b for b in bval_values if b == 0])
                    is_diffusion_mri = True
                    print(f"    -> Read from .bval file: {num_volumes} volumes, {num_b0s} b0s")
                    # If we have volumes from .bval, we can calculate Z_Dim accurately
                    # BUT: For MOSAIC, Z_Dim was already correctly set from NumberOfImagesInMosaic!
                    if num_volumes > 1 and len(dicom_files) > num_volumes and not is_mosaic:
                        calculated_z_dim = len(dicom_files) // num_volumes
                        if calculated_z_dim > 0:
                            z_dim = calculated_z_dim
                            print(f"    -> Calculated Z_Dim from .bval: {z_dim} slices per volume")
            except Exception as e:
                print(f"    -> Warning: Error reading .bval file: {e}")
        
        # If .bval file not available, analyze DICOM files to determine sequence type
        if num_volumes is None and len(dicom_files) > 1:
            try:
                # Check if this is a diffusion sequence by checking b-values
                unique_bvalues = set()
                bvalue_file_count = {}  # Count files per b-value
                b0_file_count = 0
                
                # Use already collected b-values from cache (if available)
                # Otherwise, sample files to determine if diffusion MRI
                if bvalue_to_files:
                    # Use data already collected in Z_Dim calculation
                    unique_bvalues = set(bvalue_to_files.keys())
                    b0_file_count = len(bvalue_to_files.get(0.0, set()))
                    for bval, files in bvalue_to_files.items():
                        if bval != 0:
                            bvalue_file_count[bval] = len(files)
                else:
                    # Need to sample files
                    sample_size = min(100, len(dicom_files))
                    sample_indices = [i * len(dicom_files) // sample_size for i in range(sample_size)] if sample_size > 0 else [0]
                    
                    for idx in sample_indices:
                        if idx >= len(dicom_files):
                            continue
                        ds_sample = cache.get_dicom(dicom_files[idx])
                        if ds_sample is None:
                            continue
                        
                        # Get b-value
                        bval = None
                        if hasattr(ds_sample, 'DiffusionBValue'):
                            bval = getattr(ds_sample, 'DiffusionBValue', None)
                        elif (0x0018, 0x9087) in ds_sample:
                            bval = ds_sample[0x0018, 0x9087].value
                        elif (0x0019, 0x100c) in ds_sample:  # Siemens
                            bval = ds_sample[0x0019, 0x100c].value
                        
                        if bval is not None:
                            try:
                                bval_float = float(bval)
                                unique_bvalues.add(bval_float)
                                if bval_float == 0:
                                    b0_file_count += 1
                                else:
                                    bvalue_file_count[bval_float] = bvalue_file_count.get(bval_float, 0) + 1
                            except:
                                pass
                
                # If we found b-values, this is diffusion MRI
                if len(unique_bvalues) > 0:
                    is_diffusion_mri = True
                    # Count all files to get accurate b-value distribution
                    if len(dicom_files) <= 500:  # Only count all files if reasonable number
                        unique_bvalues_full = set()
                        b0_file_count_full = 0
                        for dicom_file in dicom_files:
                            try:
                                ds_sample = pydicom.dcmread(dicom_file, stop_before_pixels=True)
                                bval = None
                                if hasattr(ds_sample, 'DiffusionBValue'):
                                    bval = getattr(ds_sample, 'DiffusionBValue', None)
                                elif (0x0018, 0x9087) in ds_sample:
                                    bval = ds_sample[0x0018, 0x9087].value
                                elif (0x0019, 0x100c) in ds_sample:
                                    bval = ds_sample[0x0019, 0x100c].value
                                
                                if bval is not None:
                                    try:
                                        bval_float = float(bval)
                                        unique_bvalues_full.add(bval_float)
                                        if bval_float == 0:
                                            b0_file_count_full += 1
                                    except:
                                        pass
                            except:
                                continue
                        
                        # NumberOfVolumes = number of unique b-values (each b-value represents one volume)
                        num_volumes = len(unique_bvalues_full)
                        # NumberOfB0s = number of b0 volumes (count unique b0 volumes, not files)
                        # Since each volume has multiple slices, we need to estimate
                        # If we have b0 files, estimate volumes: total_files / files_per_volume
                        if b0_file_count_full > 0:
                            # Estimate files per volume (assuming similar slice count per volume)
                            estimated_files_per_volume = len(dicom_files) // max(1, len(unique_bvalues_full))
                            num_b0s = max(1, b0_file_count_full // max(1, estimated_files_per_volume))
                        else:
                            num_b0s = 0
                    else:
                        # For large series, estimate from sample
                        num_volumes = len(unique_bvalues)
                        if b0_file_count > 0:
                            estimated_files_per_volume = len(dicom_files) // max(1, len(unique_bvalues))
                            num_b0s = max(1, b0_file_count // max(1, estimated_files_per_volume))
                        else:
                            num_b0s = 0
                    
                    print(f"    -> Diffusion MRI detected: {num_volumes} volumes, {num_b0s} b0s")
                
                # If not diffusion MRI, check for fMRI or other multi-volume sequences
                elif 'fmri' in series_description.lower() or 'functional' in series_description.lower() or 'bold' in series_description.lower():
                    # For fMRI, check InstanceNumber or TemporalPositionIndex to count volumes
                    # This is a simplified approach - in practice, may need more sophisticated logic
                    instance_numbers = set()
                    temporal_positions = set()
                    
                    # Use already collected data from cache if available
                    if not temporal_positions and not instance_numbers:
                        # Need to collect data
                        sample_size = min(200, len(dicom_files))
                        sample_indices = [i * len(dicom_files) // sample_size for i in range(sample_size)] if sample_size > 0 else [0]
                        
                        for idx in sample_indices:
                            if idx >= len(dicom_files):
                                continue
                            ds_sample = cache.get_dicom(dicom_files[idx])
                            if ds_sample is None:
                                continue
                            
                            instance_num = getattr(ds_sample, 'InstanceNumber', None)
                            if instance_num is not None:
                                instance_numbers.add(instance_num)
                            
                            # Check TemporalPositionIndex (for multi-volume sequences)
                            if (0x0020, 0x9128) in ds_sample:
                                temporal_pos = ds_sample[0x0020, 0x9128].value
                                if temporal_pos is not None:
                                    temporal_positions.add(temporal_pos)
                    
                    # Estimate volumes from instance numbers or temporal positions
                    if len(temporal_positions) > 1:
                        num_volumes = len(temporal_positions)
                        print(f"    -> fMRI/multi-volume detected: {num_volumes} volumes (from TemporalPositionIndex)")
                    elif len(instance_numbers) > z_dim:
                        # If instance numbers span more than slices, likely multi-volume
                        # Estimate: total instances / slices per volume
                        max_instance = max(instance_numbers) if instance_numbers else len(dicom_files)
                        estimated_volumes = max_instance // max(1, z_dim)
                        if estimated_volumes > 1:
                            num_volumes = estimated_volumes
                            print(f"    -> Multi-volume sequence detected: {num_volumes} volumes (estimated)")
                
            except Exception as e:
                print(f"    Warning: Error calculating volumes: {e}")
        
        # ===== End Diffusion MRI and multi-volume fields =====
        
        # Create output structure with units
        output_data = {
            'SeriesNumber': [series_number],
            'FolderName': [folder_name],
            'SeriesDescription': [series_description],
            'MRAcquisitionType': [mr_acq_type],
            'X_Dim': [columns],  # pixels
            'Y_Dim': [rows],  # pixels
            'Z_Dim': [z_dim],  # slices
            'X_Voxel': [x_voxel],  # mm
            'Y_Voxel': [y_voxel],  # mm
            'Z_Voxel': [z_voxel],  # mm
            'SliceGap': [slice_gap],  # mm
            'InversionTime': [inversion_time],  # ms
            'EchoTime': [echo_time],  # ms
            'RepetitionTime': [repetition_time],  # ms
            'FlipAngle': [flip_angle],  # degrees
            'Position': [position],  # x,y,z coordinates
            'StudyDescription': [study_desc],
            'SeriesAcqTime': [series_acq_time],
            'DiffusionBValue': [diffusion_bvalue],  # s/mm²
            # Parallel imaging and acceleration factors
            'MultibandFactor': [multiband_factor],  # factor
            'InplaneAccelFactor': [inplane_accel_factor],  # factor
            # Additional fields
            'PhaseEncodingDirection': [phase_encoding_direction],
            'NumberOfAverages': [number_of_averages],  # count
            'Bandwidth': [bandwidth],  # Hz/pixel
            'CoilName': [coil_name],
            'SliceOrientation': [slice_orientation],
            # New fields
            'MagneticFieldStrength': [magnetic_field_strength],  # T (Tesla)
            'PercentPhaseFOV': [percent_phase_fov],  # %
            'PercentSampling': [percent_sampling]  # %
        }
        
        # Only add NumberOfVolumes if it's a multi-volume sequence (diffusion MRI, fMRI, etc.)
        if num_volumes is not None and num_volumes > 1:
            output_data['NumberOfVolumes'] = [num_volumes]
            
            # CRITICAL: For MOSAIC format, Z_Dim is ALREADY correct from NumberOfImagesInMosaic
            # DO NOT recalculate it from total_files / num_volumes!
            # MOSAIC: each file = 1 volume containing multiple slices tiled into one image
            if not is_mosaic:
                # For non-MOSAIC: Z_Dim = total_files / NumberOfVolumes
                calculated_z_dim = len(dicom_files) // num_volumes
                if calculated_z_dim > 0:
                    z_dim = calculated_z_dim
                    # CRITICAL: Replace Z_Dim value, don't append
                    output_data['Z_Dim'] = [z_dim]  # This replaces the existing value
                    print(f"    -> Corrected Z_Dim: {z_dim} slices per volume (total files: {len(dicom_files)}, volumes: {num_volumes})")
            else:
                # For MOSAIC: keep the Z_Dim from NumberOfImagesInMosaic
                print(f"    -> MOSAIC Z_Dim preserved: {z_dim} slices per volume (from NumberOfImagesInMosaic)")
        else:
            output_data['NumberOfVolumes'] = [None]
        
        # Only add NumberOfB0s if it's diffusion MRI
        if is_diffusion_mri:
            output_data['NumberOfB0s'] = [num_b0s if num_b0s is not None else None]
        else:
            output_data['NumberOfB0s'] = [None]
        
        # Ensure all values are single scalar values (not lists) for DataFrame creation
        # Convert all list values to single scalar values
        cleaned_output_data = {}
        for key, value_list in output_data.items():
            if isinstance(value_list, list):
                if len(value_list) == 0:
                    cleaned_output_data[key] = None
                elif isinstance(value_list[0], (list, tuple)):
                    # Nested list - take first element of first element
                    cleaned_output_data[key] = value_list[0][0] if len(value_list[0]) > 0 else None
                else:
                    # Single value in list - extract it (should always be length 1)
                    cleaned_output_data[key] = value_list[0]
            else:
                # Not a list - use as is
                cleaned_output_data[key] = value_list
        
        # Debug: Check for any remaining list/tuple values that might cause multiple rows
        for key, value in cleaned_output_data.items():
            if isinstance(value, (list, tuple)):
                print(f"    WARNING: {key} is still a list/tuple: {value}, taking first element")
                cleaned_output_data[key] = value[0] if len(value) > 0 else None
        
        # Create DataFrame from single-row dictionary - explicitly create as single row
        # CRITICAL: Use pd.DataFrame([dict]) to ensure exactly 1 row
        df = pd.DataFrame([cleaned_output_data])  # Wrap in list to ensure single row
        
        # DEBUG: Print cleaned data to check for issues
        if len(df) != 1:
            print(f"    ERROR: DataFrame has {len(df)} rows instead of 1 for {folder_name}")
            print(f"    DataFrame shape: {df.shape}")
            print(f"    First few rows:")
            print(df.head())
            print(f"    Columns with list/tuple values:")
            for col in df.columns:
                col_values = df[col].tolist()
                has_list = any(isinstance(v, (list, tuple)) for v in col_values)
                if has_list:
                    print(f"      {col}: {col_values}")
            # Force to 1 row by taking first row
            df = df.iloc[[0]].copy()
            print(f"    -> Forced to 1 row")
        
        # DOUBLE CHECK: Ensure exactly 1 row
        if len(df) > 1:
            print(f"    CRITICAL: Still {len(df)} rows after force, taking first row only")
            df = df.iloc[[0]].copy()
        
        csv_path = os.path.join(output_path, f"{folder_name}.csv")
        
        # FINAL CHECK: Verify DataFrame has exactly 1 row before saving
        if len(df) != 1:
            print(f"    CRITICAL ERROR: DataFrame still has {len(df)} rows before saving!")
            print(f"    Taking first row only...")
            df = df.iloc[[0]].copy()
        
        # Save CSV
        df.to_csv(csv_path, index=False)
        
        # Verify saved CSV has only 1 row
        try:
            verify_df = pd.read_csv(csv_path)
            if len(verify_df) != 1:
                print(f"    WARNING: Saved CSV has {len(verify_df)} rows! Reading and fixing...")
                # Re-read and keep only first row
                verify_df = verify_df.iloc[[0]].copy()
                verify_df.to_csv(csv_path, index=False)
                print(f"    -> Fixed CSV to 1 row")
        except Exception as e:
            print(f"    Warning: Could not verify CSV file: {e}")
        
        print(f"    -> Generated CSV: {csv_path} (1 row, {len(df.columns)} columns)")
        
    except Exception as e:
        print(f"  Error processing folder {folder_name}: {e}")


def _process_single_folder(args):
    """Helper function for parallel folder processing"""
    folder_path, folder_name, output_path = args
    try:
        dicom_files = find_dicom_files(folder_path, use_parallel=False)  # Don't parallelize nested calls
        if dicom_files:
            gather_info(dicom_files, folder_name, output_path)
            return (folder_name, True, None)
        return (folder_name, False, None)
    except Exception as e:
        return (folder_name, False, str(e))


def process_dicom_folders(base_path, output_path, use_parallel=True):
    """Process all folders containing DICOM files"""
    folders = [f for f in Path(base_path).iterdir() if f.is_dir() and f.name not in ['.', '..']]
    print(f"  Found {len(folders)} folders to process")
    
    if len(folders) == 0:
        return
    
    csv_count = 0
    
    if use_parallel and len(folders) > 5:
        print(f"  Using parallel processing with {MAX_WORKERS} workers...")
        args_list = [(str(folder), folder.name, output_path) for folder in folders]
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            results = list(executor.map(_process_single_folder, args_list))
        
        for folder_name, success, error in results:
            if error:
                print(f"  Error processing folder {folder_name}: {error}")
            elif success:
                csv_count += 1
    else:
        # Sequential processing
        for folder in folders:
            dicom_files = find_dicom_files(str(folder), use_parallel=False)
            if dicom_files:
                print(f"  Processing folder {folder.name} ({len(dicom_files)} DICOM files)...")
                gather_info(dicom_files, folder.name, output_path)
                csv_count += 1
    
    print(f"Processed {len(folders)} folders, generated {csv_count} CSV files")


def _read_and_process_csv(csv_file):
    """Helper function for parallel CSV reading"""
    essential_columns = ['SeriesNumber', 'FolderName', 'SeriesDescription',
                        'MRAcquisitionType', 'X_Dim', 'Y_Dim', 'Z_Dim', 'X_Voxel', 'Y_Voxel', 'Z_Voxel',
                        'SliceGap', 'InversionTime', 'EchoTime',
                        'RepetitionTime', 'FlipAngle', 'Position', 'StudyDescription',
                        'SeriesAcqTime',
                        'DiffusionBValue', 'NumberOfVolumes', 'NumberOfB0s',
                        'MultibandFactor', 'InplaneAccelFactor',
                        'PhaseEncodingDirection', 'NumberOfAverages', 'Bandwidth',
                        'CoilName', 'SliceOrientation',
                        'MagneticFieldStrength', 'PercentPhaseFOV', 'PercentSampling']
    
    try:
        df = pd.read_csv(csv_file)
        # Ensure all columns exist
        for col in essential_columns:
            if col not in df.columns:
                if col in ['SeriesNumber', 'X_Fov', 'Y_Fov', 'Z_Fov', 'X_Dim', 'Y_Dim', 
                          'Z_Dim', 'X_Voxel', 'Y_Voxel', 'Z_Voxel', 'SliceGap', 
                          'InversionTime', 'EchoTime', 'RepetitionTime', 'FlipAngle',
                          'MultibandFactor', 'InplaneAccelFactor', 'NumberOfAverages', 'Bandwidth',
                          'MagneticFieldStrength', 'PercentPhaseFOV', 'PercentSampling']:
                    df[col] = None
                else:
                    df[col] = ''
        
        df = df[essential_columns]
        return (df, None)
    except Exception as e:
        return (None, str(e))


def check_and_ask_overwrite_csv(output_path, merged_csv_filename, gui_mode=False, root=None):
    """Check if CSV files exist and ask user if they want to overwrite"""
    output_path_obj = Path(output_path)
    csv_files = list(output_path_obj.glob('*.csv')) if output_path_obj.exists() else []
    merged_csv_path = output_path_obj / merged_csv_filename
    
    if csv_files or merged_csv_path.exists():
        if gui_mode and GUI_AVAILABLE and root:
            # GUI mode - must use root.after to call from main thread
            import queue
            import threading
            result_queue = queue.Queue()
            event = threading.Event()
            
            def ask_in_main_thread():
                try:
                    from tkinter import messagebox
                    response = messagebox.askyesno(
                        "CSV Files Exist",
                        f"CSV files already exist in:\n{output_path}\n\n"
                        f"Found {len(csv_files)} CSV file(s).\n"
                        f"Summary CSV: {merged_csv_path.name}\n\n"
                        "Do you want to overwrite them?",
                        icon='question'
                    )
                    result_queue.put(response)
                except Exception as e:
                    result_queue.put(False)  # On error, don't overwrite
                finally:
                    event.set()
            
            root.after(0, ask_in_main_thread)
            # Wait for response (with timeout)
            event.wait(timeout=300)  # Wait up to 5 minutes
            try:
                response = result_queue.get_nowait()
                return response
            except queue.Empty:
                return False  # Timeout or error, don't overwrite
        else:
            # CLI mode
            print(f"\n{'='*70}")
            print("WARNING: CSV files already exist!")
            print(f"{'='*70}")
            print(f"Output directory: {output_path}")
            print(f"Found {len(csv_files)} CSV file(s)")
            if merged_csv_path.exists():
                print(f"Summary CSV: {merged_csv_path.name}")
            print("\nDo you want to overwrite existing CSV files?")
            response = input("Enter 'yes' to overwrite, or 'no' to skip: ").strip().lower()
            return response in ['yes', 'y']
    return True  # No existing files, proceed


def check_and_ask_overwrite_nii(nii_base_dir, gui_mode=False, root=None):
    """Check if NIfTI files exist and ask user if they want to overwrite"""
    nii_base_dir_obj = Path(nii_base_dir)
    
    if nii_base_dir_obj.exists():
        # Check if directory has any files
        nii_files = list(nii_base_dir_obj.rglob('*.nii*'))
        if nii_files:
            if gui_mode and GUI_AVAILABLE and root:
                # GUI mode - must use root.after to call from main thread
                import queue
                import threading
                result_queue = queue.Queue()
                event = threading.Event()
                
                def ask_in_main_thread():
                    try:
                        from tkinter import messagebox
                        response = messagebox.askyesno(
                            "NIfTI Files Exist",
                            f"NIfTI files already exist in:\n{nii_base_dir}\n\n"
                            f"Found {len(nii_files)} NIfTI file(s).\n\n"
                            "Do you want to overwrite them?",
                            icon='question'
                        )
                        result_queue.put(response)
                    except Exception as e:
                        result_queue.put(False)  # On error, don't overwrite
                    finally:
                        event.set()
                
                root.after(0, ask_in_main_thread)
                # Wait for response (with timeout)
                event.wait(timeout=300)  # Wait up to 5 minutes
                try:
                    response = result_queue.get_nowait()
                    return response
                except queue.Empty:
                    return False  # Timeout or error, don't overwrite
            else:
                # CLI mode
                print(f"\n{'='*70}")
                print("WARNING: NIfTI files already exist!")
                print(f"{'='*70}")
                print(f"NIfTI directory: {nii_base_dir}")
                print(f"Found {len(nii_files)} NIfTI file(s)")
                print("\nDo you want to overwrite existing NIfTI files?")
                response = input("Enter 'yes' to overwrite, or 'no' to skip: ").strip().lower()
                return response in ['yes', 'y']
    return True  # No existing files, proceed


def run_dcm2niix_on_folders(base_path, dcm2niix_path='dcm2niix', use_parallel=True):
    """
    Run dcm2niix on each organized folder separately.
    This avoids the issue where dcm2niix only processes the last file.
    
    Args:
        base_path: Base directory containing organized DICOM folders
        dcm2niix_path: Path to dcm2niix executable (default: 'dcm2niix')
        use_parallel: Whether to process folders in parallel
    """
    base_path_obj = Path(base_path)
    
    if not base_path_obj.exists():
        print(f"ERROR: Directory {base_path} does not exist!")
        return
    
    # Find all folders containing DICOM files
    folders = []
    for item in base_path_obj.iterdir():
        if item.is_dir():
            # Check if folder contains DICOM files
            dicom_files = find_dicom_files(str(item), use_parallel=False)
            if dicom_files:
                folders.append(item)
    
    if not folders:
        print(f"No folders with DICOM files found in {base_path}")
        return
    
    print(f"Found {len(folders)} folders with DICOM files")
    print(f"Running dcm2niix on each folder separately...\n")
    
    # Create base output directory for NIfTI files
    nii_base_dir = base_path_obj.parent / f"{base_path_obj.name}_nii"
    nii_base_dir.mkdir(parents=True, exist_ok=True)
    
    def process_folder(folder_path):
        """Process a single folder with dcm2niix"""
        folder_name = folder_path.name
        print(f"Processing folder: {folder_name}")
        
        # Create output directory: base_path_nii/folder_name
        nii_output_dir = nii_base_dir / folder_name
        nii_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Change to folder directory and run dcm2niix
        # Use -f to specify output filename pattern: %d_%t_%3s = Date_Time_SeriesNumber
        # Use -z y to compress output
        # Use -b y to save BIDS sidecar (includes .bval and .bvec for diffusion)
        # Use -s y to save single file (don't split series)
        # Use -m y to merge 2D slices from same series
        # Use -ba y to anonymize BIDS sidecar
        # Pattern format: %d = SeriesDate, %t = SeriesTime, %3s = SeriesNumber (3 digits)
        cmd = [
            dcm2niix_path,
            '-z', 'y',      # Compress output (.nii.gz)
            '-b', 'y',      # Save BIDS sidecar (.json)
            '-s', 'y',      # Save single file (don't split series)
            '-m', 'y',      # Merge 2D slices from same series
            '-ba', 'n',     # Don't anonymize BIDS sidecar (keep all info)
            '-f', '%d_%t_%3s',  # Output filename: Date_Time_SeriesNumber
            '-o', str(nii_output_dir),  # Output directory (_nii folder)
            str(folder_path)  # Input directory
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(folder_path),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per folder
            )
            
            if result.returncode == 0:
                print(f"  ✓ Successfully processed {folder_name}")
                if result.stdout:
                    # Print key information from dcm2niix output
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'Convert' in line or 'Saving' in line:
                            print(f"    {line}")
            else:
                print(f"  ✗ Error processing {folder_name}")
                if result.stderr:
                    print(f"    Error: {result.stderr[:200]}")
            return (folder_name, result.returncode == 0)
        except subprocess.TimeoutExpired:
            print(f"  ✗ Timeout processing {folder_name}")
            return (folder_name, False)
        except FileNotFoundError:
            print(f"  ✗ dcm2niix not found. Please install dcm2niix or specify correct path.")
            return (folder_name, False)
        except Exception as e:
            print(f"  ✗ Error processing {folder_name}: {e}")
            return (folder_name, False)
    
    # Process folders
    if use_parallel and len(folders) > 1:
        print(f"Using parallel processing with {min(MAX_WORKERS, len(folders))} workers...\n")
        with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(folders))) as executor:
            results = list(executor.map(process_folder, folders))
    else:
        results = [process_folder(folder) for folder in folders]
    
    # Summary
    successful = sum(1 for _, success in results if success)
    print(f"\n{'='*50}")
    print(f"Summary: {successful}/{len(folders)} folders processed successfully")
    print(f"{'='*50}")


def merge_csv_files(csv_files, output_file, use_parallel=True):
    """Merge multiple CSV files into one"""
    print(f"  Merging {len(csv_files)} CSV files...")
    
    essential_columns = ['SeriesNumber', 'FolderName', 'SeriesDescription',
                        'MRAcquisitionType', 'X_Dim', 'Y_Dim', 'Z_Dim', 'X_Voxel', 'Y_Voxel', 'Z_Voxel',
                        'SliceGap', 'InversionTime', 'EchoTime',
                        'RepetitionTime', 'FlipAngle', 'Position', 'StudyDescription',
                        'SeriesAcqTime',
                        'DiffusionBValue', 'NumberOfVolumes', 'NumberOfB0s',
                        'MultibandFactor', 'InplaneAccelFactor',
                        'PhaseEncodingDirection', 'NumberOfAverages', 'Bandwidth',
                        'CoilName', 'SliceOrientation',
                        'MagneticFieldStrength', 'PercentPhaseFOV', 'PercentSampling']
    
    merged_df = pd.DataFrame()
    
    if use_parallel and len(csv_files) > 5:
        print(f"  Using parallel processing with {MAX_WORKERS} workers...")
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            results = list(executor.map(_read_and_process_csv, csv_files))
        
        for df, error in results:
            if error:
                print(f"  Warning: Error reading CSV file: {error}")
            elif df is not None:
                merged_df = pd.concat([merged_df, df], ignore_index=True)
    else:
        # Sequential processing
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                # Ensure all columns exist
                for col in essential_columns:
                    if col not in df.columns:
                        if col in ['SeriesNumber', 'X_Fov', 'Y_Fov', 'Z_Fov', 'X_Dim', 'Y_Dim', 
                                  'Z_Dim', 'X_Voxel', 'Y_Voxel', 'Z_Voxel', 'SliceGap', 
                                  'InversionTime', 'EchoTime', 'RepetitionTime', 'FlipAngle',
                                  'DiffusionBValue', 'NumberOfVolumes', 'NumberOfB0s', 'NumberOfDiffusionDirections',
                                  'MultibandFactor', 'InplaneAccelFactor', 'NumberOfAverages', 'Bandwidth']:
                            df[col] = None
                        else:
                            df[col] = ''
                
                df = df[essential_columns]
                merged_df = pd.concat([merged_df, df], ignore_index=True)
            except Exception as e:
                print(f"  Warning: Error reading {csv_file}: {e}")
    
    # Sort by SeriesNumber
    if 'SeriesNumber' in merged_df.columns:
        merged_df = merged_df.sort_values('SeriesNumber')
    
    # CRITICAL: Remove duplicate rows based on FolderName (same series should only appear once)
    if 'FolderName' in merged_df.columns:
        initial_count = len(merged_df)
        # Keep only the first occurrence of each FolderName
        merged_df = merged_df.drop_duplicates(subset=['FolderName'], keep='first')
        if len(merged_df) < initial_count:
            print(f"  Removed {initial_count - len(merged_df)} duplicate rows (same FolderName)")
    
    merged_df.to_csv(output_file, index=False)
    print(f"  Summary CSV saved to: {output_file} ({len(merged_df)} rows)")
    
    # Delete individual CSV files after successful merge
    print(f"  Deleting {len(csv_files)} individual CSV files...")
    deleted_count = 0
    output_file_path = Path(output_file)
    for csv_file in csv_files:
        try:
            csv_path = Path(csv_file)
            # Don't delete the merged file itself
            if csv_path.name != output_file_path.name:
                csv_path.unlink()
                deleted_count += 1
        except Exception as e:
            print(f"  Warning: Could not delete {csv_file}: {e}")
    print(f"  Deleted {deleted_count} individual CSV files.")


def main():
    """Main processing function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='DICOM Info Gatherer - Extract and organize DICOM file information',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a specific folder
  python process_dicom.py "G:\\DIFFUSION_PG\\PETIT_GROU_2019-02-21\\Petit_Grou_20190221_143040754"
  
  # Process with Linux/WSL path
  python process_dicom.py "/mnt/g/DIFFUSION_PG/PETIT_GROU_2019-02-21/Petit_Grou_20190221_143040754"
  
  # Disable parallel processing
  python process_dicom.py "path/to/folder" --no-parallel

Output:
  - Individual CSV files: <output_path>/<SeriesNumber>_<SeriesDescription>.csv
  - Summary CSV file: <output_path>/<folder_name>_summary.csv
  - Output path: <base_path>_CSV
  - NIfTI output (if --dcm2niix): <base_path>_nii

Note:
  - The script automatically detects if files are already organized
  - If .bval files exist, they will be used for accurate volume counting
  - Diffusion MRI fields (NumberOfVolumes, NumberOfB0s) are extracted automatically
        """
    )
    
    parser.add_argument(
        'folder',
        type=str,
        nargs='?',
        default=None,
        help='Path to the folder containing DICOM files (required)'
    )
    
    parser.add_argument(
        '--no-parallel',
        action='store_true',
        help='Disable parallel processing (use sequential processing instead)'
    )
    
    parser.add_argument(
        '--dcm2niix',
        action='store_true',
        help='Run dcm2niix conversion after processing DICOM files'
    )
    
    parser.add_argument(
        '--dcm2niix-path',
        type=str,
        default='dcm2niix',
        help='Path to dcm2niix executable (default: "dcm2niix")'
    )
    
    args = parser.parse_args()
    
    # Get base_path from argument or prompt user
    if args.folder:
        base_path = args.folder
    else:
        print("=" * 70)
        print("DICOM Info Gatherer - Python Version")
        print("=" * 70)
        print("\nUsage: python process_dicom.py <folder_path>")
        print("\nExample:")
        print('  python process_dicom.py "G:\\DIFFUSION_PG\\PETIT_GROU_2019-02-21\\Petit_Grou_20190221_143040754"')
        print("\nPlease provide the folder path:")
        base_path = input("Folder path: ").strip().strip('"').strip("'")
        
        if not base_path:
            print("\nError: No folder path provided. Exiting.")
            sys.exit(1)
    
    # Validate base_path
    base_path_obj = Path(base_path)
    if not base_path_obj.exists():
        print(f"\nError: Folder does not exist: {base_path}")
        print("Please check the path and try again.")
        sys.exit(1)
    
    if not base_path_obj.is_dir():
        print(f"\nError: Path is not a directory: {base_path}")
        sys.exit(1)
    
    # Auto-generate output_path: base_path + "_CSV"
    output_path = str(base_path_obj.parent / f"{base_path_obj.name}_CSV")
    
    # Auto-generate merged CSV filename: base_path folder name + "_summary.csv"
    merged_csv_filename = f"{base_path_obj.name}_summary.csv"
    
    # Enable/disable parallel processing
    use_parallel = not args.no_parallel
    
    # Run dcm2niix conversion
    run_dcm2niix = args.dcm2niix
    dcm2niix_path = args.dcm2niix_path
    
    # Display configuration
    print("=" * 70)
    print("DICOM Info Gatherer - Python Version")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Base path:      {base_path}")
    print(f"  Output path:    {output_path}")
    print(f"  Summary CSV:     {merged_csv_filename}")
    print(f"  Parallel mode:  {'Enabled' if use_parallel else 'Disabled'}")
    if use_parallel:
        print(f"  Workers:        {MAX_WORKERS}")
    if run_dcm2niix:
        print(f"  dcm2niix:      Enabled ({dcm2niix_path})")
    print()
    
    # Create output directory
    os.makedirs(output_path, exist_ok=True)
    
    # Check if files are already organized
    print("Checking if files are already organized...")
    files_already_organized = check_if_files_organized(base_path)
    
    if files_already_organized:
        print("  -> Files are already organized into folders. Skipping organization step.\n")
    else:
        print("  -> Files need to be organized. Proceeding with organization step.\n")
    
    if not files_already_organized:
        # Step 1: Find DICOM files
        print("\nStep 1: Finding DICOM files...")
        dicom_files = find_dicom_files(base_path, use_parallel=use_parallel)
        print(f"Found {len(dicom_files)} DICOM files.\n")
        
        if not dicom_files:
            print("No DICOM files found!")
            return
        
        # Step 2: Organize files
        print("Step 2: Organizing DICOM files into folders...")
        organize_dicom_files(dicom_files, base_path, use_parallel=use_parallel)
        print("DICOM files organized.\n")
    
    # Step 3: Process folders and generate CSV
    # Check if CSV files already exist
    csv_files = list(Path(output_path).glob('*.csv')) if Path(output_path).exists() else []
    merged_csv_path = os.path.join(output_path, merged_csv_filename)
    
    # Auto-overwrite: remove existing CSV directory
    if os.path.exists(output_path):
        import shutil
        try:
            shutil.rmtree(output_path)
            print(f"  Removed existing CSV directory: {output_path}")
        except:
            pass
    os.makedirs(output_path, exist_ok=True)
    
    print("Step 3: Processing folders and generating CSV files...")
    process_dicom_folders(base_path, output_path, use_parallel=use_parallel)
    print("CSV files generated.\n")
    
    # Step 4: Merge CSV files
    print("Step 4: Merging CSV files...")
    csv_files = list(Path(output_path).glob('*.csv'))
    merged_csv_path = os.path.join(output_path, merged_csv_filename)
    if csv_files:
        merge_csv_files([str(f) for f in csv_files], 
                        merged_csv_path,
                        use_parallel=use_parallel)
        print("Merging completed.\n")
    else:
        print("No CSV files found to merge.\n")
    
    # Step 5: Run dcm2niix conversion (optional)
    if run_dcm2niix:
        nii_base_dir = str(base_path_obj.parent / f"{base_path_obj.name}_nii")
        # Auto-overwrite: remove existing NIfTI directory
        if os.path.exists(nii_base_dir):
            import shutil
            try:
                shutil.rmtree(nii_base_dir)
                print(f"  Removed existing NIfTI directory: {nii_base_dir}")
            except:
                pass
        os.makedirs(nii_base_dir, exist_ok=True)
        
        print("Step 5: Running dcm2niix conversion...")
        run_dcm2niix_on_folders(base_path, dcm2niix_path=dcm2niix_path, use_parallel=use_parallel)
        print("dcm2niix conversion completed.\n")
    
    print("=" * 70)
    print("DICOM processing completed successfully!")
    print("=" * 70)
    if csv_files:
        print(f"\nOutput files:")
        print(f"  Individual CSVs: {output_path}")
        print(f"  Summary CSV:      {merged_csv_path}")
        print(f"\nTotal CSV files generated: {len(csv_files)}")
        print(f"Summary CSV contains: {len(pd.read_csv(merged_csv_path))} series")


class DICOMProcessorGUI:
    """GUI application for DICOM Info Gatherer - Modern UI with CustomTkinter"""
    
    def __init__(self, root=None):
        # Use CustomTkinter if available, otherwise fallback to tkinter
        if CUSTOM_TKINTER_AVAILABLE:
            try:
                # Configure CustomTkinter BEFORE creating root window
                ctk.set_appearance_mode("dark")  # "dark" or "light"
                ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"
                
                # Create CustomTkinter root window
                self.root = ctk.CTk()
                self.root.title("DICOM Info Gatherer")
                self.root.geometry("1000x800")
                self.use_ctk = True
            except Exception as e:
                # Fallback to tkinter if CustomTkinter fails
                print(f"Warning: CustomTkinter initialization failed: {e}")
                print("Falling back to standard tkinter...")
                if root is None:
                    self.root = tk.Tk()
                else:
                    self.root = root
                self.root.title("DICOM Info Gatherer")
                self.root.geometry("900x750")
                self.use_ctk = False
        else:
            # Use standard tkinter
            if root is None:
                self.root = tk.Tk()
            else:
                self.root = root
            self.root.title("DICOM Info Gatherer")
            self.root.geometry("900x750")
            self.use_ctk = False
        
        # Variables
        if self.use_ctk:
            self.folder_path = ctk.StringVar()
            self.use_parallel = ctk.BooleanVar(value=True)
            self.run_dcm2niix = ctk.BooleanVar(value=False)
            self.dcm2niix_path = ctk.StringVar(value='dcm2niix')
        else:
            self.folder_path = tk.StringVar()
            self.use_parallel = tk.BooleanVar(value=True)
            self.run_dcm2niix = tk.BooleanVar(value=False)
            self.dcm2niix_path = tk.StringVar(value='dcm2niix')
        
        self.processing = False
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface - Modern UI with CustomTkinter"""
        if self.use_ctk:
            self.setup_ui_ctk()
        else:
            self.setup_ui_tkinter()
    
    def setup_ui_ctk(self):
        """Setup CustomTkinter UI - Modern and beautiful"""
        # Main container
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Main frame
        main_frame = ctk.CTkFrame(self.root)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Header section
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        title_label = ctk.CTkLabel(header_frame,
                                   text="DICOM Info Gatherer",
                                   font=ctk.CTkFont(size=32, weight="bold"))
        title_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        subtitle_label = ctk.CTkLabel(header_frame,
                                     text="Extract and organize DICOM file information",
                                     font=ctk.CTkFont(size=14),
                                     text_color="gray")
        subtitle_label.grid(row=1, column=0, sticky="w")
        
        # Content frame
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 0))
        content_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        
        # Folder selection section
        folder_label = ctk.CTkLabel(content_frame,
                                   text="DICOM Folder",
                                   font=ctk.CTkFont(size=16, weight="bold"))
        folder_label.grid(row=0, column=0, sticky="w", pady=(20, 10), padx=20)
        
        folder_container = ctk.CTkFrame(content_frame, fg_color="transparent")
        folder_container.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        folder_container.grid_columnconfigure(0, weight=1)
        
        self.folder_entry = ctk.CTkEntry(folder_container,
                                         textvariable=self.folder_path,
                                         placeholder_text="Select or enter DICOM folder path...",
                                         font=ctk.CTkFont(size=12),
                                         height=40)
        self.folder_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        browse_btn = ctk.CTkButton(folder_container,
                                   text="Browse",
                                   command=self.browse_folder,
                                   font=ctk.CTkFont(size=12, weight="bold"),
                                   width=100,
                                   height=40)
        browse_btn.grid(row=0, column=1)
        
        # Options section
        options_label = ctk.CTkLabel(content_frame,
                                     text="Processing Options",
                                     font=ctk.CTkFont(size=16, weight="bold"))
        options_label.grid(row=2, column=0, sticky="w", pady=(20, 15), padx=20)
        
        options_container = ctk.CTkFrame(content_frame, fg_color="transparent")
        options_container.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))
        
        # Parallel processing checkbox
        self.parallel_check = ctk.CTkCheckBox(options_container,
                                             text="Enable parallel processing",
                                             variable=self.use_parallel,
                                             font=ctk.CTkFont(size=14))
        self.parallel_check.grid(row=0, column=0, sticky="w", pady=10)
        
        # dcm2niix checkbox
        self.dcm2niix_check = ctk.CTkCheckBox(options_container,
                                             text="Run dcm2niix conversion after processing",
                                             variable=self.run_dcm2niix,
                                             font=ctk.CTkFont(size=14),
                                             command=self.toggle_dcm2niix_path)
        self.dcm2niix_check.grid(row=1, column=0, sticky="w", pady=10)
        
        # dcm2niix path entry
        dcm2niix_path_frame = ctk.CTkFrame(options_container, fg_color="transparent")
        dcm2niix_path_frame.grid(row=2, column=0, sticky="ew", pady=10)
        dcm2niix_path_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(dcm2niix_path_frame,
                    text="dcm2niix path:",
                    font=ctk.CTkFont(size=14)).grid(row=0, column=0, sticky="w", padx=(20, 10))
        
        self.dcm2niix_entry = ctk.CTkEntry(dcm2niix_path_frame,
                                          textvariable=self.dcm2niix_path,
                                          font=ctk.CTkFont(size=12),
                                          height=35,
                                          state="disabled")
        self.dcm2niix_entry.grid(row=0, column=1, sticky="ew")
        
        # Process button
        self.process_button = ctk.CTkButton(content_frame,
                                            text="▶ Start Processing",
                                            command=self.start_processing,
                                            font=ctk.CTkFont(size=16, weight="bold"),
                                            height=50,
                                            corner_radius=10,
                                            fg_color=("#2ecc71", "#27ae60"),
                                            hover_color="#229954")
        self.process_button.grid(row=4, column=0, pady=25, padx=20, sticky="ew")
        
        # Status section
        status_container = ctk.CTkFrame(content_frame, fg_color="transparent")
        status_container.grid(row=5, column=0, sticky="ew", padx=20, pady=(0, 15))
        status_container.grid_columnconfigure(0, weight=1)
        
        # Progress bar - CustomTkinter doesn't have indeterminate mode, use animation
        self.progress = ctk.CTkProgressBar(status_container,
                                          height=20,
                                          corner_radius=10)
        self.progress.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.progress.set(0)
        self.progress_animating = False
        
        # Status label
        self.status_label = ctk.CTkLabel(status_container,
                                        text="Ready to process",
                                        font=ctk.CTkFont(size=14),
                                        text_color="green")
        self.status_label.grid(row=1, column=0, sticky="w")
        
        # Output log section
        log_label = ctk.CTkLabel(content_frame,
                                 text="Output Log",
                                 font=ctk.CTkFont(size=16, weight="bold"))
        log_label.grid(row=6, column=0, sticky="w", pady=(10, 10), padx=20)
        
        # Log text with modern styling
        self.log_text = ctk.CTkTextbox(content_frame,
                                       font=ctk.CTkFont(family="Consolas", size=11),
                                       height=200,
                                       corner_radius=10)
        self.log_text.grid(row=7, column=0, sticky="nsew", padx=20, pady=(0, 20))
        content_frame.grid_rowconfigure(7, weight=1)
    
    def setup_ui_tkinter(self):
        """Fallback tkinter UI if CustomTkinter is not available"""
        # Modern color scheme
        self.colors = {
            'bg': '#f5f5f5',
            'fg': '#2c3e50',
            'accent': '#3498db',
            'accent_hover': '#2980b9',
            'success': '#27ae60',
            'warning': '#f39c12',
            'error': '#e74c3c',
            'card_bg': '#ffffff',
            'border': '#e0e0e0',
            'text_secondary': '#7f8c8d'
        }
        
        # Configure root background
        self.root.configure(bg=self.colors['bg'])
        
        # Main container with padding
        container = tk.Frame(self.root, bg=self.colors['bg'])
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header section with title
        header_frame = tk.Frame(container, bg=self.colors['bg'])
        header_frame.pack(fill=tk.X, pady=(0, 25))
        
        title_label = tk.Label(header_frame, 
                               text="DICOM Info Gatherer",
                               font=("Segoe UI", 24, "bold"),
                               bg=self.colors['bg'],
                               fg=self.colors['fg'])
        title_label.pack(anchor=tk.W)
        
        subtitle_label = tk.Label(header_frame,
                                 text="Extract and organize DICOM file information",
                                 font=("Segoe UI", 10),
                                 bg=self.colors['bg'],
                                 fg=self.colors['text_secondary'])
        subtitle_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Card-style frame for main content
        card_frame = tk.Frame(container, bg=self.colors['card_bg'], relief=tk.FLAT)
        card_frame.pack(fill=tk.BOTH, expand=True)
        
        # Inner padding
        inner_frame = tk.Frame(card_frame, bg=self.colors['card_bg'])
        inner_frame.pack(fill=tk.BOTH, expand=True, padx=25, pady=25)
        inner_frame.columnconfigure(1, weight=1)
        
        # Folder selection section
        folder_label = tk.Label(inner_frame, 
                               text="DICOM Folder",
                               font=("Segoe UI", 11, "bold"),
                               bg=self.colors['card_bg'],
                               fg=self.colors['fg'])
        folder_label.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 8))
        
        folder_container = tk.Frame(inner_frame, bg=self.colors['card_bg'])
        folder_container.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        folder_container.columnconfigure(0, weight=1)
        
        self.folder_entry = tk.Entry(folder_container,
                                     textvariable=self.folder_path,
                                     font=("Segoe UI", 10),
                                     relief=tk.SOLID,
                                     borderwidth=1,
                                     highlightthickness=1,
                                     highlightcolor=self.colors['accent'],
                                     highlightbackground=self.colors['border'])
        self.folder_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        browse_btn = tk.Button(folder_container,
                              text="Browse",
                              command=self.browse_folder,
                              font=("Segoe UI", 10, "bold"),
                              bg=self.colors['accent'],
                              fg='white',
                              activebackground=self.colors['accent_hover'],
                              activeforeground='white',
                              relief=tk.FLAT,
                              cursor='hand2',
                              padx=20,
                              pady=8)
        browse_btn.grid(row=0, column=1)
        
        # Options section
        options_label = tk.Label(inner_frame,
                                text="Processing Options",
                                font=("Segoe UI", 11, "bold"),
                                bg=self.colors['card_bg'],
                                fg=self.colors['fg'])
        options_label.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=(0, 12))
        
        options_container = tk.Frame(inner_frame, bg=self.colors['card_bg'])
        options_container.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 25))
        
        # Parallel processing checkbox
        parallel_frame = tk.Frame(options_container, bg=self.colors['card_bg'])
        parallel_frame.pack(fill=tk.X, pady=8)
        
        self.parallel_check = tk.Checkbutton(parallel_frame,
                                            text="Enable parallel processing",
                                            variable=self.use_parallel,
                                            font=("Segoe UI", 10),
                                            bg=self.colors['card_bg'],
                                            fg=self.colors['fg'],
                                            activebackground=self.colors['card_bg'],
                                            activeforeground=self.colors['fg'],
                                            selectcolor=self.colors['card_bg'],
                                            cursor='hand2')
        self.parallel_check.pack(side=tk.LEFT)
        
        # dcm2niix checkbox
        dcm2niix_frame = tk.Frame(options_container, bg=self.colors['card_bg'])
        dcm2niix_frame.pack(fill=tk.X, pady=8)
        
        self.dcm2niix_check = tk.Checkbutton(dcm2niix_frame,
                                             text="Run dcm2niix conversion after processing",
                                             variable=self.run_dcm2niix,
                                             font=("Segoe UI", 10),
                                             bg=self.colors['card_bg'],
                                             fg=self.colors['fg'],
                                             activebackground=self.colors['card_bg'],
                                             activeforeground=self.colors['fg'],
                                             selectcolor=self.colors['card_bg'],
                                             cursor='hand2',
                                             command=self.toggle_dcm2niix_path)
        self.dcm2niix_check.pack(side=tk.LEFT)
        
        # dcm2niix path entry
        dcm2niix_path_frame = tk.Frame(options_container, bg=self.colors['card_bg'])
        dcm2niix_path_frame.pack(fill=tk.X, pady=8)
        dcm2niix_path_frame.columnconfigure(1, weight=1)
        
        tk.Label(dcm2niix_path_frame,
                text="dcm2niix path:",
                font=("Segoe UI", 10),
                bg=self.colors['card_bg'],
                fg=self.colors['fg']).grid(row=0, column=0, sticky=tk.W, padx=(20, 10))
        
        self.dcm2niix_entry = tk.Entry(dcm2niix_path_frame,
                                       textvariable=self.dcm2niix_path,
                                       font=("Segoe UI", 10),
                                       relief=tk.SOLID,
                                       borderwidth=1,
                                       highlightthickness=1,
                                       highlightcolor=self.colors['accent'],
                                       highlightbackground=self.colors['border'],
                                       state=tk.DISABLED)
        self.dcm2niix_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        # Process button
        button_container = tk.Frame(inner_frame, bg=self.colors['card_bg'])
        button_container.grid(row=4, column=0, columnspan=3, pady=20)
        
        self.process_button = tk.Button(button_container,
                                        text="▶ Start Processing",
                                        command=self.start_processing,
                                        font=("Segoe UI", 12, "bold"),
                                        bg=self.colors['success'],
                                        fg='white',
                                        activebackground='#229954',
                                        activeforeground='white',
                                        relief=tk.FLAT,
                                        cursor='hand2',
                                        padx=40,
                                        pady=12)
        self.process_button.pack()
        
        # Status section
        status_container = tk.Frame(inner_frame, bg=self.colors['card_bg'])
        status_container.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        status_container.columnconfigure(0, weight=1)
        
        # Progress bar
        self.progress = ttk.Progressbar(status_container,
                                        mode='indeterminate',
                                        length=400,
                                        style="Modern.Horizontal.TProgressbar")
        self.progress.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Status label
        self.status_label = tk.Label(status_container,
                                    text="Ready to process",
                                    font=("Segoe UI", 10),
                                    bg=self.colors['card_bg'],
                                    fg=self.colors['success'])
        self.status_label.grid(row=1, column=0, sticky=tk.W)
        
        # Output log section
        log_label = tk.Label(inner_frame,
                            text="Output Log",
                            font=("Segoe UI", 11, "bold"),
                            bg=self.colors['card_bg'],
                            fg=self.colors['fg'])
        log_label.grid(row=6, column=0, columnspan=3, sticky=tk.W, pady=(0, 8))
        
        log_container = tk.Frame(inner_frame, bg=self.colors['card_bg'])
        log_container.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 0))
        log_container.columnconfigure(0, weight=1)
        log_container.rowconfigure(0, weight=1)
        inner_frame.rowconfigure(7, weight=1)
        
        # Log text with modern styling
        self.log_text = scrolledtext.ScrolledText(log_container,
                                                  height=12,
                                                  wrap=tk.WORD,
                                                  font=("Consolas", 9),
                                                  bg='#1e1e1e',
                                                  fg='#d4d4d4',
                                                  insertbackground='#ffffff',
                                                  relief=tk.FLAT,
                                                  borderwidth=0,
                                                  padx=12,
                                                  pady=12)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure modern style
        self.configure_styles()
        
    def toggle_dcm2niix_path(self):
        """Enable/disable dcm2niix path entry based on checkbox"""
        if self.run_dcm2niix.get():
            if self.use_ctk:
                self.dcm2niix_entry.configure(state="normal")
            else:
                self.dcm2niix_entry.config(state=tk.NORMAL)
        else:
            if self.use_ctk:
                self.dcm2niix_entry.configure(state="disabled")
            else:
                self.dcm2niix_entry.config(state=tk.DISABLED)
    
    def start_progress_animation(self):
        """Start progress bar animation for CustomTkinter"""
        if self.use_ctk:
            self.progress_animating = True
            self._animate_progress()
    
    def _animate_progress(self):
        """Animate progress bar"""
        if not self.progress_animating:
            return
        current = self.progress.get()
        if current >= 1.0:
            self.progress.set(0)
        else:
            self.progress.set(current + 0.02)
        self.root.after(50, self._animate_progress)
    
    def stop_progress_animation(self):
        """Stop progress bar animation"""
        if self.use_ctk:
            self.progress_animating = False
            self.progress.set(0)
        else:
            self.progress.stop()
    
    def configure_styles(self):
        """Configure modern ttk styles (for tkinter fallback)"""
        if not self.use_ctk:
            style = ttk.Style()
            style.theme_use('clam')
            
            # Configure progress bar style
            style.configure("Modern.Horizontal.TProgressbar",
                           background=self.colors['accent'],
                           troughcolor=self.colors['border'],
                           borderwidth=0,
                           lightcolor=self.colors['accent'],
                           darkcolor=self.colors['accent'])
        
    def browse_folder(self):
        """Browse for folder"""
        folder = filedialog.askdirectory(title="Select DICOM Folder")
        if folder:
            self.folder_path.set(folder)
            
    def log(self, message):
        """Add message to log with modern styling"""
        if self.use_ctk:
            self.log_text.insert("end", message + "\n")
            self.log_text.see("end")
        else:
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def start_processing(self):
        """Start processing in a separate thread"""
        if self.processing:
            messagebox.showwarning("Warning", "Processing is already in progress!")
            return
            
        folder = self.folder_path.get().strip().strip('"').strip("'")
        if not folder:
            messagebox.showerror("Error", "Please select a DICOM folder!")
            return
            
        if not Path(folder).exists():
            messagebox.showerror("Error", f"Folder does not exist:\n{folder}")
            return
        
        # Check for existing files BEFORE starting the thread
        base_path_obj = Path(folder)
        output_path = str(base_path_obj.parent / f"{base_path_obj.name}_CSV")
        merged_csv_filename = f"{base_path_obj.name}_merged.csv"
        nii_base_dir = str(base_path_obj.parent / f"{base_path_obj.name}_nii")
        
        overwrite_csv = True
        overwrite_nii = True
        
        # Check CSV files
        csv_files = list(Path(output_path).glob('*.csv')) if Path(output_path).exists() else []
        merged_csv_path = Path(output_path) / merged_csv_filename
        if csv_files or merged_csv_path.exists():
            response = messagebox.askyesno(
                "CSV Files Exist",
                f"CSV files already exist in:\n{output_path}\n\n"
                f"Found {len(csv_files)} CSV file(s).\n"
                f"Summary CSV: {merged_csv_path.name}\n\n"
                "Do you want to overwrite them?",
                icon='question'
            )
            overwrite_csv = response
        
        # Check NIfTI files if dcm2niix is enabled
        if self.run_dcm2niix.get():
            nii_files = list(Path(nii_base_dir).rglob('*.nii*')) if Path(nii_base_dir).exists() else []
            if nii_files:
                response = messagebox.askyesno(
                    "NIfTI Files Exist",
                    f"NIfTI files already exist in:\n{nii_base_dir}\n\n"
                    f"Found {len(nii_files)} NIfTI file(s).\n\n"
                    "Do you want to overwrite them?",
                    icon='question'
                )
                overwrite_nii = response
            
        self.processing = True
        if self.use_ctk:
            self.process_button.configure(state="disabled", text="⏳ Processing...", fg_color="gray")
            self.start_progress_animation()
            self.status_label.configure(text="Processing...", text_color="blue")
            self.log_text.delete("1.0", "end")
        else:
            self.process_button.config(state='disabled', text="⏳ Processing...", bg=self.colors['text_secondary'])
            self.progress.start()
            self.status_label.config(text="Processing...", fg=self.colors['accent'])
            self.log_text.delete(1.0, tk.END)
        
        # Run processing in separate thread with overwrite flags
        thread = threading.Thread(target=self.process_dicom_files, args=(folder, overwrite_csv, overwrite_nii), daemon=True)
        thread.start()
        
    def process_dicom_files(self, base_path, overwrite_csv=True, overwrite_nii=True):
        """Process DICOM files (runs in separate thread)"""
        try:
            # Redirect stdout to GUI log
            import sys
            from io import StringIO
            
            class LogRedirect:
                def __init__(self, log_func):
                    self.log_func = log_func
                    self.buffer = StringIO()
                    
                def write(self, text):
                    if text.strip():
                        self.log_func(text.rstrip())
                    self.buffer.write(text)
                    
                def flush(self):
                    pass
                    
                def getvalue(self):
                    return self.buffer.getvalue()
            
            log_redirect = LogRedirect(self.log)
            old_stdout = sys.stdout
            sys.stdout = log_redirect
            
            try:
                # Process
                base_path_obj = Path(base_path)
                output_path = str(base_path_obj.parent / f"{base_path_obj.name}_CSV")
                merged_csv_filename = f"{base_path_obj.name}_merged.csv"
                use_parallel = self.use_parallel.get()
                run_dcm2niix = self.run_dcm2niix.get()
                dcm2niix_path = self.dcm2niix_path.get()
                
                print("=" * 70)
                print("DICOM Info Gatherer - Python Version")
                print("=" * 70)
                print(f"\nConfiguration:")
                print(f"  Base path:      {base_path}")
                print(f"  Output path:    {output_path}")
                print(f"  Summary CSV:     {merged_csv_filename}")
                print(f"  Parallel mode:  {'Enabled' if use_parallel else 'Disabled'}")
                if use_parallel:
                    print(f"  Workers:        {MAX_WORKERS}")
                if run_dcm2niix:
                    print(f"  dcm2niix:      Enabled ({dcm2niix_path})")
                print()
                
                os.makedirs(output_path, exist_ok=True)
                
                # Check if files are already organized
                print("Checking if files are already organized...")
                files_already_organized = check_if_files_organized(base_path)
                
                if files_already_organized:
                    print("  -> Files are already organized into folders. Skipping organization step.\n")
                else:
                    print("  -> Files need to be organized. Proceeding with organization step.\n")
                
                if not files_already_organized:
                    # Step 1: Find DICOM files
                    print("\nStep 1: Finding DICOM files...")
                    dicom_files = find_dicom_files(base_path, use_parallel=use_parallel)
                    print(f"Found {len(dicom_files)} DICOM files.\n")
                    
                    if not dicom_files:
                        print("No DICOM files found!")
                        sys.stdout = old_stdout
                        self.root.after(0, self.processing_complete, False, "No DICOM files found!")
                        return
                    
                    # Step 2: Organize files
                    print("Step 2: Organizing DICOM files into folders...")
                    organize_dicom_files(dicom_files, base_path, use_parallel=use_parallel)
                    print("DICOM files organized.\n")
                
                # Step 3: Process folders and generate CSV
                # overwrite_csv is already determined in main thread
                if not overwrite_csv:
                    self.log("\nSkipping CSV generation. Existing files will not be overwritten.")
                else:
                    print("Step 3: Processing folders and generating CSV files...")
                    process_dicom_folders(base_path, output_path, use_parallel=use_parallel)
                    print("CSV files generated.\n")
                    
                    # Step 4: Merge CSV files
                    print("Step 4: Merging CSV files...")
                    csv_files = list(Path(output_path).glob('*.csv'))
                    merged_csv_path = os.path.join(output_path, merged_csv_filename)
                    if csv_files:
                        merge_csv_files([str(f) for f in csv_files], 
                                        merged_csv_path,
                                        use_parallel=use_parallel)
                        print("Merging completed.\n")
                    else:
                        print("No CSV files found to merge.\n")
                
                # Step 5: Run dcm2niix conversion (optional)
                if run_dcm2niix:
                    nii_base_dir = str(base_path_obj.parent / f"{base_path_obj.name}_nii")
                    # overwrite_nii is already determined in main thread
                    if not overwrite_nii:
                        self.log("\nSkipping dcm2niix conversion. Existing files will not be overwritten.")
                    else:
                        print("Step 5: Running dcm2niix conversion...")
                        run_dcm2niix_on_folders(base_path, dcm2niix_path=dcm2niix_path, use_parallel=use_parallel)
                        print("dcm2niix conversion completed.\n")
                
                print("=" * 70)
                print("DICOM processing completed successfully!")
                print("=" * 70)
                if csv_files:
                    print(f"\nOutput files:")
                    print(f"  Individual CSVs: {output_path}")
                    print(f"  Summary CSV:      {merged_csv_path}")
                    print(f"\nTotal CSV files generated: {len(csv_files)}")
                    try:
                        print(f"Summary CSV contains: {len(pd.read_csv(merged_csv_path))} series")
                    except:
                        pass
                
                sys.stdout = old_stdout
                self.root.after(0, self.processing_complete, True, merged_csv_path if csv_files else None)
                
            finally:
                sys.stdout = old_stdout
            
        except Exception as e:
            import traceback
            error_msg = f"\nERROR: {str(e)}\n{traceback.format_exc()}"
            self.log(error_msg)
            self.root.after(0, self.processing_complete, False, str(e))
            
    def processing_complete(self, success, result):
        """Called when processing is complete"""
        self.processing = False
        if self.use_ctk:
            self.process_button.configure(state="normal", text="▶ Start Processing", fg_color=("#2ecc71", "#27ae60"))
            self.stop_progress_animation()
            
            if success:
                self.status_label.configure(text="✓ Processing completed successfully!", text_color="green")
                if result:
                    messagebox.showinfo("Success", 
                                      f"Processing completed!\n\nSummary CSV saved to:\n{result}")
            else:
                self.status_label.configure(text=f"✗ Error: {result}", text_color="red")
                messagebox.showerror("Error", f"Processing failed:\n{result}")
        else:
            self.process_button.config(state='normal', text="▶ Start Processing", bg=self.colors['success'])
            self.progress.stop()
            
            if success:
                self.status_label.config(text="✓ Processing completed successfully!", fg=self.colors['success'])
                if result:
                    messagebox.showinfo("Success", 
                                      f"Processing completed!\n\nSummary CSV saved to:\n{result}")
            else:
                self.status_label.config(text=f"✗ Error: {result}", fg=self.colors['error'])
                messagebox.showerror("Error", f"Processing failed:\n{result}")


def main():
    """Main processing function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='DICOM Info Gatherer - Extract and organize DICOM file information',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a specific folder
  python process_dicom.py "G:\\DIFFUSION_PG\\PETIT_GROU_2019-02-21\\Petit_Grou_20190221_143040754"
  
  # Process with Linux/WSL path
  python process_dicom.py "/mnt/g/DIFFUSION_PG/PETIT_GROU_2019-02-21/Petit_Grou_20190221_143040754"
  
  # Disable parallel processing
  python process_dicom.py "path/to/folder" --no-parallel
  
  # Enable dcm2niix conversion
  python process_dicom.py "path/to/folder" --dcm2niix
  
  # Launch GUI mode
  python process_dicom.py --gui

Output:
  - Individual CSV files: <output_path>/<SeriesNumber>_<SeriesDescription>.csv
  - Summary CSV file: <output_path>/<folder_name>_summary.csv
  - Output path: <base_path>_CSV
  - NIfTI output (if --dcm2niix): <base_path>_nii

Note:
  - The script automatically detects if files are already organized
  - If .bval files exist, they will be used for accurate volume counting
  - Diffusion MRI fields (NumberOfVolumes, NumberOfB0s) are extracted automatically
        """
    )
    
    parser.add_argument(
        'folder',
        type=str,
        nargs='?',
        default=None,
        help='Path to the folder containing DICOM files (required unless using --gui)'
    )
    
    parser.add_argument(
        '--gui',
        action='store_true',
        help='Launch graphical user interface'
    )
    
    parser.add_argument(
        '--no-parallel',
        action='store_true',
        help='Disable parallel processing (use sequential processing instead)'
    )
    
    parser.add_argument(
        '--dcm2niix',
        action='store_true',
        help='Run dcm2niix conversion after processing DICOM files'
    )
    
    parser.add_argument(
        '--dcm2niix-path',
        type=str,
        default='dcm2niix',
        help='Path to dcm2niix executable (default: "dcm2niix")'
    )
    
    args = parser.parse_args()
    
    # Launch GUI if requested
    if args.gui:
        if not GUI_AVAILABLE:
            print("ERROR: GUI is not available. tkinter is not installed.")
            print("On Linux, install it using: sudo apt-get install python3-tk")
            sys.exit(1)
        root = tk.Tk()
        app = DICOMProcessorGUI(root)
        root.mainloop()
        return
    
    # Get base_path from argument or prompt user
    if args.folder:
        base_path = args.folder
    else:
        print("=" * 70)
        print("DICOM Info Gatherer - Python Version")
        print("=" * 70)
        print("\nUsage: python process_dicom.py <folder_path>")
        print("   or: python process_dicom.py --gui")
        print("\nExample:")
        print('  python process_dicom.py "G:\\DIFFUSION_PG\\PETIT_GROU_2019-02-21\\Petit_Grou_20190221_143040754"')
        print("\nUse --help for more options")
        print("\nPlease provide the folder path:")
        base_path = input("Folder path: ").strip().strip('"').strip("'")
        
        if not base_path:
            print("\nError: No folder path provided. Exiting.")
            sys.exit(1)
    
    # Validate base_path
    base_path_obj = Path(base_path)
    if not base_path_obj.exists():
        print(f"\nError: Folder does not exist: {base_path}")
        print("Please check the path and try again.")
        sys.exit(1)
    
    if not base_path_obj.is_dir():
        print(f"\nError: Path is not a directory: {base_path}")
        sys.exit(1)
    
    # Auto-generate output_path: base_path + "_CSV"
    output_path = str(base_path_obj.parent / f"{base_path_obj.name}_CSV")
    
    # Auto-generate merged CSV filename: base_path folder name + "_summary.csv"
    merged_csv_filename = f"{base_path_obj.name}_summary.csv"
    
    # Enable/disable parallel processing
    use_parallel = not args.no_parallel
    
    # Run dcm2niix conversion
    run_dcm2niix = args.dcm2niix
    dcm2niix_path = args.dcm2niix_path
    
    # Display configuration
    print("=" * 70)
    print("DICOM Info Gatherer - Python Version")
    print("=" * 70)
    print(f"\nConfiguration:")
    print(f"  Base path:      {base_path}")
    print(f"  Output path:    {output_path}")
    print(f"  Summary CSV:     {merged_csv_filename}")
    print(f"  Parallel mode:  {'Enabled' if use_parallel else 'Disabled'}")
    if use_parallel:
        print(f"  Workers:        {MAX_WORKERS}")
    if run_dcm2niix:
        print(f"  dcm2niix:      Enabled ({dcm2niix_path})")
    print()
    
    # Create output directory
    os.makedirs(output_path, exist_ok=True)
    
    # Check if files are already organized
    print("Checking if files are already organized...")
    files_already_organized = check_if_files_organized(base_path)
    
    if files_already_organized:
        print("  -> Files are already organized into folders. Skipping organization step.\n")
    else:
        print("  -> Files need to be organized. Proceeding with organization step.\n")
    
    if not files_already_organized:
        # Step 1: Find DICOM files
        print("\nStep 1: Finding DICOM files...")
        dicom_files = find_dicom_files(base_path, use_parallel=use_parallel)
        print(f"Found {len(dicom_files)} DICOM files.\n")
        
        if not dicom_files:
            print("No DICOM files found!")
            return
        
        # Step 2: Organize files
        print("Step 2: Organizing DICOM files into folders...")
        organize_dicom_files(dicom_files, base_path, use_parallel=use_parallel)
        print("DICOM files organized.\n")
    
    # Step 3: Process folders and generate CSV
    # Check if CSV files already exist
    csv_files = list(Path(output_path).glob('*.csv')) if Path(output_path).exists() else []
    merged_csv_path = os.path.join(output_path, merged_csv_filename)
    
    # Auto-overwrite: remove existing CSV directory
    if os.path.exists(output_path):
        import shutil
        try:
            shutil.rmtree(output_path)
            print(f"  Removed existing CSV directory: {output_path}")
        except:
            pass
    os.makedirs(output_path, exist_ok=True)
    
    print("Step 3: Processing folders and generating CSV files...")
    process_dicom_folders(base_path, output_path, use_parallel=use_parallel)
    print("CSV files generated.\n")
    
    # Step 4: Merge CSV files
    print("Step 4: Merging CSV files...")
    csv_files = list(Path(output_path).glob('*.csv'))
    merged_csv_path = os.path.join(output_path, merged_csv_filename)
    if csv_files:
        merge_csv_files([str(f) for f in csv_files], 
                        merged_csv_path,
                        use_parallel=use_parallel)
        print("Merging completed.\n")
    else:
        print("No CSV files found to merge.\n")
    
    # Step 5: Run dcm2niix conversion (optional)
    if run_dcm2niix:
        nii_base_dir = str(base_path_obj.parent / f"{base_path_obj.name}_nii")
        # Auto-overwrite: remove existing NIfTI directory
        if os.path.exists(nii_base_dir):
            import shutil
            try:
                shutil.rmtree(nii_base_dir)
                print(f"  Removed existing NIfTI directory: {nii_base_dir}")
            except:
                pass
        os.makedirs(nii_base_dir, exist_ok=True)
        
        print("Step 5: Running dcm2niix conversion...")
        run_dcm2niix_on_folders(base_path, dcm2niix_path=dcm2niix_path, use_parallel=use_parallel)
        print("dcm2niix conversion completed.\n")
    
    print("=" * 70)
    print("DICOM processing completed successfully!")
    print("=" * 70)
    if csv_files:
        print(f"\nOutput files:")
        print(f"  Individual CSVs: {output_path}")
        print(f"  Summary CSV:      {merged_csv_path}")
        print(f"\nTotal CSV files generated: {len(csv_files)}")
        print(f"Summary CSV contains: {len(pd.read_csv(merged_csv_path))} series")


if __name__ == '__main__':
    if len(sys.argv) > 1 and '--gui' in sys.argv:
        if not GUI_AVAILABLE:
            print("ERROR: GUI is not available. tkinter is not installed.")
            print("Please install it or use command-line mode.")
            sys.exit(1)
        
        if CUSTOM_TKINTER_AVAILABLE:
            print("Using CustomTkinter for modern UI...")
            print("Note: If you encounter a segmentation fault, CustomTkinter will be disabled.")
            print("      You can force standard tkinter by setting CUSTOM_TKINTER_AVAILABLE=False")
            try:
                app = DICOMProcessorGUI()
                app.root.mainloop()
            except (Exception, SystemError, OSError) as e:
                import traceback
                print(f"Error initializing CustomTkinter GUI: {e}")
                traceback.print_exc()
                print("Falling back to standard tkinter...")
                root = tk.Tk()
                app = DICOMProcessorGUI(root)
                root.mainloop()
        else:
            print("CustomTkinter not available, using standard tkinter.")
            print("For a modern UI, install CustomTkinter: pip install customtkinter")
            root = tk.Tk()
            app = DICOMProcessorGUI(root)
            root.mainloop()
    else:
        main()

