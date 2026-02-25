#!/bin/bash
# AMiGA Dependency Installation Script
# This script sets up the Python virtual environment for the backend
# and installs the Node.js dependencies for the frontend.

echo "========================================="
echo "  Setting up AMiGA Environment"
echo "========================================="

# Prevent script from stopping completely on a single dependency error
set +e

# Get the directory where the script is located
TARGET_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

# 1. Setup Backend
echo ""
echo "[1/2] Setting up Python backend environment..."
cd "$TARGET_DIR"

if [ ! -d ".venv" ]; then
    echo "Checking if python3-venv is installed..."
    if ! dpkg -l | grep -q python3-venv; then
        echo "Installing python3-venv (may require sudo password)..."
        sudo apt-get update && sudo apt-get install -y python3-venv || echo "⚠️ Warning: Failed to install python3-venv. Venv creation might fail."
    fi

    echo "Creating virtual environment in .venv..."
    python3 -m venv .venv || { echo "❌ Failed to create virtual environment! Please install python3-venv manually."; exit 1; }
else
    echo "Virtual environment .venv already exists."
fi

echo "Activating virtual environment and installing requirements..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt || echo "⚠️  Warning: Some backend dependencies failed to install (often due to hardware packages). Continuing anyway..."
echo "✅ Backend dependency step complete."

# 2. Setup Frontend
echo ""
echo "[2/2] Setting up Vite frontend environment..."

echo "Checking Node.js and npm versions..."
if ! command -v node &> /dev/null; then
    echo "Node.js is not installed."
    echo "Installing up-to-date nodejs and npm (may require sudo password)..."
    # Using NodeSource to get Node.js 22.x instead of the older default apt version
    curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - || echo "⚠️ Warning: Failed to add NodeSource repository."
    sudo apt-get install -y nodejs || echo "⚠️ Warning: Failed to install nodejs."
else
    # Extract the major version number (e.g., 18 from v18.20.4)
    NODE_VERSION=$(node -v | cut -d 'v' -f 2 | cut -d '.' -f 1)
    if [ "$NODE_VERSION" -lt 20 ]; then
        echo "⚠️ Your Node.js version (v$NODE_VERSION) is older than the recommended v20+."
        echo "Attempting to update Node.js to version 22.x using NodeSource (may require sudo password)..."
        curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - || echo "⚠️ Warning: Failed to add NodeSource repository."
        sudo apt-get install -y nodejs || echo "⚠️ Warning: Failed to update nodejs. You may need to update manually from https://nodejs.org/"
    else
        echo "Node.js version (v$NODE_VERSION) is up to date."
    fi
fi

if ! command -v npm &> /dev/null; then
    echo "npm is missing entirely, attempting to install..."
    sudo apt-get install -y npm || echo "⚠️ Warning: Failed to install npm."
fi

cd "$TARGET_DIR/frontend"

echo "Installing npm dependencies..."
npm install || echo "⚠️  Warning: npm install had some issues, continuing anyway..."
echo "✅ Frontend dependency step complete."

echo ""
echo "========================================="
echo "  Setup Complete! "
echo "  You can now run the simulation using:  "
echo "  ./start_simulate.sh                    "
echo "========================================="
