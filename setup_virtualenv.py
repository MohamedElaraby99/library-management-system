#!/usr/bin/env python3
"""
Virtualenv setup script for PythonAnywhere deployment
"""

import os
import subprocess
import sys

def setup_virtualenv():
    """Set up virtualenv for the project"""
    print("🔧 Setting up virtualenv...")
    
    # Get the project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create virtualenv if it doesn't exist
    venv_dir = os.path.join(project_dir, 'venv')
    if not os.path.exists(venv_dir):
        print("Creating virtualenv...")
        subprocess.run([sys.executable, '-m', 'venv', venv_dir], check=True)
    
    # Activate virtualenv and install requirements
    if os.name == 'nt':  # Windows
        activate_script = os.path.join(venv_dir, 'Scripts', 'activate')
        pip_path = os.path.join(venv_dir, 'Scripts', 'pip')
    else:  # Unix/Linux
        activate_script = os.path.join(venv_dir, 'bin', 'activate')
        pip_path = os.path.join(venv_dir, 'bin', 'pip')
    
    # Install requirements
    print("Installing requirements...")
    subprocess.run([pip_path, 'install', '--upgrade', 'pip'], check=True)
    subprocess.run([pip_path, 'install', '-r', 'requirements.txt'], check=True)
    
    print("✅ Virtualenv setup completed successfully!")
    print(f"\nVirtualenv path: {venv_dir}")
    print("\nTo activate the virtualenv:")
    if os.name == 'nt':
        print(f"    {venv_dir}\\Scripts\\activate")
    else:
        print(f"    source {venv_dir}/bin/activate")

if __name__ == '__main__':
    setup_virtualenv() 