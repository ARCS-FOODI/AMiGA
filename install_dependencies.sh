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
    echo "Creating virtual environment in .venv..."
    python3 -m venv .venv
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
