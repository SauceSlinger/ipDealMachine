# Data validation utilities
import re
from typing import Dict, Any, Tuple

# Import centralized field definitions
from config import NUMERIC_FIELDS, PERCENTAGE_FIELDS, INTEGER_FIELDS

class DataValidator:
    @staticmethod
    def validate_numeric(value: str, field_name: str) -> Tuple[bool, str]:
        """Validate numeric fields"""
        if not value:
            return True, "" # Empty is valid
        # Remove common formatting
        clean_value = value.replace(',', '').replace('$', '').strip()
        try:
            float(clean_value)
            return True, ""
        except ValueError:
            return False, f"{field_name} must be a valid number"

    @staticmethod
    def validate_percentage(value: str, field_name: str) -> Tuple[bool, str]:
        """Validate percentage fields"""
        if not value:
            return True, ""
        clean_value = value.replace('%', '').strip()
        try:
            num_value = float(clean_value)
            if 0 <= num_value <= 100:
                return True, ""
            else:
                return False, f"{field_name} must be between 0 and 100"
        except ValueError:
            return False, f"{field_name} must be a valid percentage"

    @staticmethod
    def validate_integer(value: str, field_name: str) -> Tuple[bool, str]:
        """Validate integer fields"""
        if not value:
            return True, ""
        # Reject decimal numbers like '4.5' for integer-only fields
        try:
            if '.' in str(value):
                # If it has a decimal point, ensure it's equivalent to an int like '4.0'
                f = float(value)
                if not f.is_integer():
                    return False, f"{field_name} must be a whole number"
                # else fall through to int conversion
            int(float(value))
            return True, ""
        except ValueError:
            return False, f"{field_name} must be a whole number"

    @staticmethod
    def validate_all_fields(data: Dict[str, str]) -> Dict[str, str]:
        """Validate all fields and return error messages"""
        errors = {}
        # Numeric validations
        for field in NUMERIC_FIELDS:
            if field in data:
                valid, error = DataValidator.validate_numeric(data[field], field.replace('_', ' ').title())
                if not valid:
                    errors[field] = error
        # Percentage validations
        for field in PERCENTAGE_FIELDS:
            if field in data:
                valid, error = DataValidator.validate_percentage(data[field], field.replace('_', ' ').title())
                if not valid:
                    errors[field] = error
        # Integer validations
        for field in INTEGER_FIELDS:
            if field in data:
                valid, error = DataValidator.validate_integer(data[field], field.replace('_', ' ').title())
                if not valid:
                    errors[field] = error
        return errors
