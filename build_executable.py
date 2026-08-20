#!/usr/bin/env python3
"""
Build script for ClawAI desktop application.
This creates a standalone executable with all dependencies included.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, cwd=None):
    """Run a shell command and return the result."""
    print(f"Running: {' '.join(command) if isinstance(command, list) else command}")
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        print("Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed with exit code {e.returncode}: {e.stderr}")
        return False

def build_frontend():
    """Build the React frontend."""
    print("\n=== Building Frontend ===")
    
    # Check if npm is available
    if not run_command(["npm", "--version"]):
        print("Error: npm is required but not found. Please install Node.js.")
        return False
    
    # Build the frontend using npm
    result = run_command(["npm", "run", "build"], cwd="D:\\ClawAI")
    
    if not result:
        print("Frontend build failed!")
        return False
        
    print("\nFrontend built successfully!\n")
    return True

def check_frontend_exists():
    """Check if the frontend dist directory exists."""
    dist_path = Path("D:/ClawAI/frontend/dist") 
    return dist_path.exists() and (dist_path / "index.html").exists()

def build_executable():
    """Build the executable using PyInstaller."""
    print("\n=== Building Executable ===")
    
    # Check if frontend is built
    if not check_frontend_exists():
        print("Frontend distribution files not found. Attempting to build...")
        if not build_frontend():
            return False
    
    # Install required packages for building (if needed)
    try:
        import PyInstaller
    except ImportError:
        print("\nInstalling PyInstaller...")
        run_command([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Create the executable using our spec file  
    result = run_command([
        sys.executable, "-m", "PyInstaller", 
        "--clean",
        "--onefile",
        "--windowed",  # Hide console window for desktop app
        "--name=ClawAI-Studio",
        "--icon=frontend/src/assets/icon.ico",  # If icon exists  
        "clawai.spec"
    ], cwd="D:\\ClawAI")
    
    if result:
        print("\n✅ Executable built successfully!")
        print("The executable is located in the 'dist' folder.")
        
        # Show where it was created
        exe_path = Path("D:/ClawAI/dist/ClawAI-Studio.exe") 
        if exe_path.exists():
            print(f"Executable location: {exe_path.absolute()}")
            
    return result

def main():
    """Main build function."""
    print("Starting ClawAI executable builder...")
    
    # Change to project directory
    os.chdir("D:\\ClawAI")
    
    try:
        success = build_executable()
        
        if success:
            print("\n🎉 Build completed successfully!")
            return 0
        else:
            print("\n❌ Build failed.")
            return 1
            
    except Exception as e:
        print(f"\n💥 Unexpected error during build: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())