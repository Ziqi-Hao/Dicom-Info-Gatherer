# Building Standalone Executables

This guide explains how to build standalone executables for **Windows** and **Linux** using PyInstaller.

---

## 📋 Prerequisites

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install PyInstaller

```bash
pip install pyinstaller
```

---

## 🪟 Building for Windows

### Option A: Automated Build (Recommended)

Simply double-click or run:

```cmd
build_windows.bat
```

### Option B: Manual Build

```cmd
pyinstaller --onefile ^
  --windowed ^
  --name="DICOM-Info-Gatherer" ^
  --icon=GUI.png ^
  --add-data "README.md;." ^
  --hidden-import=tkinter ^
  --hidden-import=customtkinter ^
  --hidden-import=pydicom ^
  --hidden-import=pandas ^
  --hidden-import=numpy ^
  process_dicom.py
```

**Output**: `dist\DICOM-Info-Gatherer.exe` (~50-100 MB)

---

## 🐧 Building for Linux

### Option A: Automated Build (Recommended)

```bash
chmod +x build_linux.sh
./build_linux.sh
```

### Option B: Manual Build

```bash
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
```

**Output**: `dist/DICOM-Info-Gatherer` (~60-120 MB)

---

## 📦 Output Location

After building:
- **Windows**: `dist\DICOM-Info-Gatherer.exe`
- **Linux**: `dist/DICOM-Info-Gatherer`

The executable can be distributed independently - **no Python installation required!**

---

## ⚙️ Build Options Explained

| Option | Description |
|--------|-------------|
| `--onefile` | Package everything into a single executable |
| `--windowed` | Hide console window (GUI mode only) |
| `--name` | Name of the output executable |
| `--icon` | Application icon (Windows) |
| `--add-data` | Include additional files (README, etc.) |
| `--hidden-import` | Force include modules that PyInstaller might miss |

---

## 🧪 Testing the Executable

### Windows
```cmd
dist\DICOM-Info-Gatherer.exe --help
dist\DICOM-Info-Gatherer.exe --gui
```

### Linux
```bash
dist/DICOM-Info-Gatherer --help
dist/DICOM-Info-Gatherer --gui
```

---

## 🐛 Troubleshooting

### "Failed to execute script" error
- **Cause**: Missing dependencies
- **Fix**: Add `--hidden-import=<module>` for missing modules

### GUI doesn't appear
- **Cause**: `--windowed` flag may hide error messages
- **Fix**: Remove `--windowed` during testing to see console output

### Executable is too large
- **Cause**: PyInstaller bundles entire Python environment
- **Fix**: This is normal. Alternative: Use `--exclude-module` to remove unused packages

### CustomTkinter issues
- **Cause**: CustomTkinter may have packaging issues
- **Fix**: The script has a fallback to standard tkinter

---

## 📝 Notes

1. **Cross-compilation**: You must build on the target OS (Windows exe on Windows, Linux binary on Linux)
2. **Antivirus**: Some antivirus software may flag PyInstaller executables as suspicious (false positive)
3. **Dependencies**: The executable includes all Python dependencies, making it 50-120 MB
4. **dcm2niix**: Not included! Users must install `dcm2niix` separately if they want NIfTI conversion

---

## 🚀 Distribution

After building, you can distribute:
- `DICOM-Info-Gatherer.exe` (Windows) or `DICOM-Info-Gatherer` (Linux)
- `README.md` (optional, for user reference)

No other files are needed!

