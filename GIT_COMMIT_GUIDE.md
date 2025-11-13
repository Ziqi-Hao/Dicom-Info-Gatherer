# Git Commit Guide for DICOM Info Gatherer

This guide will help you commit and push your changes to GitHub.

---

## 📋 Pre-commit Checklist

Before committing, ensure:

- ✅ All test scripts have been deleted
- ✅ `process_dicom.py` is working correctly
- ✅ `README.md` is up-to-date
- ✅ `requirements.txt` lists all dependencies
- ✅ `.gitignore` excludes output files and test scripts
- ✅ Build scripts (`build_windows.bat`, `build_linux.sh`) are executable

---

## 🗂️ Current File Structure

### ✅ Files to Commit (Core)
```
├── process_dicom.py          # Main script
├── run_dcm2niix.py           # dcm2niix helper
├── requirements.txt          # Python dependencies
├── README.md                 # Documentation
├── CHANGELOG.md              # Version history
├── BUILD_GUIDE.md            # Executable build guide
├── GIT_COMMIT_GUIDE.md       # This file
├── .gitignore                # Git ignore rules
├── GUI.png                   # GUI screenshot
├── build_windows.bat         # Windows build script
└── build_linux.sh            # Linux build script
```

### ❌ Files Already Deleted (Test Scripts)
```
❌ apply_auto_overwrite.py
❌ check_csv_files.py
❌ check_csv_timestamp.sh
❌ check_dimensions.py
❌ check_json_multiband.py
❌ check_phase_encoding.py
❌ check_series32_in_summary.py
❌ compare_multiband_sources.py
❌ debug_sequence32.py
❌ explore_multiband_calculation.py
❌ search_multiband_in_csa.py
❌ test_gather_info.py
```

### 🚫 Files to Ignore (Never Commit)
```
# Python artifacts
__pycache__/
*.pyc
venv/
env/

# PyInstaller outputs
build/
dist/
*.spec
release/

# Processing outputs
*_CSV/
*_nii/
*_summary.csv

# IDE
.vscode/
.idea/
```

---

## 🚀 Git Workflow

### 1. Check Current Status

```bash
git status
```

**Expected output**:
- New files: `requirements.txt`, `.gitignore`, `BUILD_GUIDE.md`, `CHANGELOG.md`, `build_*.bat/sh`
- Modified files: `README.md`, `process_dicom.py`, `GIT_COMMIT_GUIDE.md`
- Deleted files: All test scripts
- Untracked: `GUI.png` (will be added)

---

### 2. Stage All Changes

```bash
# Stage all changes (new, modified, deleted)
git add -A

# Or stage selectively:
git add process_dicom.py
git add run_dcm2niix.py
git add README.md
git add requirements.txt
git add .gitignore
git add BUILD_GUIDE.md
git add CHANGELOG.md
git add GIT_COMMIT_GUIDE.md
git add build_windows.bat
git add build_linux.sh
git add GUI.png
```

---

### 3. Verify Staged Changes

```bash
git status
```

**Should show**:
- Changes to be committed: All core files
- Untracked files: None (or only ignored files like `__pycache__/`)

---

### 4. Commit Changes

```bash
git commit -m "v2.0.0: Major Python rewrite with GUI, MOSAIC support, and advanced features

- Complete rewrite in Python (removed MATLAB dependency)
- Modern GUI with CustomTkinter (fallback to tkinter)
- Parallel processing for faster DICOM analysis
- Siemens MOSAIC format support with dimension correction
- Accurate Multiband/SMS and iPAT extraction from CSA headers
- Diffusion MRI: b-value, volumes, b0 counts from .bval/.bvec
- fMRI: temporal dimension detection
- Z_Dim fix: slices per volume, not total files
- 30+ extracted CSV fields with units
- Auto-overwrite mode (no prompts)
- PyInstaller support for standalone executables
- Build scripts for Windows and Linux
- Comprehensive documentation (README, BUILD_GUIDE, CHANGELOG)
- GUI screenshot added
- All test scripts removed"
```

**Or use a shorter commit message**:

```bash
git commit -m "v2.0.0: Python rewrite with GUI, MOSAIC support, and advanced DICOM features"
```

---

### 5. Push to GitHub

#### If this is your first push:

```bash
# Create a new repository on GitHub first (e.g., yourusername/Dicom-Info-Gatherer)
# Then:
git remote add origin https://github.com/yourusername/Dicom-Info-Gatherer.git
git branch -M main
git push -u origin main
```

#### If you've already pushed before:

```bash
git push origin main
```

Or simply:

```bash
git push
```

---

## 🏷️ Creating a Release (Optional)

After pushing, create a GitHub release:

### On GitHub Website:

1. Go to your repository: `https://github.com/yourusername/Dicom-Info-Gatherer`
2. Click **"Releases"** → **"Create a new release"**
3. **Tag version**: `v2.0.0`
4. **Release title**: `v2.0.0 - Major Python Rewrite`
5. **Description**: Copy from `CHANGELOG.md`
6. **Attach binaries** (optional): Upload pre-built executables
   - `DICOM-Info-Gatherer.exe` (Windows)
   - `DICOM-Info-Gatherer` (Linux)
7. Click **"Publish release"**

### Using Git Tags:

```bash
# Create an annotated tag
git tag -a v2.0.0 -m "v2.0.0: Major Python rewrite with GUI and MOSAIC support"

# Push the tag
git push origin v2.0.0

# Or push all tags
git push --tags
```

---

## 🔄 Future Updates

For subsequent changes:

1. **Make changes** to files
2. **Test thoroughly**
3. **Update CHANGELOG.md** with new version
4. **Stage changes**: `git add <files>`
5. **Commit**: `git commit -m "Descriptive message"`
6. **Push**: `git push`

---

## 🐛 Troubleshooting

### "fatal: remote origin already exists"
```bash
# Check current remote
git remote -v

# If wrong URL, update it
git remote set-url origin https://github.com/yourusername/Dicom-Info-Gatherer.git
```

### "failed to push some refs"
```bash
# Pull latest changes first
git pull origin main --rebase

# Then push
git push origin main
```

### Accidentally committed wrong files
```bash
# Remove file from staging (before commit)
git reset HEAD <file>

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes) - CAREFUL!
git reset --hard HEAD~1
```

### Need to ignore already-tracked files
```bash
# Remove from Git tracking but keep local file
git rm --cached <file>

# Then commit
git commit -m "Remove file from tracking"
```

---

## 📝 Commit Message Best Practices

### Good Commit Messages:
```
✅ "Fix Z_Dim calculation for MOSAIC sequences"
✅ "Add Multiband factor extraction from CSA headers"
✅ "Update README with GUI screenshot and installation guide"
✅ "v2.0.0: Major Python rewrite with GUI and advanced features"
```

### Bad Commit Messages:
```
❌ "fixed stuff"
❌ "update"
❌ "asdfasdf"
❌ "trying to fix bug"
```

### Format:
```
<type>: <short summary>

<optional detailed description>

<optional issue references>
```

**Types**: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

**Example**:
```
feat: Add Siemens MOSAIC format support

- Detect MOSAIC tag in ImageType
- Extract true acquisition matrix from AcquisitionMatrix
- Prevent dimension sampling from overwriting MOSAIC corrections
- Add Z_Dim preservation for multi-slice mosaic images

Fixes #42
```

---

## 🎉 You're Done!

Your changes are now on GitHub. Share the repository link:
```
https://github.com/yourusername/Dicom-Info-Gatherer
```

Users can now:
- Clone your repository
- Download releases
- Report issues
- Contribute improvements

---

## 📚 Additional Resources

- [GitHub Docs: Adding Files](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository)
- [Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

**Happy coding! 🚀**
