#!/bin/bash
# AMiGA Dependency Installation Script for macOS
# This script sets up the Python virtual environment for the backend
# and installs the Node.js dependencies for the frontend.

echo "========================================="
echo "  Setting up AMiGA Environment (macOS)"
echo "========================================="

# Prevent script from stopping completely on a single dependency error
set +e

# Get the directory where the script is located
TARGET_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

echo "Checking for Homebrew..."
if ! command -v brew &> /dev/null; then
    echo "⚠️  Homebrew is not installed. It is highly recommended to install it."
    echo "You can install it by running: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    HAS_BREW=0
else
    HAS_BREW=1
fi

# 1. Setup Backend
echo ""
echo "[1/2] Setting up Python backend environment..."
cd "$TARGET_DIR"

if ! command -v python3 &> /dev/null; then
    echo "python3 is not installed."
    if [ "$HAS_BREW" -eq 1 ]; then
        echo "Installing Python 3 via Homebrew..."
        brew install python
    else
        echo "❌ Cannot install python3 automatically without Homebrew. Please install Python 3 manually."
        exit 1
    fi
fi

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment in .venv..."
    python3 -m venv .venv || { echo "❌ Failed to create virtual environment!"; exit 1; }
else
    echo "Virtual environment .venv already exists."
fi

echo "Activating virtual environment and installing requirements..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt || echo "⚠️  Warning: Some backend dependencies failed to install. Continuing anyway..."
echo "✅ Backend dependency step complete."

# 2. Setup Frontend
echo ""
echo "[2/2] Setting up Vite frontend environment..."

echo "Checking Node.js..."
if ! command -v node &> /dev/null; then
    echo "Node.js is not installed."
    if [ "$HAS_BREW" -eq 1 ]; then
        echo "Installing Node.js via Homebrew..."
        brew install node
    else
        echo "❌ Cannot install Node.js automatically without Homebrew. Please install Node.js manually."
        exit 1
    fi
else
    # Extract the major version number (e.g., 18 from v18.20.4)
    NODE_VERSION=$(node -v | cut -d 'v' -f 2 | cut -d '.' -f 1)
    if [ "$NODE_VERSION" -lt 20 ]; then
        echo "⚠️ Your Node.js version (v$NODE_VERSION) is older than the recommended v20+."
        if [ "$HAS_BREW" -eq 1 ]; then
            echo "Upgrading Node.js via Homebrew..."
            brew upgrade node
        else
            echo "Please consider upgrading Node.js manually."
        fi
    else
        echo "Node.js version (v$NODE_VERSION) is up to date."
    fi
fi

if ! command -v npm &> /dev/null; then
    echo "❌ npm is missing entirely. This is unexpected if Node.js is installed. Please verify your Node.js installation."
    exit 1
fi

cd "$TARGET_DIR/frontend"

echo "Installing npm dependencies in frontend..."
npm install || echo "⚠️  Warning: npm install had some issues, continuing anyway..."
echo "✅ Frontend dependency step complete."

echo ""
echo "========================================="
echo "  Setup Complete! "
echo "  You can now run the simulation using:  "
echo "  ./start_simulate.sh                    "
echo "========================================="
