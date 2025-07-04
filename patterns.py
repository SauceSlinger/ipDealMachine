# Regex patterns for extracting data from MLS PDF files
# Each key in EXTRACTION_PATTERNS corresponds to a field in your application.
# The value is a list of regex patterns. The first matching pattern will be used.
# Patterns are ordered from most specific to more general if there's overlap.

import re
import logging

logger = logging.getLogger(__name__)

EXTRACTION_PATTERNS = { # Correct spelling here
    # --- Property Identification & Price ---
    'mls_number': [
        r'MLS#:\s*(\d+)',
        r'MLS#:\s*(\d+)\n',
        r'MLS:\s*(\d+)',
        r'(\d+)\n\s*MLS#:',
    ],
    'purchase_price': [
        r'(?:List Price|LP|Price):\s*[\$£€]?([\d,\.]+)',
        r'List Price:\s*[\$£€]?([\d,\.]+)',
        r'LP:\s*[\$£€]?([\d,\.]+)',
        r'Price:\s*[\$£€]?([\d,\.]+)',
        r'Sale Price:\s*[\$£€]?([\d,\.]+)',
        r'Asking Price:\s*[\$£€]?([\d,\.]+)',
    ],
    'property_type': [
        r'(?:Prop Type|Property Type):\s*([A-Za-z\s]+)',
        r'Property Type:\s*([A-Za-z\s]+)',
        r'Prop Type:\s*([A-Za-z\s]+)',
        r'Sub Type:\s*([A-Za-z\s]+)',
    ],
    'year_built': [
        r'(?:Yr Built|Year Built):\s*(\d{4})',
        r'Year Built:\s*(\d{4})',
        r'Yr Built:\s*(\d{4})',
    ],
    'number_of_units': [
        r'(?:Number of Units|Units):\s*(\d+)',
        r'Units:\s*(\d+)',
        r'# of Units:\s*(\d+)',
        r'Unit Count:\s*(\d+)',
        r'(\d+)-plex',
    ],
    # 'monthly_rent_per_unit': This is typically not in general MLS listings,
    # but rather in pro-forma or specific rental listings. Keep as-is.
    # r'(?:Monthly Rent Per Unit|Rent Per Unit):\s*[\$£€]?([\d,\.]+)',

    # --- Expenses ---
    'property_taxes': [
        r'(?:Property Taxes|Tax Expense|Ann Taxes|Annual Taxes):\s*[\$£€]?([\d,\.]+)',
        r'Property Taxes:\s*[\$£€]?([\d,\.]+)',
        r'Tax Expense:\s*[\$£€]?([\d,\.]+)',
        r'Ann Taxes:\s*[\$£€]?([\d,\.]+)',
        r'Annual Taxes:\s*[\$£€]?([\d,\.]+)',
    ],
    'insurance': [
        r'(?:Insurance|Annual Insurance):\s*[\$£€]?([\d,\.]+)',
        r'Insurance:\s*[\$£€]?([\d,\.]+)',
        r'Annual Insurance:\s*[\$£€]?([\d,\.]+)',
    ],
    'property_management_fees': [
        r'(?:Property Management Fees|Management Fees):\s*[\$£€]?([\d,\.]+)',
        r'Property Management Fees:\s*[\$£€]?([\d,\.]+)',
        r'Management Fees:\s*[\$£€]?([\d,\.]+)',
    ],
    'maintenance_repairs': [
        r'(?:Maintenance and Repairs|Maintenance|Repairs):\s*[\$£€]?([\d,\.]+)',
        r'Maintenance and Repairs:\s*[\$£€]?([\d,\.]+)',
        r'Maintenance:\s*[\$£€]?([\d,\.]+)',
        r'Repairs:\s*[\$£€]?([\d,\.]+)',
    ],
    'utilities': [
        r'(?:Utilities|Annual Utilities):\s*[\$£€]?([\d,\.]+)',
        r'Utilities:\s*[\$£€]?([\d,\.]+)',
        r'Annual Utilities:\s*[\$£€]?([\d,\.]+)',
    ],
    'gross_scheduled_income': [
        r'(?:Gross Scheduled Income|Gross Income|GSI):\s*[\$£€]?([\d,\.]+)',
        r'Gross Scheduled Income:\s*[\$£€]?([\d,\.]+)',
        r'Gross Income:\s*[\$£€]?([\d,\.]+)',
        r'GSI:\s*[\$£€]?([\d,\.]+)',
    ],

    # --- Loan/Financing (less common to extract directly, usually user input) ---
    'down_payment': [
        r'(?:Down Payment|DP):\s*([\d\.]+)%',
        r'Down Payment Percentage:\s*([\d\.]+)%',
    ],
    'interest_rate': [
        r'(?:Interest Rate|Rate):\s*([\d\.]+)%',
        r'Interest Rate:\s*([\d\.]+)%',
    ],
    'loan_terms_years': [
        r'(?:Loan Terms|Loan Term|Term):\s*(\d+)\s*(?:years|yrs)',
        r'Loan Term \(Years\):\s*(\d+)',
    ],

    # --- Additional Property Details (for display/context, not financial calcs) ---
    'total_beds': [
        r'(?:Beds|Bedrooms|Ttl Beds):\s*(\d+)',
        r'Beds:\s*(\d+)',
        r'Bedrooms:\s*(\d+)',
        r'Ttl Beds:\s*(\d+)',
    ],
    'total_baths': [
        r'(?:Baths|Bathrooms|Ttl Baths):\s*([\d\.]+)',
        r'Baths:\s*([\d\.]+)',
        r'Bathrooms:\s*([\d\.]+)',
        r'Ttl Baths:\s*([\d\.]+)',
    ],
    'total_sqft': [
        r'(?:Ttl Dwl SqFt|Approx Square Feet|SqFt|Total SqFt):\s*([\d,\.]+)\s*sf',
        r'Ttl Dwl SqFt:\s*([\d,\.]+)',
        r'Approx Square Feet:\s*([\d,\.]+)\s*sf',
        r'SqFt:\s*([\d,\.]+)',
        r'Total SqFt:\s*([\d,\.]+)',
    ],
    'lot_sf': [
        r'(?:Lot SF|Lot Size):\s*([\d,\.]+)\s*sf',
        r'Lot Size:\s*([\d,\.]+)\s*sf',
        r'Lot SF \(approx\):\s*([\d,\.]+)\s*sf',
    ],
    'county': [
        r'County:\s*([A-Za-z\s]+)',
    ],
    'community': [
        r'Commty:\s*([A-Za-z\s]+)',
        r'Community:\s*([A-Za-z\s]+)',
    ],
    'style_code': [
        r'Style Code:\s*([A-Za-z0-9\s-]+)',
    ],
    'exterior': [
        r'Exterior:\s*([A-Za-z\s]+)',
    ],
    'roof': [
        r'Roof:\s*([A-Za-z\s]+)',
    ],
    'heating': [
        r'Heating:\s*([A-Za-z\s]+)',
        r'Energy Source\(heat\):\s*([A-Za-z\s]+)',
    ],
    'cooling': [
        r'Cooling:\s*([A-Za-z\s]+)',
    ],
    'floor_covering': [
        r'Floor Cvr:\s*([A-Za-z,\s]+)',
        r'Floor Coverning:\s*([A-Za-z,\s]+)',
    ],
    'appliances': [
        r'Appliances:\s*([A-Za-z\s,()]+)',
    ],
    'interior_features': [
        r'Interior Ft:\s*([A-Za-z\s,()]+)',
        r'Interior Features\n\s*([A-Za-z\s,()]+)',
    ],
}

def extract_data_with_patterns(text_content: str) -> dict:
    """
    Extracts data from the given text content using predefined regex patterns.
    Args:
        text_content (str): The raw text content extracted from a PDF.
    Returns:
        dict: A dictionary where keys are field names and values are extracted strings.
    """
    extracted_data = {}
    for field_name, patterns in EXTRACTION_PATTERNS.items(): # Corrected typo here
        for pattern in patterns:
            match = re.search(pattern, text_content, re.IGNORECASE | re.DOTALL)
            if match:
                value = match.group(1).strip()
                value = re.sub(r'\s+', ' ', value)
                value = value.replace('"', '').strip()
                extracted_data[field_name] = value
                logger.info(f"Extracted '{field_name}': '{value}' using pattern '{pattern}'")
                break
        if field_name not in extracted_data:
            logger.debug(f"No match found for '{field_name}'")
    return extracted_data

