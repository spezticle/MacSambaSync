#!/bin/zsh

# Configuration
VENV_PATH="/opt/venv/MacSambaSync"
PYTHON_EXEC="python3"
REQUIREMENTS_FILE="requirements.txt"
WORKHORSE_SCRIPT="mss.py"

# Text formatting
BOLD_GREEN='\033[1;32m'
BOLD_RED='\033[1;31m'
RESET='\033[0m'

# Check if script is being run as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${BOLD_RED}Do not run this script as root. Exiting...${RESET}"
    exit 1
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check and fix ownership of a specific directory
ensure_ownership() {
    local dir="$1"
    if [ ! -w "$dir" ]; then
        echo -e "${BOLD_RED}No write permission for $dir. Requesting sudo to fix permissions...${RESET}"
        sudo mkdir -p "$dir"  # Only ensure the specific directory exists
        sudo chown -Rv "$USER:`id -gn`" "$dir"  # Apply ownership to the specific directory
        if [ $? -ne 0 ]; then
            echo -e "${BOLD_RED}Failed to set permissions for $dir. Exiting...${RESET}"
            exit 1
        fi
        echo -e "${BOLD_GREEN}Ownership of $dir set to $USER:`id -gn`.${RESET}"
    fi
}

# Ensure Python 3 is available
if ! command_exists $PYTHON_EXEC; then
    echo -e "${BOLD_RED}Python 3 is not installed or not in PATH. Exiting...${RESET}"
    exit 1
fi

# Step 1: Ensure the virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Virtual environment not found at $VENV_PATH. Creating..."
    ensure_ownership "$VENV_PATH"
    $PYTHON_EXEC -m venv "$VENV_PATH"
    if [ $? -ne 0 ]; then
        echo -e "${BOLD_RED}Failed to create virtual environment at $VENV_PATH. Exiting...${RESET}"
        exit 1
    fi
    echo -e "${BOLD_GREEN}Virtual environment created successfully at $VENV_PATH.${RESET}"
else
    echo -e "${BOLD_GREEN}Virtual environment already exists at $VENV_PATH.${RESET}"
    ensure_ownership "$VENV_PATH"
fi

# Step 2: Activate the virtual environment
echo "Activating virtual environment..."
source "$VENV_PATH/bin/activate"

if [ $? -ne 0 ]; then
    echo -e "${BOLD_RED}Failed to activate the virtual environment. Exiting...${RESET}"
    exit 1
fi

# Step 3: Upgrade pip if needed
echo "Checking for pip upgrades..."
pip install --upgrade pip
if [ $? -ne 0 ]; then
    echo -e "${BOLD_RED}Failed to upgrade pip. Continuing with the current version.${RESET}"
else
    echo -e "${BOLD_GREEN}pip is up to date.${RESET}"
fi

# Step 4: Check for dependencies in requirements.txt
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo "Installing dependencies from $REQUIREMENTS_FILE..."
    pip install -r "$REQUIREMENTS_FILE"
    if [ $? -ne 0 ]; then
        echo -e "${BOLD_RED}Failed to install dependencies. Exiting...${RESET}"
        deactivate
        exit 1
    fi
    echo -e "${BOLD_GREEN}Dependencies installed successfully.${RESET}"

    # Step 5: Compare installed modules with requirements.txt
    echo "Checking for extra modules not listed in $REQUIREMENTS_FILE..."
    INSTALLED_MODULES=$(pip freeze | awk -F '==' '{print $1}' | tr '[:upper:]' '[:lower:]')

    if [ -s "$REQUIREMENTS_FILE" ]; then
        # Parse requirements.txt, ignoring comments and empty lines
        REQUIRED_MODULES=$(awk -F '==' '!/^#/ && NF {print $1}' "$REQUIREMENTS_FILE" | tr '[:upper:]' '[:lower:]')
    else
        REQUIRED_MODULES=""
    fi

    for module in $INSTALLED_MODULES; do
        if ! echo "$REQUIRED_MODULES" | grep -q "^$module$"; then
            echo "Uninstalling extra module: $module"
            pip uninstall -y "$module"
            if [ $? -ne 0 ]; then
                echo -e "${BOLD_RED}Failed to uninstall $module. Continuing...${RESET}"
            fi
            echo -e "${BOLD_GREEN}Extra modules removed successfully.${RESET}"
        else
            echo "No modules needed to uninstall"
        fi
    done
else
    echo -e "${BOLD_RED}No requirements.txt file found. Skipping dependency installation and cleanup.${RESET}"
fi

# Step 6: Ready to execute the workhorse script
echo -e "${BOLD_GREEN}Setup complete. Ready to execute ${WORKHORSE_SCRIPT}.${RESET}"
"$VENV_PATH/bin/python" "$WORKHORSE_SCRIPT"