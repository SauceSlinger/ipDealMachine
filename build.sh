#!/bin/bash

# Build script for MLS PDF Extractor

echo "Building MLS PDF Extractor..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Run tests
echo "Running tests..."
python -m pytest tests/ -v

# Create executable (optional)
echo "Creating executable..."
pip install pyinstaller
pyinstaller --onefile --windowed --name="MLS-PDF-Extractor" Main.py

echo "Build complete!"
echo "To run the application:"
echo "1. source venv/bin/activate"
echo "2. python main.py"