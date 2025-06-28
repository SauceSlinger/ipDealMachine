# Configuration settings for MLS PDF Extractor

import os

# Application settings
APP_NAME = "MLS PDF Data Extractor"
APP_VERSION = "1.0.1"
WINDOW_SIZE = "800x900"

# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
EXPORTS_DIR = os.path.join(DATA_DIR, "exports")
SAMPLE_DIR = os.path.join(DATA_DIR, "sample_pdfs")

# Create directories if they don't exist
os.makedirs(EXPORTS_DIR, exist_ok=True)
os.makedirs(SAMPLE_DIR, exist_ok=True)

# Default values for fields (King County WA averages/common values)
DEFAULT_VALUES = {
    'number_of_units': '1', # Will be extracted or remain 1 if not found
    'monthly_rent_per_unit': '1500.00', # Added default to allow GPI calculation
    'vacancy_rate': '3.0', # King County average for investment properties, user adjustable
    'property_taxes': '', # Often extracted, leave empty for now as it's not a general default
    'insurance': '2000.00', # Annual estimate for a small multi-family in King County
    'property_management_fees': '4800.00', # Annual estimate (e.g., 8% of $5k monthly rent)
    'maintenance_repairs': '8000.00', # Annual estimate for a multi-family property
    'utilities': '2400.00', # Annual estimate for owner-paid utilities (common areas etc.)
    'purchase_price': '', # Should be extracted or manually entered
    'down_payment': '20.0', # Common down payment percentage for investment loans
    'interest_rate': '6.5', # Average interest rate for multi-family loans (as of June 2025)
    'loan_terms_years': '30', # Typical loan term in years
    'gross_scheduled_income': '' # Will be extracted or manually entered, GPI logic will use it if rent/units are empty
}

# PDF processing settings
MAX_FILE_SIZE_MB = 50
SUPPORTED_FORMATS = ['.pdf']

# --- Centralized Field Definitions for GUI and Validation ---
# Define the order and labels for GUI display
GUI_FIELD_ORDER = [
    ("Number of Units", "number_of_units"),
    ("Monthly Rent per Unit ($)", "monthly_rent_per_unit"),
    ("Vacancy Rate (%)", "vacancy_rate"),
    ("Property Taxes ($)", "property_taxes"),
    ("Insurance ($)", "insurance"),
    ("Property Management Fees ($)", "property_management_fees"),
    ("Maintenance and Repairs ($)", "maintenance_repairs"),
    ("Utilities ($)", "utilities"),
    ("Purchase Price ($)", "purchase_price"),
    ("Down Payment (%)", "down_payment"),
    ("Interest Rate (%)", "interest_rate"),
    ("Loan Terms (Years)", "loan_terms_years"),
    ("Gross Scheduled Income ($)", "gross_scheduled_income")
]

# Define field types for validation
NUMERIC_FIELDS = [
    'monthly_rent_per_unit', 'property_taxes', 'insurance',
    'property_management_fees', 'maintenance_repairs', 'utilities',
    'purchase_price', 'gross_scheduled_income'
]

PERCENTAGE_FIELDS = ['vacancy_rate', 'interest_rate', 'down_payment']

INTEGER_FIELDS = ['number_of_units', 'loan_terms_years']
