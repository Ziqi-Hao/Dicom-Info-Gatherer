# DICOM Info Gatherer

<p align="center">
  <img src="GUI.png" alt="DICOM Info Gatherer GUI" width="600">
</p>

## Overview

**DICOM Info Gatherer** is a powerful Python tool for processing DICOM (Digital Imaging and Communications in Medicine) files, extracting comprehensive metadata, and generating structured CSV outputs. Designed for researchers and medical professionals working with MRI data, it provides robust support for advanced sequences including diffusion MRI, fMRI, and Siemens MOSAIC formats.

### ✨ Key Highlights

- 🖥️ **Modern GUI** with intuitive controls and real-time progress tracking
- 🚀 **Parallel Processing** for fast, multi-threaded DICOM analysis
- 📊 **Comprehensive CSV Reports** with 30+ extracted parameters
- 🧠 **Advanced Sequence Support**: Diffusion MRI, fMRI, Multiband/SMS, iPAT/GRAPPA
- 🔬 **Siemens MOSAIC**: Automatic detection and dimension correction
- 🎯 **Intelligent Extraction**: Deep CSA header parsing for accurate parameters
- 📦 **Standalone Executables**: Build Windows/Linux binaries (no Python needed!)

---

## Features

### Core Functionality
- **CSV Generation**: Automatically extracts 30+ metadata fields from DICOM files
- **File Organization**: Organizes DICOM files into folders by series
- **Summary Report**: Merges individual series CSVs into a single `*_summary.csv` file
- **Auto-overwrite**: Automatically clears old outputs for fresh processing

### Advanced DICOM Support
- **Diffusion MRI**: b-values, b-vectors, number of volumes, b0 counts (from .bval/.bvec files)
- **fMRI**: Temporal dimension detection (NumberOfVolumes)
- **Siemens MOSAIC**: Correct dimension extraction (e.g., 160×160 from 800×800 tiled images)
- **Multiband/SMS**: Accurate extraction from CSA headers (`ucMultiSliceMode`)
- **In-plane Acceleration**: iPAT/GRAPPA factors from PATModeText
- **Phase Encoding**: BIDS-compatible format (e.g., `j-`, `i`, `k`)

### Processing Options
- **Parallel Processing**: Multi-threaded for faster execution (default: enabled)
- **dcm2niix Integration**: Optional NIfTI conversion with .bval/.bvec/.json sidecars
- **Dual Interface**: Both GUI and CLI modes

---

## Installation

### Option 1: Use Pre-built Executable (No Python Required!)

Download the latest release for your OS:
- **Windows**: `DICOM-Info-Gatherer.exe`
- **Linux**: `DICOM-Info-Gatherer`

Double-click to launch the GUI, or run from command line. **No installation needed!**

### Option 2: Run from Source (Python)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/Dicom-Info-Gatherer.git
   cd Dicom-Info-Gatherer
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the tool**:
   ```bash
   python process_dicom.py --gui
   ```

### Prerequisites (for Option 2)
- Python 3.7 or higher
- Required packages: `pydicom`, `pandas`, `numpy`
- Optional: `customtkinter` (modern GUI), `dcm2niix` (NIfTI conversion)

---

## Usage

### 🖥️ Graphical User Interface (GUI)

**Launch the GUI**:
```bash
python process_dicom.py --gui
```

Or double-click the executable (if using pre-built version).

**GUI Features**:
- 📁 Folder browser for selecting DICOM directory
- ⚙️ Options for parallel processing and dcm2niix conversion
- 📊 Real-time progress bar and status updates
- 📝 Scrollable log window with detailed processing info

![GUI Screenshot](GUI.png)

---

### 💻 Command Line Interface (CLI)

#### Basic Usage

```bash
python process_dicom.py "path/to/dicom/folder"
```

#### Examples

**Windows:**
```cmd
python process_dicom.py "G:\DIFFUSION_PG\PETIT_GROU_2019-02-21\Petit_Grou_20190221_143040754"
```

**Linux/WSL:**
```bash
python process_dicom.py "/mnt/g/DIFFUSION_PG/PETIT_GROU_2019-02-21/Petit_Grou_20190221_143040754"
```

**Disable parallel processing:**
```bash
python process_dicom.py "path/to/folder" --no-parallel
```

**Enable dcm2niix conversion:**
```bash
python process_dicom.py "path/to/folder" --dcm2niix
```

**Custom dcm2niix path:**
```bash
python process_dicom.py "path/to/folder" --dcm2niix --dcm2niix-path "/usr/local/bin/dcm2niix"
```

**View all options:**
```bash
python process_dicom.py --help
```

---

## Output

### Generated Files

1. **Organized DICOM Folders**: Files organized by series
   - Format: `<SeriesNumber>_<SeriesDescription>/`
   - Example: `32_ep2d_gslider_p8mmiso_b2000/`

2. **CSV Output Directory**: `<base_path>_CSV/`
   - Contains: `<folder_name>_summary.csv` (comprehensive metadata)

3. **NIfTI Output Directory** (optional): `<base_path>_nii/`
   - Contains: `.nii.gz`, `.bval`, `.bvec`, `.json` files per series

### Output Structure

```
<base_path>/
├── 1_localizer/
│   └── DICOM files...
├── 32_ep2d_gslider_p8mmiso_b2000/
│   └── DICOM files...
├── <base_path>_CSV/
│   └── <folder_name>_summary.csv
└── <base_path>_nii/  (if --dcm2niix enabled)
    ├── 1_localizer/
    │   ├── localizer_*.nii.gz
    │   └── localizer_*.json
    └── 32_ep2d_gslider_p8mmiso_b2000/
        ├── ep2d_gslider_*.nii.gz
        ├── ep2d_gslider_*.bval
        ├── ep2d_gslider_*.bvec
        └── ep2d_gslider_*.json
```

---

## Extracted CSV Fields

The `*_summary.csv` file contains **one row per series** with 30+ metadata fields:

### 📋 Series Information
- `FolderName`, `SeriesNumber`, `SeriesDescription`

### 📐 Image Dimensions
- `X_Dim (pixels)`, `Y_Dim (pixels)`, `Z_Dim (slices per volume)`
- `X_Voxel (mm)`, `Y_Voxel (mm)`, `Z_Voxel (mm)`, `SliceGap (mm)`

### 🧲 MRI Parameters
- `TR (ms)`, `TE (ms)`, `FlipAngle (degrees)`, `InversionTime (ms)`
- `MagneticFieldStrength (T)`, `Bandwidth (Hz/pixel)`
- `PercentPhaseFOV (%)`, `PercentSampling (%)`

### ⚡ Parallel Imaging
- `MultibandFactor` (SMS/through-plane acceleration)
- `InplaneAccelFactor` (iPAT/GRAPPA)

### 🧠 Diffusion MRI (if applicable)
- `DiffusionBValue (s/mm²)`, `NumberOfVolumes`, `NumberOfB0s`

### 📍 Acquisition Details
- `PhaseEncodingDirection`, `SliceOrientation`, `CoilName`
- `NumberOfAverages`, `MRAcquisitionType`
- `ImagePositionPatient`, `StudyDescription`, `SeriesAcqTime`

---

## Advanced Features

### 🔬 Siemens MOSAIC Format

Automatically detects and corrects dimensions for MOSAIC sequences (e.g., gSlider):
- **Detects**: `'MOSAIC'` tag in ImageType
- **Extracts**: True acquisition matrix from `AcquisitionMatrix` or private tags
- **Example**: 800×800 (MOSAIC tiled) → 160×160 (true dimensions)

### 🧠 Diffusion MRI Support

**Priority-based extraction**:
1. **.bval/.bvec files** (most accurate, from dcm2niix)
2. **DICOM tags**: `DiffusionBValue`, `DiffusionGradientOrientation`
3. **Temporal indices**: `TemporalPositionIndex`, `InstanceNumber`

**Outputs**:
- `NumberOfVolumes`: Total volumes (including b0s)
- `NumberOfB0s`: Count of b=0 volumes

### ⚡ Multiband & iPAT

**Multiband Factor** (slice/through-plane acceleration):
- **Source**: Siemens CSA Header → `sKSpace.ucMultiSliceMode` (most accurate)
- **Fallback**: `ParallelReductionFactorOutOfPlane`, PATModeText (`s2`, `s3`, etc.)

**In-plane Acceleration Factor** (iPAT/GRAPPA):
- **Source**: Siemens PATModeText → `p2`, `p3`, etc.
- **Fallback**: `ParallelReductionFactorInPlane`, private tags

---

## Building Standalone Executables

Want to distribute a **single executable file** without Python? See [BUILD_GUIDE.md](BUILD_GUIDE.md) for detailed instructions.

### Quick Build

**Windows**:
```cmd
build_windows.bat
```

**Linux**:
```bash
chmod +x build_linux.sh
./build_linux.sh
```

Output: `release/DICOM-Info-Gatherer.exe` (Windows) or `release/DICOM-Info-Gatherer` (Linux)

---

## File Structure

```
Dicom-Info-Gatherer/
├── process_dicom.py          # Main script (CLI + GUI)
├── run_dcm2niix.py           # Standalone dcm2niix runner
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── BUILD_GUIDE.md            # Executable build instructions
├── CHANGELOG.md              # Version history
├── GIT_COMMIT_GUIDE.md       # Git workflow guide
├── build_windows.bat         # Windows build script
├── build_linux.sh            # Linux build script
├── GUI.png                   # GUI screenshot
└── .gitignore                # Git ignore rules
```

---

## Troubleshooting

### GUI Won't Launch
- **Linux**: Install tkinter: `sudo apt-get install python3-tk`
- **CustomTkinter issues**: Falls back to standard tkinter automatically

### Incorrect Dimensions
- Ensure DICOM files are complete and not corrupted
- Check if MOSAIC format is detected (look for "MOSAIC" in processing log)

### dcm2niix Not Found
- Install dcm2niix: https://github.com/rordenlab/dcm2niix/releases
- Or specify path: `--dcm2niix-path "/path/to/dcm2niix"`

---

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

MIT License - See LICENSE file for details

---

## Acknowledgments

- **[pydicom](https://github.com/pydicom/pydicom)** - DICOM file handling
- **[dcm2niix](https://github.com/rordenlab/dcm2niix)** - NIfTI conversion
- **[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)** - Modern GUI framework

---

## Citation

If you use this tool in your research, please cite:

```bibtex
@software{dicom_info_gatherer,
  title = {DICOM Info Gatherer},
  author = {Your Name},
  year = {2024},
  url = {https://github.com/yourusername/Dicom-Info-Gatherer}
}
```

---

## Support

- 📧 Email: your.email@example.com
- 🐛 Issues: https://github.com/yourusername/Dicom-Info-Gatherer/issues
- 💬 Discussions: https://github.com/yourusername/Dicom-Info-Gatherer/discussions

---

**Made with ❤️ for the neuroimaging community**
