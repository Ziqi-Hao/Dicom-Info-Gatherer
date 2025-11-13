# Changelog

All notable changes to the DICOM Info Gatherer project.

---

## [2.0.0] - 2024-11-13

### 🎉 Major Updates

#### Core Features
- **Complete rewrite in Python** - Removed MATLAB dependency
- **Modern GUI** - CustomTkinter-based interface with fallback to standard tkinter
- **Parallel Processing** - Multi-threaded DICOM processing for improved performance
- **Automatic Organization** - Smart file organization with duplicate detection
- **CSV Generation** - Individual series CSVs merged into comprehensive summary
- **NIfTI Conversion** - Integrated dcm2niix support with organized output

#### Advanced DICOM Support
- **Siemens MOSAIC Format** - Automatic detection and dimension correction
- **Multiband/SMS** - Accurate extraction from CSA headers (ucMultiSliceMode)
- **In-plane Acceleration** - iPAT/GRAPPA factor extraction (PATModeText)
- **Diffusion MRI** - b-value, b-vector, number of volumes/b0s
- **fMRI Support** - Temporal dimension detection
- **Phase Encoding Direction** - BIDS-compatible format

#### Extracted Parameters
- Dimensions: X, Y, Z (with proper multi-volume handling)
- Resolution: Pixel spacing, FOV, slice thickness
- Sequence: TR, TE, Flip Angle, Bandwidth
- Hardware: Magnetic field strength, coil name
- Acceleration: Multiband factor, in-plane acceleration
- Diffusion: b-value, number of volumes, number of b0s
- Sampling: Percent phase FOV, percent sampling
- Orientation: Slice orientation, phase encoding direction

### 🔧 Technical Improvements

#### Robustness
- **Intelligent Dimension Detection** - Statistical consensus from multiple files
- **DICOM Caching** - Reduced I/O operations for better performance
- **Magic Number Detection** - Reliable DICOM identification without file extensions
- **Error Handling** - Comprehensive try-catch blocks with fallbacks

#### Accuracy
- **MOSAIC Correction** - Extracts true acquisition matrix (e.g., 160x160 from 800x800 tiled)
- **Z_Dim Calculation** - Accurate slice count per volume, not total files
- **Volume Detection** - Priority: .bval files > TemporalPositionIndex > InstanceNumber
- **CSA Header Parsing** - Deep extraction of Siemens-specific parameters

#### User Experience
- **Auto-overwrite** - No more confirmation prompts (old outputs auto-deleted)
- **Progress Feedback** - Real-time status updates and progress bar (GUI)
- **Command-line Arguments** - Flexible CLI usage with --help
- **Dual Mode** - Both CLI and GUI support

### 🐛 Bug Fixes
- Fixed: Incorrect dimension reporting for MOSAIC sequences
- Fixed: Z_Dim showing total files instead of slices per volume
- Fixed: MultibandFactor extracting in-plane acceleration (p3) instead of SMS
- Fixed: InplaneAccelFactor showing NumberOfImagesInMosaic (22) for MOSAIC
- Fixed: Multiple CSV rows per series (now strictly one row)
- Fixed: NumberOfVolumes == Z_Dim for diffusion sequences
- Fixed: GUI segmentation fault on overwrite confirmation
- Fixed: Dimension detection overwriting MOSAIC corrections

### 📦 Distribution
- **PyInstaller Support** - Build standalone executables
- **Cross-platform** - Windows (.exe) and Linux builds
- **Build Scripts** - Automated build_windows.bat and build_linux.sh
- **No Dependencies** - Executables bundle all Python dependencies

### 📚 Documentation
- Comprehensive README with CLI/GUI usage
- BUILD_GUIDE.md for creating executables
- GIT_COMMIT_GUIDE.md for version control
- Inline code documentation and debug outputs

---

## [1.0.0] - Initial Release (MATLAB)

### Features
- Basic DICOM file organization
- CSV generation with basic metadata
- MATLAB-based implementation
- Requires Image Processing Toolbox

---

## Version Comparison

| Feature | v1.0 (MATLAB) | v2.0 (Python) |
|---------|---------------|---------------|
| No Installation Required | ❌ | ✅ (with executable) |
| GUI | ❌ | ✅ |
| Parallel Processing | ⚠️ Limited | ✅ Full |
| MOSAIC Support | ❌ | ✅ |
| Multiband Detection | ❌ | ✅ |
| Diffusion MRI | ⚠️ Basic | ✅ Complete |
| Auto-overwrite | ❌ | ✅ |
| Cross-platform | ❌ | ✅ |
| Open Source Dependencies | ❌ | ✅ |

---

**Legend**: ✅ Fully Supported | ⚠️ Partially Supported | ❌ Not Supported

