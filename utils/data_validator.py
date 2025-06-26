# Data validation utilities
import re
from typing import Dict, Any, Tuple

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
        try:
            int(value)
            return True, ""
        except ValueError:
            return False, f"{field_name} must be a whole number"

    @staticmethod
    def validate_all_fields(data: Dict[str, str]) -> Dict[str, str]:
        """Validate all fields and return error messages"""
        errors = {}
        # Numeric validations
        numeric_fields = [
            'monthly_rent_per_unit', 'property_taxes', 'insurance',
            'property_management_fees', 'maintenance_repairs', 'utilities',
            'purchase_price', 'down_payment', 'gross_scheduled_income' # Added gross_scheduled_income
        ]
        for field in numeric_fields:
            if field in data:
                valid, error = DataValidator.validate_numeric(data[field], field.replace('_', ' ').title())
                if not valid:
                    errors[field] = error
        # Percentage validations
        percentage_fields = ['vacancy_rate', 'interest_rate']
        for field in percentage_fields:
            if field in data:
                valid, error = DataValidator.validate_percentage(data[field], field.replace('_', ' ').title())
                if not valid:
                    errors[field] = error
        # Integer validations
        integer_fields = ['number_of_units', 'loan_terms_years']
        for field in integer_fields:
            if field in data:
                valid, error = DataValidator.validate_integer(data[field], field.replace('_', ' ').title())
                if not valid:
                    errors[field] = error
        return errors
