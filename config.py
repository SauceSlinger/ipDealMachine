# Configuration settings for MLS PDF Extractor

import os

# Application settings
APP_NAME = "MLS PDF Data Extractor"
APP_VERSION = "1.0.0"
WINDOW_SIZE = "800x900"

# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
EXPORTS_DIR = os.path.join(DATA_DIR, "exports")
SAMPLE_DIR = os.path.join(DATA_DIR, "sample_pdfs")

# Create directories if they don't exist
os.makedirs(EXPORTS_DIR, exist_ok=True)
os.makedirs(SAMPLE_DIR, exist_ok=True)

# Default values
DEFAULT_VALUES = {
    'number_of_units': '1',
    'vacancy_rate': '5.0',
    'interest_rate': '7.0',
    'loan_terms_years': '30'
}

# PDF processing settings
MAX_FILE_SIZE_MB = 50
SUPPORTED_FORMATS = ['.pdf']