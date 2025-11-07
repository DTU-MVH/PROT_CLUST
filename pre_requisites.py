import subprocess
import sys
import importlib.util

def check_and_install_prerequisites(libraries):
    """
    Checks if required Python libraries are installed. 
    If not, it installs them using pip.
    
    Args:
        libraries (list): A list of library names (e.g., ['gdown', 'pandas']).
    """
    print("--- 🛠️ Checking and installing prerequisites...")
    
    # List to track packages that needed installation
    packages_to_install = []

    for package in libraries:
        # Use importlib.util.find_spec to check if a package is available
        spec = importlib.util.find_spec(package)
        
        if spec is None:
            print(f"Library '{package}' not found. Preparing to install...")
            packages_to_install.append(package)
        else:
            print(f"Library '{package}' is already installed. Skipping.")

    if packages_to_install:
        print("\nAttempting to install missing packages...")
        
        # Build the pip install command
        install_command = [sys.executable, "-m", "pip", "install"] + packages_to_install
        
        try:
            # Execute the installation command
            process = subprocess.run(
                install_command, 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            print("\n✅ Installation successful:")
            # Display only a summary of the installation output
            print(process.stdout[-500:]) 
            
        except subprocess.CalledProcessError as e:
            print(f"\n❌ ERROR during installation of: {', '.join(packages_to_install)}")
            print(f"Pip Error Output:\n{e.stderr}")
            sys.exit(1) # Exit if installation fails

    print("\nPrerequisite check complete.")


#### main execution #####
# Manually defined list of required libraries
REQUIRED_LIBRARIES = ['gdown']
    
# If you later use pandas, numpy, etc., you would change this to:
# REQUIRED_LIBRARIES = ['gdown', 'pandas', 'numpy'] 
    
check_and_install_prerequisites(REQUIRED_LIBRARIES)