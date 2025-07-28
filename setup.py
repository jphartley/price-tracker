#!/usr/bin/env python3
"""
Setup script for Price Tracker application
This script sets up the development environment for both backend and frontend
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, cwd=None, description=""):
    """Run a shell command and handle errors"""
    print(f"Running: {description or command}")
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, check=True, 
                              capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False

def setup_backend():
    """Set up the backend environment"""
    print("\n=== Setting up Backend ===")
    backend_dir = Path("backend")
    
    if not backend_dir.exists():
        print("Backend directory not found!")
        return False
    
    # Create virtual environment if it doesn't exist
    venv_dir = backend_dir / "venv"
    if not venv_dir.exists():
        if not run_command("python -m venv backend/venv", description="Creating virtual environment"):
            return False
    
    # Install requirements
    if sys.platform == "win32":
        pip_path = "backend/venv/Scripts/pip"
        python_path = "backend/venv/Scripts/python"
    else:
        pip_path = "backend/venv/bin/pip"
        python_path = "backend/venv/bin/python"
    
    if not run_command(f"{pip_path} install -r backend/requirements.txt", 
                      description="Installing Python dependencies"):
        return False
    
    # Install Playwright browsers
    if not run_command(f"{python_path} -m playwright install", 
                      description="Installing Playwright browsers"):
        return False
    
    print("✅ Backend setup complete!")
    return True

def setup_frontend():
    """Set up the frontend environment"""
    print("\n=== Setting up Frontend ===")
    frontend_dir = Path("frontend")
    
    if not frontend_dir.exists():
        print("Frontend directory not found!")
        return False
    
    # Install npm dependencies
    if not run_command("npm install", cwd="frontend", 
                      description="Installing Node.js dependencies"):
        return False
    
    print("✅ Frontend setup complete!")
    return True

def main():
    """Main setup function"""
    print("🚀 Setting up Price Tracker Application")
    
    # Check if we're in the right directory
    if not Path("backend").exists() or not Path("frontend").exists():
        print("❌ Please run this script from the project root directory")
        print("   Expected structure: project_root/backend and project_root/frontend")
        sys.exit(1)
    
    # Setup backend
    if not setup_backend():
        print("❌ Backend setup failed!")
        sys.exit(1)
    
    # Setup frontend
    if not setup_frontend():
        print("❌ Frontend setup failed!")
        sys.exit(1)
    
    print("\n🎉 Setup complete!")
    print("\nTo start the application:")
    print("1. Backend:  cd backend && ./venv/bin/python main.py")
    print("2. Frontend: cd frontend && npm run dev")
    print("\nThe backend will run on http://localhost:8000")
    print("The frontend will run on http://localhost:5173")

if __name__ == "__main__":
    main()