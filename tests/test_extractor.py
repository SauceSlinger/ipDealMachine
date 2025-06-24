#!/usr/bin/env python3
"""
Test suite for MLS PDF Extractor
"""

import unittest
import os
import sys

# Add the parent directory to sys.path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from patterns import extract_data_with_patterns
from utils.data_validator import DataValidator
from config import DEFAULT_VALUES


class TestPatternExtraction(unittest.TestCase):
    """Test pattern extraction functionality"""

    def test_rent_extraction(self):
        """Test monthly rent extraction"""
        test_text = "Monthly rent: $1,200 per unit"
        result = extract_data_with_patterns(test_text)
        self.assertEqual(result.get('monthly_rent_per_unit'), '1200')

    def test_units_extraction(self):
        """Test number of units extraction"""
        test_text = "Property has 4 units total"
        result = extract_data_with_patterns(test_text)
        self.assertEqual(result.get('number_of_units'), '4')

    def test_price_extraction(self):
        """Test purchase price extraction"""
        test_text = "Purchase price: $250,000"
        result = extract_data_with_patterns(test_text)
        self.assertEqual(result.get('purchase_price'), '250000')

    def test_multiple_patterns(self):
        """Test extraction of multiple patterns"""
        test_text = """
        Property Information:
        Units: 3
        Monthly rent per unit: $1,500
        Property taxes: $3,600
        Insurance: $1,200
        Interest rate: 6.5%
        """
        result = extract_data_with_patterns(test_text)

        self.assertEqual(result.get('number_of_units'), '3')
        self.assertEqual(result.get('monthly_rent_per_unit'), '1500')
        self.assertEqual(result.get('property_taxes'), '3600')
        self.assertEqual(result.get('insurance'), '1200')
        self.assertEqual(result.get('interest_rate'), '6.5')


class TestDataValidator(unittest.TestCase):
    """Test data validation functionality"""

    def setUp(self):
        self.validator = DataValidator()

    def test_numeric_validation(self):
        """Test numeric field validation"""
        valid, error = self.validator.validate_numeric("1200", "Test Field")
        self.assertTrue(valid)
        self.assertEqual(error, "")

        valid, error = self.validator.validate_numeric("abc", "Test Field")
        self.assertFalse(valid)
        self.assertIn("must be a valid number", error)

    def test_percentage_validation(self):
        """Test percentage field validation"""
        valid, error = self.validator.validate_percentage("5.5", "Vacancy Rate")
        self.assertTrue(valid)

        valid, error = self.validator.validate_percentage("150", "Vacancy Rate")
        self.assertFalse(valid)
        self.assertIn("must be between 0 and 100", error)

    def test_integer_validation(self):
        """Test integer field validation"""
        valid, error = self.validator.validate_integer("4", "Units")
        self.assertTrue(valid)

        valid, error = self.validator.validate_integer("4.5", "Units")
        self.assertFalse(valid)
        self.assertIn("must be a whole number", error)

    def test_all_fields_validation(self):
        """Test validation of all fields"""
        test_data = {
            'number_of_units': '4',
            'monthly_rent_per_unit': '1200',
            'vacancy_rate': '5.0',
            'interest_rate': '6.5',
            'loan_terms_years': '30'
        }

        errors = self.validator.validate_all_fields(test_data)
        self.assertEqual(len(errors), 0)

        # Test with invalid data
        invalid_data = {
            'number_of_units': '4.5',  # Should be integer
            'vacancy_rate': '150',  # Should be <= 100
            'monthly_rent_per_unit': 'abc'  # Should be numeric
        }

        errors = self.validator.validate_all_fields(invalid_data)
        self.assertGreater(len(errors), 0)


class TestConfig(unittest.TestCase):
    """Test configuration settings"""

    def test_default_values(self):
        """Test that default values are defined"""
        self.assertIn('number_of_units', DEFAULT_VALUES)
        self.assertIn('vacancy_rate', DEFAULT_VALUES)
        self.assertIn('interest_rate', DEFAULT_VALUES)
        self.assertIn('loan_terms_years', DEFAULT_VALUES)

    def test_default_values_valid(self):
        """Test that default values are valid"""
        validator = DataValidator()
        errors = validator.validate_all_fields(DEFAULT_VALUES)
        self.assertEqual(len(errors), 0)


class TestIntegration(unittest.TestCase):
    """Integration tests"""

    def test_full_workflow(self):
        """Test the complete workflow"""
        # Sample MLS-like text
        sample_text = """
        PROPERTY DETAILS
        Address: 123 Main Street
        Units: 6
        Monthly rent per unit: $1,800
        Total monthly income: $10,800

        EXPENSES
        Property taxes: $8,400 annually
        Insurance: $2,400 per year
        Property management: $1,080 monthly
        Maintenance and repairs: $3,600 yearly
        Utilities: $1,200 annually

        FINANCING
        Purchase price: $485,000
        Down payment: $97,000
        Interest rate: 6.75%
        Loan term: 30 years
        Vacancy rate: 8%
        """

        # Extract data
        extracted = extract_data_with_patterns(sample_text)

        # Validate extracted data
        validator = DataValidator()
        errors = validator.validate_all_fields(extracted)

        # Check that we extracted key fields
        self.assertIn('number_of_units', extracted)
        self.assertIn('monthly_rent_per_unit', extracted)
        self.assertIn('purchase_price', extracted)

        # Check that validation passes
        self.assertEqual(len(errors), 0)

        # Check specific values
        self.assertEqual(extracted['number_of_units'], '6')
        self.assertEqual(extracted['monthly_rent_per_unit'], '1800')
        self.assertEqual(extracted['purchase_price'], '485000')


if __name__ == '__main__':
    # Create a test suite
    test_suite = unittest.TestSuite()

    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestPatternExtraction))
    test_suite.addTest(unittest.makeSuite(TestDataValidator))
    test_suite.addTest(unittest.makeSuite(TestConfig))
    test_suite.addTest(unittest.makeSuite(TestIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)