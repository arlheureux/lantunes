#!/usr/bin/env python3
import sys
import os
import subprocess
import shutil
import pkg_resources

project_root = os.path.dirname(os.path.abspath(__file__))
venv_path = os.path.join(project_root, 'venv')
venv_python = os.path.join(venv_path, 'bin', 'python')
pip_path = os.path.join(venv_path, 'bin', 'pip')

# All required dependencies
REQUIRED_DEPS = [
    'fastapi', 'uvicorn', 'sqlalchemy', 'mutagen', 'pyyaml', 
    'python-multipart', 'websockets', 'requests', 'PyJWT', 'passlib', 'bcrypt'
]

def get_installed_packages():
    """Get list of installed packages"""
    try:
        return {pkg.key for pkg in pkg_resources.working_set}
    except Exception:
        return set()

def install_missing_packages():
    """Install any missing required packages"""
    installed = get_installed_packages()
    missing = [dep for dep in REQUIRED_DEPS if dep.lower() not in installed]
    
    if missing:
        print(f"Installing missing packages: {', '.join(missing)}")
        subprocess.run([pip_path, 'install'] + missing, cwd=project_root)
    else:
        print("All dependencies already installed.")

# Check if running in our venv
in_venv = sys.prefix != sys.base_prefix or os.path.basename(sys.prefix) == 'venv'

if not in_venv:
    if os.path.exists(venv_python):
        # Check and install missing packages before running
        install_missing_packages()
        os.execv(venv_python, [venv_python] + sys.argv)
    else:
        print("Creating virtual environment...")
        subprocess.run([sys.executable, '-m', 'venv', venv_path], cwd=project_root)
        
        print("Installing dependencies...")
        subprocess.run([pip_path, 'install'] + REQUIRED_DEPS, cwd=project_root)
        
        os.execv(venv_python, [venv_python] + sys.argv)

# We're in the venv - check for missing packages anyway
install_missing_packages()

sys.path.insert(0, os.path.join(project_root, 'backend'))
os.chdir(project_root)

from main import app
import uvicorn

if __name__ == "__main__":
    print("Starting LanTunes server on http://0.0.0.0:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)