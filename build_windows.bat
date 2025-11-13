@echo off
REM ============================================================
REM DICOM Info Gatherer - Windows Build Script
REM ============================================================

echo.
echo ============================================================
echo   Building DICOM Info Gatherer for Windows
echo ============================================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>NUL
if errorlevel 1 (
    echo [ERROR] PyInstaller not found!
    echo.
    echo Please install it first:
    echo   pip install pyinstaller
    echo.
    pause
    exit /b 1
)

REM Clean previous build
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec

echo [1/3] Cleaning previous build... DONE
echo.

REM Build the executable
echo [2/3] Building executable (this may take 2-5 minutes)...
echo.

pyinstaller --onefile ^
  --windowed ^
  --name="DICOM-Info-Gatherer" ^
  --add-data "README.md;." ^
  --hidden-import=tkinter ^
  --hidden-import=customtkinter ^
  --hidden-import=pydicom ^
  --hidden-import=pandas ^
  --hidden-import=numpy ^
  process_dicom.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo [3/3] Build complete!
echo.

REM Create release directory
if not exist release mkdir release
copy dist\DICOM-Info-Gatherer.exe release\
copy README.md release\

echo ============================================================
echo   BUILD SUCCESSFUL!
echo ============================================================
echo.
echo Output location: release\DICOM-Info-Gatherer.exe
echo.
echo You can now distribute the 'release' folder!
echo.

pause

