# Changelog

## [2.0.0] - 2024-11-13

### Major Updates

- **Complete Python rewrite** - Removed MATLAB dependency
- **Modern GUI** - CustomTkinter-based interface with fallback to tkinter
- **Parallel Processing** - Multi-threaded DICOM processing
- **Siemens MOSAIC Support** - Automatic dimension correction
- **Advanced DICOM Support** - Multiband/SMS, iPAT/GRAPPA, Diffusion MRI, fMRI
- **CSV Generation** - 30+ extracted parameters with units

### Key Features

- CSV generation with comprehensive metadata
- File organization by series
- Summary report merging
- Diffusion MRI: b-values, volumes, b0 counts
- MOSAIC format: dimension correction (e.g., 160×160 from 800×800)
- Multiband/iPAT extraction from CSA headers
- GUI and CLI interfaces

### Bug Fixes

- Fixed: MOSAIC dimension reporting (800×800 → 160×160)
- Fixed: Z_Dim calculation (slices per volume, not total files)
- Fixed: MultibandFactor extraction (correct SMS detection)
- Fixed: InplaneAccelFactor for MOSAIC sequences
- Fixed: Multiple CSV rows per series (now one row)

---

## [1.0.0] - Initial Release (MATLAB)

- Basic DICOM file organization
- CSV generation with basic metadata
- MATLAB-based implementation
