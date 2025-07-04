# Configuration settings for MLS PDF Extractor

import os

# Application settings
APP_NAME = "MLS PDF Data Extractor"
APP_VERSION = "1.0.5" # Updated version
WINDOW_SIZE = "1400x1000" # Main window size

# Database settings
DATABASE_NAME = "mls_properties.db" # SQLite database file name

# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
EXPORTS_DIR = os.path.join(DATA_DIR, "exports")
SAMPLE_DIR = os.path.join(DATA_DIR, "sample_pdfs")

# Create directories if they don't exist
os.makedirs(EXPORTS_DIR, exist_ok=True)
os.makedirs(SAMPLE_DIR, exist_ok=True)

# Define Century 21 inspired color palette
C21_GOLD = '#DAA520' # A rich gold
C21_BLACK = '#000000'
C21_DARK_GRAY = '#333333'
C21_WHITE = '#FFFFFF'
C21_LIGHT_GRAY = '#F5F5F5' # For general backgrounds


#
# except ImportError:
#     pass # Handle cases where ttk might not be available or styled
# # --- End Custom Tkinter Styles ---

# --- Color Coding for Input Fields ---
INPUT_COLOR_DEFAULT = '#FFFFCC'  # Light Yellow
INPUT_COLOR_MANUAL = '#CCE5FF'   # Light Blue
INPUT_COLOR_EXTRACTED = '#CCFFCC' # Light Green

# --- Color Gradient for Output Fields (7 steps from Red to Green) ---
# This gradient is designed to go from bright red (most negative) to bright green (best)
# with white in the middle (neutral/break-even).
OUTPUT_GRADIENT_COLORS = [
    '#FF0000', # Bright Red (Most Negative)
    '#FF6666', # Lighter Red
    '#FFCCCC', # Pale Red
    '#FFFFFF', # White (Neutral/Break-even)
    '#CCFFCC', # Pale Green
    '#66FF66', # Lighter Green
    '#00FF00'  # Bright Green (Best)
]

# --- Output Value Ranges for Color Gradient Mapping ---
# Define min, mid, max for each output to map to the 7-color gradient.
# Values outside this range will be clamped to the min/max color.
# These are initial assumptions and can be adjusted based on typical investment property performance.
OUTPUT_RANGES = {
    'gpi': {'min': 0, 'mid': 50000, 'max': 150000, 'direction': 'positive'}, # Annual income
    'vc': {'min': 0, 'mid': 5000, 'max': 15000, 'direction': 'negative'}, # Annual loss, lower is better
    'egi': {'min': 0, 'mid': 45000, 'max': 140000, 'direction': 'positive'}, # Annual income
    'noi': {'min': -10000, 'mid': 30000, 'max': 100000, 'direction': 'positive'}, # Annual income, can be negative
    'cap_rate': {'min': 3.0, 'mid': 6.0, 'max': 10.0, 'direction': 'positive'}, # Percentage, higher is better
    'debt_service': {'min': 10000, 'mid': 40000, 'max': 80000, 'direction': 'negative'}, # Annual payment, lower is better
    'cfbt': {'min': -20000, 'mid': 0, 'max': 20000, 'direction': 'positive'}, # Annual cash flow, can be negative, 0 is neutral
    'coc_return': {'min': -10.0, 'mid': 5.0, 'max': 20.0, 'direction': 'positive'}, # Percentage, higher is better, can be negative
    'grm': {'min': 5.0, 'mid': 10.0, 'max': 15.0, 'direction': 'negative'}, # Multiplier, lower is better
    'dscr': {'min': 0.5, 'mid': 1.2, 'max': 2.0, 'direction': 'positive'} # Ratio, higher is better (1.2-1.5 is common benchmark)
}


# Default values for fields (King County WA averages/common values)
DEFAULT_VALUES = {
    'number_of_units': '1',
    'monthly_rent_per_unit': '1500.00',
    'vacancy_rate': '3.0',
    'property_taxes': '',
    'insurance': '2000.00',
    'property_management_fees': '4800.00',
    'maintenance_repairs': '8000.00',
    'utilities': '2400.00',
    'purchase_price': '',
    'down_payment': '20.0',
    'interest_rate': '6.5',
    'loan_terms_years': '30',
    'gross_scheduled_income': '0'
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
