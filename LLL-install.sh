#!/bin/bash
# install.sh - Install script for the Disney Ride Wait Time Display application
# This script supports Linux (e.g., Raspberry Pi) and Windows (using Git Bash/WSL)
# It creates a virtual environment, upgrades pip, and installs required packages.

set -e

echo "Starting installation..."

# Determine which Python command to use (python3 or python)
if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON=python
else
    echo "Python is not installed. Please install Python 3 and try again."
    exit 1
fi

echo "Using Python command: $PYTHON"

# Create a virtual environment if not already present
if [ ! -d "venv" ]; then
    echo "Creating a Python virtual environment..."
    $PYTHON -m venv venv
fi

# Activate the virtual environment.
# On Linux (including Raspberry Pi), the activate script is in venv/bin/activate.
# On Windows (using Git Bash/WSL), it is usually in venv/Scripts/activate.
if [[ "$OSTYPE" == "msys"* || "$OSTYPE" == "cygwin"* || "$OSTYPE" == "win32"* ]]; then
    echo "Activating virtual environment for Windows..."
    source venv/Scripts/activate
else
    echo "Activating virtual environment for Linux..."
    source venv/bin/activate
fi

# Upgrade pip
echo "Upgrading pip..."
$PYTHON -m pip install --upgrade pip

# Install required Python packages
echo "Installing required packages..."
pip install requests aiohttp

# Optionally install any additional packages if needed.
# For example, if you need Pillow or other packages, add them here:
# pip install Pillow

echo "Installation complete."
echo "To activate the virtual environment in the future, run:"
if [[ "$OSTYPE" == "msys"* || "$OSTYPE" == "cygwin"* || "$OSTYPE" == "win32"* ]]; then
    echo "    source venv/Scripts/activate"
else
    echo "    source venv/bin/activate"
fi
