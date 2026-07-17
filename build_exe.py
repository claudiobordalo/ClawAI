"""
build_exe.py – Script de build para criar o executável standalone da ClawAI Desktop.

Build:
    python build_exe.py          # Single-file exe
    python build_exe.py --dir    # Single-directory output

Output:
    dist/ClawAI.exe              (single-file)
    dist/ClawAI/ClawAI.exe       (single-directory)
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT / "frontend"
DIST_DIR = FRONTEND_DIR / "dist"
CLAWAI_DIR = ROOT / "clawai"
PYINSTALLER_SPEC = ROOT / "ClawAI.spec"


def check_prerequisites():
    """Check that all prerequisites are available."""
    errors = []

    # Check Python version
    if sys.version_info < (3, 10):
        errors.append("Python 3.10+ is required")

    # Check npm
    npm_cmd = shutil.which("npm")
    if not npm_cmd:
        # Try common Windows paths
        for path in [
            r"C:\Program Files\nodejs\npm.cmd",
            r"C:\Program Files (x86)\nodejs\npm.cmd",
            os.path.expanduser("~\\AppData\\Local\\Programs\\Node.js\\npm.cmd"),
        ]:
            if os.path.exists(path):
                npm_cmd = path
                break
        if not npm_cmd:
            errors.append("npm not found. Install Node.js from https://nodejs.org/")

    # Check pip packages
    for pkg in ["pyinstaller", "fastapi", "uvicorn", "httpx", "psutil"]:
        try:
            __import__(pkg.replace("-", "_"))
        except ImportError:
            errors.append(f"{pkg} not installed. Run: pip install {pkg}")

    if errors:
        print("❌ Prerequisites not met:")
        for err in errors:
            print(f"   - {err}")
        return False
    return True


def build_frontend():
    """Build the React frontend."""
    print("\n[1/4] Building frontend...")

    npm_cmd = shutil.which("npm") or "npm"
    result = subprocess.run(
        [npm_cmd, "run", "build"],
        cwd=str(FRONTEND_DIR),
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        print(f"❌ Frontend build failed:\n{result.stderr[:500]}")
        return False

    if not DIST_DIR.exists():
        print("❌ Frontend build completed but dist/ not found")
        return False

    print(f"✅ Frontend built ({len(list(DIST_DIR.rglob('*')))} files)")
    return True


def install_dependencies():
    """Install Python dependencies."""
    print("\n[2/4] Installing Python dependencies...")

    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", "."],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        print(f"❌ Dependency install failed:\n{result.stderr[:500]}")
        return False

    print("✅ Dependencies installed")
    return True


def run_pyinstaller(single_file: bool = True):
    """Run PyInstaller to create the executable."""
    print("\n[3/4] Running PyInstaller...")

    # Clean previous build
    dist_dir = ROOT / "dist"
    if dist_dir.exists():
        shutil.rmtree(dist_dir)

    # Build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        "--name", "ClawAI",
    ]

    if single_file:
        cmd.append("--onefile")
        output_name = "ClawAI.exe"
    else:
        cmd.append("--onedir")
        output_name = "ClawAI"

    cmd.append("--windowed")
    cmd.append("--icon=frontend/public/icon.ico")  # Optional icon

    # Add data files
    if DIST_DIR.exists():
        cmd.extend(["--add-data", f"{DIST_DIR}{os.pathsep}frontend/dist"])
    cmd.extend(["--add-data", f"{CLAWAI_DIR}{os.pathsep}clawai"])
    cmd.extend(["--add-data", f"{ROOT / 'configs'}{os.pathsep}configs"])
    cmd.extend(["--add-data", f"{ROOT / 'database'}{os.pathsep}database"])

    # Hidden imports
    for mod in [
        "uvicorn", "fastapi", "httpx", "psutil",
        "webview", "clawai.main", "clawai.server",
        "clawai.bootstrap", "clawai.desktop_server",
    ]:
        cmd.extend(["--hidden-import", mod])

    # Exclusions
    for mod in ["tkinter", "pytest", "sphinx", "jupyter", "IPython"]:
        cmd.extend(["--exclude-module", mod])

    # Entry point
    cmd.append(str(ROOT / "main.py"))

    print(f"  Command: {' '.join(cmd[:5])} ...")

    result = subprocess.run(cmd, cwd=str(ROOT), timeout=300)

    if result.returncode != 0:
        print("❌ PyInstaller failed")
        return None

    # Find the output
    output = dist_dir / output_name
    if single_file:
        return output
    else:
        return output / "ClawAI.exe"


def create_installer(output_exe: Path):
    """Create a simple installer wrapper if needed."""
    print("\n[4/4] Finalizing...")

    if not output_exe.exists():
        print("❌ Output not found")
        return False

    # Add version info if available
    try:
        with open(ROOT / "package.json") as f:
            version = json.load(f).get("version", "1.0.0")
        print(f"  Version: {version}")
    except Exception:
        pass

    print(f"\n✅ Build complete!")
    print(f"   Output: {output_exe}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Build ClawAI Desktop")
    parser.add_argument("--dir", action="store_true", help="Build single-directory instead of single-file")
    parser.add_argument("--skip-frontend", action="store_true", help="Skip frontend build")
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependency install")
    args = parser.parse_args()

    print("=" * 60)
    print("  ClawAI Desktop Build")
    print("=" * 60)

    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)

    # Build frontend
    if not args.skip_frontend:
        if not build_frontend():
            sys.exit(1)

    # Install dependencies
    if not args.skip_deps:
        if not install_dependencies():
            sys.exit(1)

    # Run PyInstaller
    output = run_pyinstaller(single_file=not args.dir)
    if not output:
        sys.exit(1)

    # Finalize
    if not create_installer(output):
        sys.exit(1)

    print("=" * 60)


if __name__ == "__main__":
    main()
