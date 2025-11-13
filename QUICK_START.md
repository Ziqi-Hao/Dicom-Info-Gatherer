# Quick Start Guide

## Installation

```bash
git clone https://github.com/yourusername/Dicom-Info-Gatherer.git
cd Dicom-Info-Gatherer
pip install -r requirements.txt
```

## Usage

### Command Line

```bash
# Basic usage
python process_dicom.py "path/to/dicom/folder"

# With options
python process_dicom.py "path/to/folder" --dcm2niix --no-parallel
```

### GUI

```bash
python process_dicom.py --gui
```

## Output

- **CSV**: `<base_path>_CSV/<folder_name>_summary.csv`
- **Organized DICOMs**: `<SeriesNumber>_<SeriesDescription>/`
- **NIfTI** (optional): `<base_path>_nii/`

## Help

```bash
python process_dicom.py --help
```
