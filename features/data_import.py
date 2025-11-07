import os
from pathlib import Path
import sys

# --- Configuration ---
# Your specific File ID for 'data_file_protein.tsv'
TARGET_FILE_ID = '1frPiLnGVfVNmmpr0IhX5qUp_kYRB1bQg' 
TARGET_FILENAME = "data_file_protein.tsv"
# ---------------------

# NOTE: This script requires the 'gdown' library, which should be checked by pre_requisites.py
try:
    import gdown
except ImportError:
    print("The 'gdown' library is not installed. Please run pre_requisites.py first.")
    # Exit with a system error code to stop main.py cleanly
    sys.exit(1)


def setup_project_folders():
    """
    1. Creates the _raw and data folders in the project directory if they don't exist.
    """
    print("--- 📂 Setting up project folders...")
    
    # Define the folders relative to the project root
    raw_folder = Path("_raw")
    data_folder = Path("data")
    
    # Create folders: exist_ok=True prevents errors if they already exist.
    raw_folder.mkdir(exist_ok=True)
    data_folder.mkdir(exist_ok=True)
    
    print(f"Created/ensured folder: {raw_folder.resolve()}")
    print(f"Created/ensured folder: {data_folder.resolve()}")
    print("Folders setup complete.\n")
    
    # Return the data folder path, as this is the final destination for the file
    return raw_folder


def import_google_drive_data(target_folder: Path):
    """
    2. Imports the specified file from Google Drive into the local data folder.
    """
    print(f"--- ⬇️ Importing Google Drive file: {TARGET_FILENAME}...")
    
    # Define the full local path where the file should be saved
    output_path = target_folder / TARGET_FILENAME
    
    try:
        # Use gdown.download() for a single file. 
        # Using minimal arguments to ensure compatibility with various gdown versions.
        gdown.download(
            id=TARGET_FILE_ID,
            output=str(output_path),
            quiet=False, # Show progress
            use_cookies=False, 
        )
        print("\n✅ Data import successful!")
        print(f"File downloaded to: {output_path.resolve()}")
        
    except Exception as e:
        print("\n❌ Error during data import!")
        print("Please ensure the specific file is set to 'Anyone with the link' (Viewer).")
        print(f"Error details: {e}")
        # Use raise to propagate the error back to main.py's subprocess handler
        raise 


if __name__ == "__main__":
    
    # 1. Create the necessary folders and get the target directory (data folder)
    target_data_folder = setup_project_folders()
    
    # 2. Import the single file into the 'data' folder
    import_google_drive_data(target_data_folder)