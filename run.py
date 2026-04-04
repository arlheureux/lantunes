#!/usr/bin/env python3
import sys
import os
import subprocess
import shutil

project_root = os.path.dirname(os.path.abspath(__file__))
venv_path = os.path.join(project_root, 'venv')
venv_python = os.path.join(venv_path, 'bin', 'python')

in_venv = sys.prefix != sys.base_prefix or os.path.basename(sys.prefix) == 'venv'

if not in_venv:
    if os.path.exists(venv_python):
        os.execv(venv_python, [venv_python] + sys.argv)
    else:
        print("Creating virtual environment...")
        subprocess.run([sys.executable, '-m', 'venv', 'venv'], cwd=project_root)
        
        print("Installing dependencies...")
        pip_path = os.path.join(venv_path, 'bin', 'pip')
        deps = ['fastapi', 'uvicorn', 'sqlalchemy', 'mutagen', 'pyyaml', 'python-multipart']
        subprocess.run([pip_path, 'install'] + deps, cwd=project_root)
        
        os.execv(venv_python, [venv_python] + sys.argv)

sys.path.insert(0, os.path.join(project_root, 'backend'))
os.chdir(project_root)

from main import app
import uvicorn

if __name__ == "__main__":
    print("Starting LanTunes server on http://0.0.0.0:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)