# Building ClawAI Executable

This document provides instructions for building a standalone executable of the ClawAI desktop application.

## Prerequisites

Before building, ensure you have:

1. **Python 3.8+** installed on your system
2. **Node.js and npm** (for frontend build)
3. All Python dependencies listed in `requirements.txt`

## Building Steps

### Method 1: Using the Build Script

Run the provided build script:
```bash
python build_executable.py
```
or 

### Method 2: Manual PyInstaller Command  

Make sure you're in the project root directory and run:

```bash
# Install dependencies if not already installed  
pip install -r requirements.txt

# Ensure frontend is built (if needed)
cd frontend && npm run build && cd ..

# Build with PyInstaller 
pyinstaller --clean --onefile --windowed --name=ClawAI-Studio main.py
```

### Method 3: Using the Batch Script  

Run `simple_build.bat` which will:
1. Check if frontend is built  
2. Install required packages
3. Create executable using PyInstaller

## Build Configuration 

The build process includes:

- All Python source files from clawaii and clawai directories 
- Frontend static assets (`frontend/dist/**/*`)
- Environment configuration files (`.env`, `config.json`) 
- Required dependencies specified in `requirements.txt`
- Proper handling of FastAPI, PyWebView, and other components

## Output Location 

The built executable will be located at:
```
dist/ClawAI-Studio.exe
```

## Troubleshooting  

If you encounter issues:

1. **Missing frontend files**: Ensure the React app is built with `npm run build` 
2. **Import errors**: Check that all dependencies are installed via pip  
3. **Path issues**: Make sure to run commands from project root directory

## Notes 

- The executable will include a bundled Python interpreter
- All required libraries and modules are included in the single file
- For debugging, you can build with `console=True` instead of `--windowed`