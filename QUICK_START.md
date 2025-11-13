# 🚀 Quick Start Guide

## 选择你的使用方式：

---

## 方法 1️⃣: 使用源代码（推荐开发）

### 安装依赖
```bash
pip install -r requirements.txt
```

### 启动GUI
```bash
python process_dicom.py --gui
```

### 命令行使用
```bash
python process_dicom.py "你的DICOM文件夹路径"
```

---

## 方法 2️⃣: 编译成可执行文件（推荐分发）

### Windows
双击运行或命令行：
```cmd
build_windows.bat
```
输出：`release\DICOM-Info-Gatherer.exe`

### Linux
```bash
chmod +x build_linux.sh
./build_linux.sh
```
输出：`release/DICOM-Info-Gatherer`

---

## 📤 GitHub 提交步骤

```bash
# 1. 检查状态
git status

# 2. 添加所有文件
git add -A

# 3. 提交
git commit -m "v2.0.0: Python rewrite with GUI and MOSAIC support"

# 4. 推送到GitHub
git push origin main
```

详细说明见：[GIT_COMMIT_GUIDE.md](GIT_COMMIT_GUIDE.md)

---

## 📋 完整文件清单

### ✅ 核心文件（需要提交）
- `process_dicom.py` - 主程序
- `run_dcm2niix.py` - dcm2niix辅助脚本
- `requirements.txt` - Python依赖
- `README.md` - 项目文档
- `CHANGELOG.md` - 更新日志
- `BUILD_GUIDE.md` - 构建指南
- `GIT_COMMIT_GUIDE.md` - Git提交指南
- `QUICK_START.md` - 本文件
- `.gitignore` - Git忽略规则
- `GUI.png` - GUI截图
- `build_windows.bat` - Windows构建脚本
- `build_linux.sh` - Linux构建脚本

### ❌ 已删除（测试脚本）
- 所有 `test_*.py`, `check_*.py`, `debug_*.py` 等

### 🚫 不提交（自动忽略）
- `__pycache__/`, `build/`, `dist/`, `release/`
- `*_CSV/`, `*_nii/`, `*_summary.csv`

---

## 🎯 输出文件说明

运行后生成：

```
你的DICOM文件夹/
├── 1_localizer/
├── 32_ep2d_gslider_p8mmiso_b2000/
├── ...
├── 你的DICOM文件夹_CSV/
│   └── 文件夹名_summary.csv  ← 主要输出
└── 你的DICOM文件夹_nii/  (如果启用dcm2niix)
    └── ...
```

---

## ⚙️ 主要功能

✅ **CSV生成** - 30+个DICOM参数提取  
✅ **并行处理** - 多线程加速  
✅ **MOSAIC支持** - Siemens gSlider序列  
✅ **Multiband检测** - 从CSA头提取SMS因子  
✅ **Diffusion MRI** - b值、体积数、b0计数  
✅ **自动覆盖** - 无需确认，直接清空旧输出  

---

## 🐛 常见问题

**GUI无法启动？**
```bash
# Linux安装tkinter
sudo apt-get install python3-tk
```

**dcm2niix未找到？**
- 下载：https://github.com/rordenlab/dcm2niix/releases
- 或指定路径：`--dcm2niix-path "/path/to/dcm2niix"`

**Z_Dim不正确？**
- 检查是否为MOSAIC格式（日志会显示"MOSAIC detected"）
- 确认DICOM文件完整且未损坏

---

## 📞 获取帮助

```bash
python process_dicom.py --help
```

或查看完整文档：
- [README.md](README.md) - 详细使用说明
- [BUILD_GUIDE.md](BUILD_GUIDE.md) - 构建可执行文件
- [CHANGELOG.md](CHANGELOG.md) - 版本历史

---

**祝使用愉快！🎉**

