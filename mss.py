import os
import sys
import subprocess
import yaml

# Path to the virtual environment
#VENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv")
VENV_PATH = "/opt/venv/MacSambaSync"
# Path to the config.yaml file
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")

def create_venv():
    """
    Ensures a virtual environment exists at VENV_PATH.
    If it does not exist, creates it.
    """
    try:
        if not os.path.exists(VENV_PATH):
            print(f"Virtual environment not found at {VENV_PATH}. Creating one...")
            subprocess.check_call([sys.executable, "-m", "venv", VENV_PATH])
            print("Virtual environment created successfully.")
        else:
            print(f"Virtual environment already exists at {VENV_PATH}.")
    except Exception as e:
        print(f"Error creating virtual environment: {e}")
        sys.exit(1)

def load_config():
    """
    Loads the configuration from the config.yaml file.
    Ensures the file exists and is valid YAML.
    """
    try:
        if not os.path.exists(CONFIG_FILE):
            raise FileNotFoundError(f"Configuration file not found: {CONFIG_FILE}")
        
        with open(CONFIG_FILE, "r") as f:
            config = yaml.safe_load(f)
        
        if not isinstance(config, dict):
            raise ValueError("Configuration file must contain a valid dictionary.")
        
        print("Configuration loaded successfully.")
        return config
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)

def ensure_venv_activation():
    """
    Ensures that the script is executed using the Python interpreter from the venv.
    """
    if sys.prefix != VENV_PATH:
        print(f"Script is not using the virtual environment at {VENV_PATH}.")
        print("Please activate the venv or run the script with the venv Python interpreter.")
        print(f"Example: {os.path.join(VENV_PATH, 'bin', 'python')} {__file__}")
        sys.exit(1)

def main():
    """
    Main function of the script.
    Ensures a venv is configured, configuration is loaded, and the script is executed within the venv.
    """
    print("Starting script...")
    
    # Ensure the virtual environment exists
    create_venv()
    
    # Ensure the script is running within the venv
    ensure_venv_activation()
    
    # Load the configuration
    config = load_config()
    
    # Success message
    print("Script executed successfully!")

if __name__ == "__main__":
    main()