#!/bin/bash
# ============================================================
# DICOM Info Gatherer - Linux Build Script
# ============================================================

echo ""
echo "============================================================"
echo "  Building DICOM Info Gatherer for Linux"
echo "============================================================"
echo ""

# Check if PyInstaller is installed
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "[ERROR] PyInstaller not found!"
    echo ""
    echo "Please install it first:"
    echo "  pip install pyinstaller"
    echo ""
    exit 1
fi

# Clean previous build
rm -rf build dist *.spec

echo "[1/3] Cleaning previous build... DONE"
echo ""

# Build the executable
echo "[2/3] Building executable (this may take 2-5 minutes)..."
echo ""

pyinstaller --onefile \
  --windowed \
  --name="DICOM-Info-Gatherer" \
  --add-data "README.md:." \
  --hidden-import=tkinter \
  --hidden-import=customtkinter \
  --hidden-import=pydicom \
  --hidden-import=pandas \
  --hidden-import=numpy \
  process_dicom.py

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Build failed!"
    exit 1
fi

echo ""
echo "[3/3] Build complete!"
echo ""

# Create release directory
mkdir -p release
cp dist/DICOM-Info-Gatherer release/
cp README.md release/
chmod +x release/DICOM-Info-Gatherer

echo "============================================================"
echo "  BUILD SUCCESSFUL!"
echo "============================================================"
echo ""
echo "Output location: release/DICOM-Info-Gatherer"
echo ""
echo "You can now distribute the 'release' folder!"
echo ""

