# Regex patterns for extracting MLS data

import re

# Compile patterns for better performance
PATTERNS = {
    'number_of_units': [
        re.compile(r'units?\s*[:=]\s*(\d+)', re.IGNORECASE),
        re.compile(r'(\d+)\s*units?', re.IGNORECASE),
        re.compile(r'unit\s*count\s*[:=]\s*(\d+)', re.IGNORECASE),
        re.compile(r'total\s*units?\s*[:=]\s*(\d+)', re.IGNORECASE),
        re.compile(r'number\s*of\s*units?\s*[:=]\s*(\d+)', re.IGNORECASE)
    ],
    'monthly_rent_per_unit': [
        re.compile(r'rent\s*per\s*unit\s*[:=]\s*\$?([\d,]+)', re.IGNORECASE),
        re.compile(r'monthly\s*rent\s*[:=]\s*\$?([\d,]+)', re.IGNORECASE),
        re.compile(r'rental\s*income\s*[:=]\s*\$?([\d,]+)', re.IGNORECASE),
        re.compile(r'\$?([\d,]+)\s*per\s*month', re.IGNORECASE),
        re.compile(r'rent\s*[:=]\s*\$?([\d,]+)', re.IGNORECASE)
    ],
    'vacancy_rate': [
        re.compile(r'vacancy\s*rate?\s*[:=]\s*(\d+(?:\.\d+)?)\s*%?', re.IGNORECASE),
        re.compile(r'vacant\s*[:=]\s*(\d+(?:\.\d+)?)\s*%?', re.IGNORECASE),
        re.compile(r'occupancy\s*[:=]\s*(\d+(?:\.\d+)?)\s*%?', re.IGNORECASE)
    ],
    'property_taxes': [
        re.compile(r'property\s*tax(?:es)?\s*[:=]\s*\$?([\d,]+)', re.IGNORECASE),
        re.compile(r'taxes?\s*[:=]\s*\$?([\d,]+)', re.IGNORECASE),
        re.compile(r'annual\s*tax(?:es)?\s*[:=]\s*\$?([\d,]+)', re.IGNORECASE),
        re.compile(r'tax\s*amount\s*[:=]\s*\$?([\d,]+)', re.IGNORECASE)
    ],
    'insurance': [
        re.compile(r'insurance\s*[:=]\s*\$?([\d,]+)', re.IGNORECASE),
        re.compile(r'property\s*insurance\s*[:=]\s*\$?([\d,]+)', re.IGNORECASE),
        re.compile(r'annual\s*insurance\s*[:=]\s*\$?([\d,]+)', re.IGNORECASE)
    ],
    'property_management_fees': [
        re.compile(r'management\s*fee?s?\s*[:=]\s*\$?([\d,]+)', re.IGNORECASE),
        re.compile(r'property\s*management\s*[:=]\s*\$?([\d,]+)', re.IGNORECASE),
        re.compile(r'mgmt\s*fee?s?\s*[:=]\s*\$?([\d,]+)', re.IGNORECASE),
        re.compile(r'pm\s*fee?s?\s*[:=]\s*\$?([\d,]+)', re.IGNORECASE)
    ],
    'maintenance_repairs': [
        re.compile(r'maintenance\s*(?:and\s*)?repairs?\s*[:=]\s*\$?([\d,]+)', re.IGNORECASE),
        re.compile(r'repair\s*(?:and\s*)?maintenance\s*[:=]\s*\$?([\d,]+)', re.IGNORECASE),
        re.compile(r'maint\s*[:=]\s*\$?([\d,]+)', re.IGNORECASE),
        re.compile(r'repairs?\s*[:=]\s*\$?([\d,]+)', re.IGNORECASE)
    ],
    'utilities': [
        re.compile(r'utilities\s*[:=]\s*\$?([\d,]+)', re.IGNORECASE),
        re.compile(r'utility\s*costs?\s*[:=]\s*\$?([\d,]+)', re.IGNORECASE),
        re.compile(r'utils?\s*[:=]\s*\$?([\d,]+)', re.IGNORECASE)
    ],
    'purchase_price': [
        re.compile(r'purchase\s*price\s*[:=]\s*\$?([\d,]+)', re.IGNORECASE),
        re.compile(r'asking\s*price\s*[:=]\s*\$?([\d,]+)', re.IGNORECASE),
        re.compile(r'list\s*price\s*[:=]\s*\$?([\d,]+)', re.IGNORECASE),
        re.compile(r'price\s*[:=]\s*\$?([\d,]+)', re.IGNORECASE),
        re.compile(r'sale\s*price\s*[:=]\s*\$?([\d,]+)', re.IGNORECASE)
    ],
    'down_payment': [
        re.compile(r'down\s*payment\s*[:=]\s*\$?([\d,]+)', re.IGNORECASE),
        re.compile(r'down\s*[:=]\s*\$?([\d,]+)', re.IGNORECASE),
        re.compile(r'initial\s*payment\s*[:=]\s*\$?([\d,]+)', re.IGNORECASE)
    ],
    'interest_rate': [
        re.compile(r'interest\s*rate\s*[:=]\s*(\d+(?:\.\d+)?)\s*%?', re.IGNORECASE),
        re.compile(r'rate\s*[:=]\s*(\d+(?:\.\d+)?)\s*%?', re.IGNORECASE),
        re.compile(r'apr\s*[:=]\s*(\d+(?:\.\d+)?)\s*%?', re.IGNORECASE)
    ],
    'loan_terms_years': [
        re.compile(r'loan\s*term\s*[:=]\s*(\d+)\s*years?', re.IGNORECASE),
        re.compile(r'term\s*[:=]\s*(\d+)\s*years?', re.IGNORECASE),
        re.compile(r'(\d+)\s*year\s*loan', re.IGNORECASE),
        re.compile(r'amortization\s*[:=]\s*(\d+)\s*years?', re.IGNORECASE)
    ]
}


def extract_data_with_patterns(text):
    """Extract data using compiled regex patterns"""
    extracted = {}
    text_clean = re.sub(r'\s+', ' ', text.lower())

    for field, field_patterns in PATTERNS.items():
        for pattern in field_patterns:
            match = pattern.search(text_clean)
            if match:
                value = match.group(1).replace(',', '')
                extracted[field] = value
                break

    return extracted