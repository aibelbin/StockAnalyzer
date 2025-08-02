#!/bin/bash
"""
Virtual Environment Setup for StockAnalyzer
==========================================
This script sets up a virtual environment and installs all required packages.
"""

set -e  # Exit on any error

echo "Setting up StockAnalyzer Virtual Environment..."
echo "=============================================="

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Virtual environment created: ./venv"
else
    echo "Virtual environment already exists: ./venv"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install required packages
echo "Installing required packages..."
pip install fastapi uvicorn python-multipart aiofiles
pip install requests pdf2image pillow opencv-python pytesseract
pip install beautifulsoup4 selenium pandas

# Install system packages if needed (for Tesseract OCR)
echo "Checking system packages..."
if ! command -v tesseract &> /dev/null; then
    echo "Tesseract OCR not found. Please install it manually:"
    echo "sudo apt update && sudo apt install tesseract-ocr -y"
fi

echo ""
echo "=============================================="
echo "Virtual environment setup completed!"
echo "=============================================="
echo "To activate the environment manually, run:"
echo "source venv/bin/activate"
echo ""
echo "To start the persistent server, run:"
echo "python3 run_persistent_server.py"
echo "=============================================="
