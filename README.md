MLS PDF Extractor
The MLS PDF Extractor is a desktop application designed to streamline the process of extracting key real estate investment data from MLS PDF files. It provides a user-friendly graphical interface (GUI) to automatically parse property information, fill in missing financial variables with King County, Washington averages, perform essential investment calculations, and present all data in a clear, organized, two-column layout.

This application is ideal for real estate investors and agents who need quick financial insights from MLS reports.

Features
PDF Data Extraction: Automatically extracts key property information like list price, number of units, property taxes, and gross scheduled income directly from MLS PDF files.

Automated Data Filling: When data is not explicitly found in the PDF, the application automatically populates fields (e.g., vacancy rate, insurance, management fees, loan terms) with sensible default averages for King County, Washington.

Comprehensive Financial Projections: Calculates crucial investment metrics in real-time based on input data:

Gross Potential Income (GPI)

Vacancy and Credit Loss (V&C)

Effective Gross Income (EGI)

Net Operating Income (NOI)

Capitalization Rate (Cap Rate)

Debt Service (Mortgage Payment)

Cash Flow Before Taxes (CFBT)

Cash-on-Cash Return (CoC)

Gross Rent Multiplier (GRM)

Debt Service Coverage Ratio (DSCR)

Interactive GUI: All input fields are editable, allowing users to manually adjust extracted or default values to run different scenarios.

Two-Column Layout: A visually appealing and organized two-column interface separates input data from financial outputs for enhanced clarity and ease of observation.

Century 21 Inspired Theme: Features a professional color scheme of gold, black, dark gray, and white for a branded look.

PDF Content Preview: Displays a preview of the extracted text content from the PDF for verification.

Data Export: Save all extracted and calculated data to a JSON file for record-keeping and further analysis.

Setup Guide
Follow these steps to set up and run the MLS PDF Extractor on your system.

Prerequisites
Python 3.8+

pip (Python package installer)

Installation Steps
Clone the Repository (or create project structure):
If you have a Git repository:

git clone <your-repository-url>
cd mls-pdf-extractor

If you're creating files manually, ensure your project directory (mls-pdf-extractor) has the following structure and files:

mls-pdf-extractor/
├── main.py
├── config.py
├── patterns.py
├── requirements.txt
├── utils/
│   ├── __init__.py
│   ├── pdf_processor.py
│   └── data_validator.py
└── data/
    ├── exports/
    └── sample_pdfs/

Create a Virtual Environment:
It's highly recommended to use a virtual environment to manage dependencies.

python3 -m venv venv

Activate the Virtual Environment:

On Linux/macOS:

source venv/bin/activate

On Windows (Command Prompt):

venv\Scripts\activate.bat

On Windows (PowerShell):

venv\Scripts\Activate.ps1

Install Dependencies:
First, ensure your requirements.txt file contains the necessary libraries:

pdfplumber
PyPDF2

Then, install them:

pip install -r requirements.txt

Note: The application attempts to use pdfplumber first, then falls back to PyPDF2. If you encounter issues, ensure at least one of these is installed.

Usage
Run the Application:
Navigate to your mls-pdf-extractor directory in your activated virtual environment and run:

python main.py

The GUI application window will open.

Load Defaults (Optional, but recommended on first launch):
Upon launch, the application will automatically load default values and perform initial calculations. You can click the "Load Defaults" button at any time to reset input fields to their predefined King County averages.

Select a PDF File:
Click the "Browse" button next to "PDF File:" to select an MLS PDF report from your system.

Extract Data:
Click the "Extract Data" button. The application will process the PDF, extract relevant information, display a preview of the PDF content, and automatically populate the "Input Data" fields.

Review and Adjust Inputs:
Review the "Input Data" fields. Values extracted from the PDF will overwrite defaults. You can manually adjust any field (e.g., "Monthly Rent per Unit", "Vacancy Rate", or any expense) to model different scenarios. Changes will trigger real-time recalculations of the financial projections.

Observe Financial Projections:
The "Financial Projections" pane on the right side of the window will display all calculated metrics (GPI, NOI, Cap Rate, Cash Flow, etc.) in real-time as you modify input values.

Validate Data (Optional):
Click "Validate Data" to check if your entered inputs meet basic formatting requirements (e.g., numbers are numbers, percentages are within range).

Save Results:
Click "Save to JSON" to export all current input data and calculated financial projections into a JSON file. You will be prompted to choose a location and filename for the export. By default, files save to the data/exports directory.

Clear All:
Click "Clear All" to reset all input fields and calculated outputs.

Project Structure
main.py: The main application script that initializes the GUI, handles user interactions, and orchestrates data extraction and financial calculations.

config.py: Contains application-wide settings, file paths, default input values (King County averages), and centralized definitions for GUI field order, validation types, and the Century 21 color palette. This is your primary configuration file.

patterns.py: Defines the regular expression patterns used to extract specific data points from the raw text content of MLS PDFs.

requirements.txt: Lists the Python libraries required for the application.

utils/: A directory for utility modules:

__init__.py: Makes utils a Python package.

pdf_processor.py: Handles the extraction of text content from PDF files using pdfplumber or PyPDF2.

data_validator.py: Contains functions to validate the format and range of input data fields.

data/: Directory for application data:

exports/: Default location for saving exported JSON data.

sample_pdfs/: Recommended location for storing sample MLS PDF files for testing.

Troubleshooting
"PDF processing library not found" warning:
Ensure pdfplumber (or PyPDF2) is installed. Run: pip install pdfplumber.

Calculations showing "N/A":
Check the input fields. If Gross Scheduled Income, Number of Units, or Monthly Rent per Unit are missing, GPI (and thus other calculations) cannot proceed. Ensure you have loaded defaults or entered sufficient data.

Permission Errors:
Make sure you have write permissions in the project directory, especially in the data/exports folder.

PDF not extracting data correctly:

The current regex patterns in patterns.py are tailored to common MLS formats. If your PDFs have a significantly different layout, you may need to adjust or add new patterns in patterns.py.

Try installing PyPDF2 as an alternative if pdfplumber struggles: pip install PyPDF2. The application will attempt to use it if pdfplumber fails.