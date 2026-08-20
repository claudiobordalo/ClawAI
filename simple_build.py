import subprocess
import sys

# Simple build script for ClawAI 
print("Starting basic executable build...")

try:
    # Change to project directory first  
    result = subprocess.run([
        "pyinstaller", "--clean", "--onefile",
        "--windowed", "--name=ClawAI-Studio", 
        "main.py"
    ], cwd="D:\\ClawAI", check=True)
    
    print("Build completed successfully!")
except Exception as e:
    print(f"Error during build: {e}")