import subprocess
import sys
from pathlib import Path

def run_script(script_name):
    """
    Executes a Python script using a subprocess and checks for errors.
    """
    print(f"\n--- 🚀 Starting {script_name}...")
    
    # Use the current Python executable to run the script
    command = [sys.executable, script_name]
    
    try:
        # Execute the script
        process = subprocess.run(
            command, 
            check=True,  # Raise a CalledProcessError if the script returns a non-zero exit code
            # Inherit standard I/O so you see the output of pre_requisites.py and data_import.py
            # in the main console
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        print(f"--- ✅ {script_name} finished successfully.")
        
    except subprocess.CalledProcessError as e:
        print(f"\n--- ❌ ERROR: {script_name} failed with return code {e.returncode}.")
        print("Please check the error output above for details.")
        sys.exit(e.returncode) # Exit the main script with the error code


if __name__ == "__main__":
    
    # Define the path to the data_import script relative to main.py
    DATA_IMPORT_PATH = Path("features") / "data_import.py"
    
    # Check if the data_import file actually exists at the expected location
    if not DATA_IMPORT_PATH.exists():
        print(f"\nFATAL ERROR: Could not find script at '{DATA_IMPORT_PATH}'")
        print("Please ensure the 'features' folder and 'data_import.py' exist.")
        sys.exit(1)
    
    # 1. Run the prerequisite check first
    run_script("pre_requisites.py")
    
    # 2. Run the data import script next using the full relative path
    run_script(str(DATA_IMPORT_PATH))
    
    print("\n\n✨ All project setup tasks complete! ✨")