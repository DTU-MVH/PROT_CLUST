import os
import sys
import subprocess
import platform
from pathlib import Path

# Define the project structure based on your screenshot
PROJECT_STRUCTURE = [
    "_raw",
    "data",
    "data/output",
    "features",
    "features/plotting",
    ".venv" # We will handle this specifically
]

def create_structure():
    print(f"📁 Setting up directory structure for PROT_CLUST...")
    
    root_dir = Path(__file__).parent
    
    for folder in PROJECT_STRUCTURE:
        folder_path = root_dir / folder
        if not folder_path.exists():
            print(f"   + Creating missing directory: {folder}/")
            os.makedirs(folder_path, exist_ok=True)
        else:
            print(f"   ✓ Directory exists: {folder}/")

def setup_virtual_env():
    """Checks for .venv and creates it if missing."""
    print(f"\n🐍 Checking Virtual Environment...")
    venv_path = Path(__file__).parent / ".venv"
    
    if not venv_path.exists():
        print("   + Creating virtual environment (.venv)...")
        try:
            subprocess.check_call([sys.executable, "-m", "venv", ".venv"])
            print("   ✓ Virtual environment created.")
        except subprocess.CalledProcessError:
            print("   ! Failed to create virtual environment.")
            return False
    else:
        print("   ✓ Virtual environment already exists.")
    return True

def install_requirements():
    """Installs pip packages if requirements.txt exists."""
    print(f"\n📦 Checking dependencies...")
    req_file = Path(__file__).parent / "requirements.txt"
    
    # Determine the pip executable inside the venv
    is_windows = platform.system() == "Windows"
    pip_executable = Path(".venv") / ("Scripts" if is_windows else "bin") / "pip"
    
    if req_file.exists():
        if pip_executable.exists():
            print(f"   + Installing requirements from {req_file.name}...")
            try:
                subprocess.check_call([str(pip_executable), "install", "-r", "requirements.txt"])
                print("   ✓ Dependencies installed successfully.")
            except subprocess.CalledProcessError:
                print("   ! Error installing dependencies.")
        else:
            print("   ! Could not find pip in .venv. Make sure the environment was created correctly.")
    else:
        print("   ? No 'requirements.txt' found. Skipping dependency installation.")
        print("     (Run 'pip freeze > requirements.txt' to generate this file).")

def check_data_files():
    """Reminds the user about the missing ignored data files."""
    print(f"\n💾 Data File Check...")
    
    # Based on your screenshot, these appear to be STRING DB files
    required_files = [
        Path("_raw/9606.protein.info.v12.0.txt"),
        Path("_raw/9606.protein.links.v12.0.min400.txt") # Assuming the truncated name
    ]
    
    missing_data = [f for f in required_files if not f.exists()]
    
    if missing_data:
        print("   ! The following data files are missing (due to .gitignore):")
        for f in missing_data:
            print(f"     - {f}")
        print("\n   ℹ️  ACTION REQUIRED: Please download the organism data (9606/Human)")
        print("       from the STRING database (string-db.org) or run 'raw_data.py'")
        print("       if it contains a download script.")
    else:
        print("   ✓ Required raw data files are present.")

if __name__ == "__main__":
    print("========================================")
    print("   PROT_CLUST Environment Setup Tool    ")
    print("========================================")
    
    create_structure()
    if setup_virtual_env():
        install_requirements()
    check_data_files()
    
    print("\n✅ Setup complete! To activate your environment:")
    if platform.system() == "Windows":
        print("   > .venv\\Scripts\\activate")
    else:
        print("   > source .venv/bin/activate")