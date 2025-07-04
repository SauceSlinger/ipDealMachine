# MLS PDF Extractor - Version 1.0.4

Welcome to the MLS PDF Extractor, a desktop application designed to streamline the process of extracting key real estate data from MLS PDF documents and performing financial projections. This tool is built to help real estate investors quickly analyze potential investment properties.

## What's New in Version 1.0.4 (The Visual & Robust Update!)

This version brings significant enhancements to the user interface, making data interaction more intuitive, and crucial under-the-hood improvements for stability and extraction accuracy.

### ✨ Key Features & Enhancements:

Dynamic Color-Coded Input Fields:

* Yellow Background: Indicates default values.

* Blue Background: Shows data that has been manually adjusted by you.

* Green Background: Highlights data successfully extracted from a PDF.

* Input field colors update instantly as data changes!

Intuitive 7-Color Gradient for Financial Projections:

* Output values are now color-coded on a gradient from bright red (most negative/worst performance) through white (neutral/break-even) to bright green (best performance).

* This provides immediate visual feedback on the health and potential of your investment projections.

Clear Color Keys: Dedicated legends below both the input and output sections explain the meaning of each color, ensuring clarity at a glance.

Expanded PDF Data Extraction:

* Significantly improved pattern recognition for extracting information from various MLS PDF formats.

* Includes support for synonymous terms (e.g., "Ann Taxes" for "Property Taxes," "LP" for "List Price") to capture more data automatically.

Enhanced Stability & Database Handling:

* Resolved critical threading issues with SQLite, ensuring robust and reliable database operations when extracting and saving data in the background.

* Fixed an issue where the file path was inadvertently cleared after selection.

* Addressed a TclError related to dynamic ttk.Entry styling, making the UI more stable.

User Interface Refinements: Continued focus on a clean, professional, and friendly user experience with improved styling and responsiveness.

### Features

PDF Data Extraction: Automatically parses MLS PDF documents to pull out key property details.

Manual Data Input: Easily adjust or input data manually for properties not from a PDF, or to fine-tune extracted values.

Financial Projections: Calculates essential real estate investment metrics:

* Gross Potential Income (GPI)

* Vacancy and Credit Loss (V&C)

* Effective Gross Income (EGI)

* Net Operating Income (NOI)

* Capitalization Rate (Cap Rate)

* Debt Service (Mortgage Payment)

* Cash Flow Before Taxes (CFBT)

* Cash-on-Cash Return (CoC)

* Gross Rent Multiplier (GRM)

* Debt Service Coverage Ratio (DSCR)

Data Validation: Basic validation to ensure data integrity for calculations.

Database Storage: Save and load property data and financial projections to/from an integrated SQLite database.

PDF Content Preview: View a text preview of the loaded PDF directly within the application.

Setup & Installation
Clone the Repository:

    git clone <repository_url>
    cd mls-pdf-extractor

Create a Virtual Environment (Recommended):

    python3 -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate

Install Dependencies:

    pip install --upgrade pip
    pip install -r requirements.txt

Note: If you encounter issues with PDF extraction, ensure pdfplumber or PyPDF2 are correctly installed. You might need sudo apt-get install python3-tk on some Linux systems for Tkinter.

Usage
Run the Application:

    python main.py

Select a PDF: Click "Browse" to choose an MLS PDF file.

Extract Data: Click "Extract Data" to automatically parse the document. The extracted values will populate the input fields.

Review & Adjust:

Observe the color coding on the input fields to see the source of the data.

Manually adjust any values as needed; the field color will change to blue, and financial projections will update in real-time.

See the output fields dynamically change color based on their calculated performance.

Save Data: Click "Save Current Data" to store the property details and financial projections in the local database.

Load Saved Properties: Use the "Processed Properties" list on the right to load previously saved properties.

Project Structure

    mls-pdf-extractor/
    ├── main.py                 # Main application GUI and logic
    ├── config.py               # Configuration settings, default values, and color definitions
    ├── patterns.py             # Regular expressions for PDF data extraction
    ├── requirements.txt        # Python dependencies
    ├── utils/
    │   ├── __init__.py
    │   ├── pdf_processor.py    # Handles PDF text extraction
    │   ├── data_validator.py   # Validates input data
    │   └── database.py         # Manages SQLite database interactions
    └── data/                   # Directory for database and sample files
        └── mls_properties.db   # SQLite database file (created automatically)
        └── exports/            # Exported JSON files (if implemented)
        └── sample_pdfs/        # Place sample PDFs here

Contributing
Feel free to open issues or submit pull requests if you have suggestions for improvements or encounter any bugs!