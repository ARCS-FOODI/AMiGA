#!/bin/bash
# AMiGA Dependency Installation Script
# This script sets up the Python virtual environment for the backend
# and installs the Node.js dependencies for the frontend.

echo "========================================="
echo "  Setting up AMiGA Environment"
echo "========================================="

# Stop on first error
set -e

# 1. Setup Backend
echo ""
echo "[1/2] Setting up Python backend environment..."
cd /home/siyyo/Documents/arcs_foodi/AMiGA

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment in .venv..."
    python3 -m venv .venv
else
    echo "Virtual environment .venv already exists."
fi

echo "Activating virtual environment and installing requirements..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Backend dependencies installed successfully."

# 2. Setup Frontend
echo ""
echo "[2/2] Setting up Vite frontend environment..."
cd /home/siyyo/Documents/arcs_foodi/AMiGA/frontend

echo "Installing npm dependencies..."
npm install
echo "✅ Frontend dependencies installed successfully."

echo ""
echo "========================================="
echo "  Setup Complete! "
echo "  You can now run the simulation using:  "
echo "  ./start_simulate.sh                    "
echo "========================================="
