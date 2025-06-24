# MLS PDF Data Extractor

A desktop application for extracting real estate investment data from MLS PDF files.

## Features
- Extract 12 key financial metrics from PDF files
- User-friendly GUI interface
- Data validation and error checking
- Export to JSON format
- Support for multiple PDF formats

## Quick Start
1. Run the build script: `./build.sh`
2. Activate virtual environment: `source venv/bin/activate`
3. Start the application: `python main.py`

## Dependencies
- Python 3.8+
- pdfplumber or PyPDF2
- tkinter (included with Python)

## Usage
1. Select a PDF file containing MLS data
2. Click "Extract Data" to automatically parse the document
3. Review and edit extracted values
4. Save results to JSON file