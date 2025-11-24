import ast
import sys
import subprocess
import importlib.util
import os

# ==============================================================================
# 1. CONFIGURATION SECTION
# ==============================================================================

# LIST OF FILES TO CHECK:
# Add the names of the python scripts you want to check prerequisites for here.
# Example: FILES_TO_CHECK = ["main_script.py", "data_processor.py"]
FILES_TO_CHECK = [
    "features/data_import.py",
    "features/preprocessing.py", 
    "features/lovain_clustering.py",
    "features/markov_clustering_highperformance.py",
    "features/louvain_clust_object_out.py"
]

# LIBRARY NAME MAPPING:
# Sometimes the name you type in 'import' is different from the name you use to 'pip install'.
# We verify standard imports automatically, but specific exceptions go here.
# Format: "import_name": "pip_package_name"
CUSTOM_PACKAGE_MAPPING = {
    "cv2": "opencv-python",       # 'import cv2' requires 'pip install opencv-python'
    "sklearn": "scikit-learn",    # 'import sklearn' requires 'pip install scikit-learn'
    "PIL": "Pillow",              # 'import PIL' requires 'pip install Pillow'
    "yaml": "PyYAML",             # 'import yaml' requires 'pip install PyYAML'
    "bs4": "beautifulsoup4",      # 'import bs4' requires 'pip install beautifulsoup4'
    "dotenv": "python-dotenv",    # 'import dotenv' requires 'pip install python-dotenv'
    "dateutil": "python-dateutil" # 'import dateutil' requires 'pip install python-dateutil'
}

# ==============================================================================
# 2. HELPER FUNCTIONS (The Logic)
# ==============================================================================

def get_imports_from_file(filepath):
    """
    Reads a Python file and uses the 'ast' (Abstract Syntax Tree) module
    to find every library that is imported.
    
    Why 'ast'? Because parsing text with Regex is unreliable (e.g., imports 
    inside comments would be detected wrongly). AST understands the code structure.
    """
    if not os.path.exists(filepath):
        print(f"Warning: The file '{filepath}' was not found. Skipping.")
        return set()

    # Open the file and read its content
    with open(filepath, "r", encoding="utf-8") as file:
        try:
            # Parse the code structure
            tree = ast.parse(file.read(), filename=filepath)
        except SyntaxError as e:
            print(f"Syntax Error in {filepath}: {e}")
            return set()

    imports = set()
    
    # Walk through every 'node' (line/instruction) in the code tree
    for node in ast.walk(tree):
        
        # Case 1: standard imports (e.g., "import os", "import pandas as pd")
        if isinstance(node, ast.Import):
            for alias in node.names:
                # split('.')[0] ensures we get 'matplotlib' from 'matplotlib.pyplot'
                imports.add(alias.name.split('.')[0]) 
        
        # Case 2: from imports (e.g., "from math import sqrt")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split('.')[0])

    return imports

def is_standard_library(module_name):
    """
    Checks if the module is built into Python (like 'os', 'sys', 'math').
    We should NOT try to pip install these.
    """
    # Python 3.10+ has a list of standard libraries we can check
    if sys.version_info >= (3, 10):
        if module_name in sys.stdlib_module_names:
            return True
    
    # Fallback check for built-in modules
    return module_name in sys.builtin_module_names

def is_installed(module_name):
    """
    Checks if a library is currently installed in the environment.
    It tries to find the module specification without actually running it.
    """
    try:
        spec = importlib.util.find_spec(module_name)
        return spec is not None
    except (ModuleNotFoundError, ValueError):
        return False

def install_package(package_name):
    """
    Runs the pip command to install the missing package.
    We use sys.executable to ensure we install it for the CURRENT Python version running this script.
    """
    print(f"   -> Installing package: {package_name}...")
    try:
        # Equivalent to running: python -m pip install package_name
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"   -> Successfully installed {package_name}")
    except subprocess.CalledProcessError:
        print(f"   -> ERROR: Failed to install {package_name}. Check your internet or permissions.")

# ==============================================================================
# 3. MAIN EXECUTION
# ==============================================================================

def main():
    print("--- Starting Prerequisite Check ---")
    
    all_imports = set()

    # STEP 1: Collect all imports from all files listed at the top
    for script in FILES_TO_CHECK:
        print(f"Scanning file: {script}")
        found = get_imports_from_file(script)
        all_imports.update(found)

    print(f"\nAll imports detected: {', '.join(sorted(all_imports))}")
    print("-" * 40)

    # STEP 2: Process each import
    for module in sorted(all_imports):
        
        # Skip Standard Library modules (os, sys, json, etc.)
        if is_standard_library(module):
            continue

        # Skip Local Files (e.g., if you import 'my_helper' and 'my_helper.py' exists locally)
        if os.path.exists(f"{module}.py"):
            print(f"✔ '{module}' is a local file.")
            continue

        # Determine the package name to install.
        # Use the mapping at the top if it exists, otherwise assume package name = import name.
        package_to_install = CUSTOM_PACKAGE_MAPPING.get(module, module)

        # STEP 3: Check if installed, if not, install it
        if is_installed(module):
            print(f"✔ '{module}' is satisfied.")
        else:
            print(f"✘ '{module}' is MISSING. Starting installation...")
            install_package(package_to_install)

    print("-" * 40)
    print("Done. You can now run your scripts.")


main()