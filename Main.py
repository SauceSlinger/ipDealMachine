#!/usr/bin/env python3
"""
MLS PDF Data Extractor
A desktop application for extracting real estate data from MLS PDF files
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import json
from datetime import datetime
import threading
import logging
import re  # Import the regex module

# Import our custom modules
from config import (
    APP_NAME, APP_VERSION, WINDOW_SIZE, EXPORTS_DIR, DEFAULT_VALUES,
    GUI_FIELD_ORDER, NUMERIC_FIELDS, PERCENTAGE_FIELDS, INTEGER_FIELDS  # <-- ADDED THESE IMPORTS
)
from patterns import extract_data_with_patterns
from utils.pdf_processor import PDFProcessor
from utils.data_validator import DataValidator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLSDataExtractor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry(WINDOW_SIZE)

        # Apply a theme for a modern look
        self.style = ttk.Style()
        self.style.theme_use('clam')  # You can try 'clam', 'alt', 'default', 'classic'

        # Configure styles for various widgets
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0', font=('Arial', 10))
        self.style.configure('TButton', font=('Arial', 10, 'bold'), padding=6)
        self.style.map('TButton',
                       background=[('active', '#e0e0e0')],
                       foreground=[('active', 'black')])
        self.style.configure('Accent.TButton', background='#4CAF50', foreground='white')
        self.style.map('Accent.TButton',
                       background=[('active', '#45a049')],
                       foreground=[('active', 'white')])
        self.style.configure('TEntry', fieldbackground='white')
        self.style.configure('TLabelframe', background='#f0f0f0')
        self.style.configure('TLabelframe.Label', background='#f0f0f0', font=('Arial', 12, 'bold'))
        self.style.configure('TProgressbar', thickness=10)

        # Initialize processors
        self.pdf_processor = PDFProcessor()
        self.validator = DataValidator()

        # Data structure for extracted information (input fields)
        # This will be populated from GUI_FIELD_ORDER dynamically
        self.extracted_data = {key: '' for label, key in GUI_FIELD_ORDER}

        # Data structure for calculated outputs
        self.calculated_outputs = {
            'gpi': tk.StringVar(value="N/A"),
            'vc': tk.StringVar(value="N/A"),
            'egi': tk.StringVar(value="N/A"),
            'noi': tk.StringVar(value="N/A"),
            'cap_rate': tk.StringVar(value="N/A"),
            'debt_service': tk.StringVar(value="N/A"),
            'cfbt': tk.StringVar(value="N/A"),
            'coc_return': tk.StringVar(value="N/A"),
            'grm': tk.StringVar(value="N/A"),
            'dscr': tk.StringVar(value="N/A")
        }

        self.setup_ui()
        # Automatically load defaults and calculate on application start
        self.root.after(100, self.load_defaults_and_calculate)

    def load_defaults_and_calculate(self):
        """Loads defaults and then triggers a calculation. Used on app start."""
        self.load_defaults()
        self.calculate_projections()

    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Title
        title_label = ttk.Label(main_frame, text=f"{APP_NAME} v{APP_VERSION}",
                                font=('Arial', 18, 'bold'), anchor='center')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 25), sticky=tk.E + tk.W)

        # File selection
        ttk.Label(main_frame, text="PDF File:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.file_path_var = tk.StringVar()
        self.file_entry = ttk.Entry(main_frame, textvariable=self.file_path_var, width=50)
        self.file_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 5))

        browse_btn = ttk.Button(main_frame, text="Browse", command=self.browse_file)
        browse_btn.grid(row=1, column=2, pady=5)

        # Extract button
        extract_btn = ttk.Button(main_frame, text="Extract Data",
                                 command=self.extract_data_threaded, style='Accent.TButton')
        extract_btn.grid(row=2, column=0, columnspan=3, pady=20)

        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        # Status label
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, font=('Arial', 9, 'italic'))
        status_label.grid(row=4, column=0, columnspan=3, pady=5)

        # Data fields frame (Inputs)
        fields_frame = ttk.LabelFrame(main_frame, text="Input Data", padding="15")
        fields_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=20)
        fields_frame.columnconfigure(1, weight=1)

        # Create entry fields for each data point using GUI_FIELD_ORDER
        self.entry_vars = {}
        self.entries = {}

        for i, (label, key) in enumerate(GUI_FIELD_ORDER):
            ttk.Label(fields_frame, text=label + ":").grid(row=i, column=0, sticky=tk.W, pady=2)
            var = tk.StringVar()
            entry = ttk.Entry(fields_frame, textvariable=var, width=40)
            entry.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=2, padx=(10, 0))

            self.entry_vars[key] = var
            self.entries[key] = entry

            # Add trace to update calculations when input fields change
            var.trace_add("write", lambda name, index, mode, var=var: self.calculate_projections())

        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=6, column=0, columnspan=3, pady=20)

        # Save, Clear, Validate, and Load Defaults buttons
        save_btn = ttk.Button(buttons_frame, text="Save to JSON", command=self.save_data)
        save_btn.grid(row=0, column=0, padx=5)

        validate_btn = ttk.Button(buttons_frame, text="Validate Data", command=self.validate_data)
        validate_btn.grid(row=0, column=1, padx=5)

        clear_btn = ttk.Button(buttons_frame, text="Clear All", command=self.clear_data)
        clear_btn.grid(row=0, column=2, padx=5)

        defaults_btn = ttk.Button(buttons_frame, text="Load Defaults", command=self.load_defaults)
        defaults_btn.grid(row=0, column=3, padx=5)

        calculate_btn = ttk.Button(buttons_frame, text="Calculate Financials", command=self.calculate_projections,
                                   style='Accent.TButton')
        calculate_btn.grid(row=0, column=4, padx=5)

        # Financial Projections Output Pane
        output_frame = ttk.LabelFrame(main_frame, text="Financial Projections", padding="15")
        output_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=20)
        output_frame.columnconfigure(1, weight=1)  # Allow output values to expand

        output_fields = [
            ("Gross Potential Income (GPI)", "gpi"),
            ("Vacancy and Credit Loss (V&C)", "vc"),
            ("Effective Gross Income (EGI)", "egi"),
            ("Net Operating Income (NOI)", "noi"),
            ("Capitalization Rate (Cap Rate)", "cap_rate"),
            ("Debt Service (Mortgage Payment)", "debt_service"),
            ("Cash Flow Before Taxes (CFBT)", "cfbt"),
            ("Cash-on-Cash Return (CoC)", "coc_return"),
            ("Gross Rent Multiplier (GRM)", "grm"),
            ("Debt Service Coverage Ratio (DSCR)", "dscr")
        ]

        for i, (label, key) in enumerate(output_fields):
            ttk.Label(output_frame, text=label + ":", font=('Arial', 10, 'bold')).grid(row=i, column=0, sticky=tk.W,
                                                                                       pady=2)
            ttk.Label(output_frame, textvariable=self.calculated_outputs[key], font=('Arial', 10)).grid(row=i, column=1,
                                                                                                        sticky=tk.W,
                                                                                                        pady=2,
                                                                                                        padx=(10, 0))

        # PDF content preview
        preview_frame = ttk.LabelFrame(main_frame, text="PDF Content Preview", padding="15")
        preview_frame.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(20, 0))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)

        self.content_text = scrolledtext.ScrolledText(preview_frame, height=10, width=70, wrap=tk.WORD)
        self.content_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights for resizing
        main_frame.rowconfigure(5, weight=1)  # Input fields frame
        main_frame.rowconfigure(7, weight=1)  # Output fields frame
        main_frame.rowconfigure(8, weight=1)  # PDF preview frame

    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select MLS PDF File",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filename:
            self.file_path_var.set(filename)
            self.status_var.set(f"Selected: {os.path.basename(filename)}")

    def extract_data_threaded(self):
        # Run extraction in a separate thread to prevent UI freezing
        thread = threading.Thread(target=self.extract_data)
        thread.daemon = True
        thread.start()

    def extract_data(self):
        if not self.pdf_processor.supported_library:
            self.root.after(0, lambda: messagebox.showerror("Error",
                                                            "PDF processing library not found. Please install pdfplumber or PyPDF2:\npip install pdfplumber"))
            return

        file_path = self.file_path_var.get()
        if not file_path:
            self.root.after(0, lambda: messagebox.showerror("Error", "Please select a PDF file"))
            return

        try:
            self.root.after(0, lambda: self.progress.start())
            self.root.after(0, lambda: self.status_var.set("Extracting data from PDF..."))

            # Extract text from PDF using our processor
            text_content = self.pdf_processor.extract_text(file_path)

            # Update preview
            preview_text = text_content[:2000] + "\n..." if len(text_content) > 2000 else text_content
            self.root.after(0, lambda: self.content_text.delete(1.0, tk.END))
            self.root.after(0, lambda: self.content_text.insert(1.0, preview_text))

            # Extract data using our patterns
            extracted = extract_data_with_patterns(text_content)

            # Update UI with extracted data
            # First, load defaults to fill in any missing non-extracted fields
            self.root.after(0, self.load_defaults)
            # Then, update with extracted data which will overwrite defaults
            self.root.after(0, lambda: self.update_fields(extracted))

            self.root.after(0, lambda: self.status_var.set("Data extraction completed. Calculating financials..."))
            self.root.after(0, self.calculate_projections)  # Calculate after extraction

            logger.info(f"Successfully extracted data from {file_path}")

        except Exception as e:
            error_msg = f"Failed to extract data: {str(e)}"
            logger.error(error_msg)
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            self.root.after(0, lambda: self.status_var.set("Extraction failed"))
        finally:
            self.root.after(0, lambda: self.progress.stop())

    def validate_data(self):
        """Validate all entered data"""
        data = {field: var.get() for field, var in self.entry_vars.items()}
        errors = self.validator.validate_all_fields(data)

        if errors:
            error_msg = "Validation errors found:\n\n"
            for field, error in errors.items():
                error_msg += f"• {error}\n"
            messagebox.showerror("Validation Errors", error_msg)
        else:
            messagebox.showinfo("Validation Success", "All data is valid!")
            self.calculate_projections()  # Calculate after successful validation

    def load_defaults(self):
        """Load default values for common fields"""
        for field_label, field_key in GUI_FIELD_ORDER:  # Iterate through the defined order
            if field_key in self.entry_vars:  # Only set if the field exists in the GUI
                current_value = self.entry_vars[field_key].get()
                default_value = DEFAULT_VALUES.get(field_key, '')  # Get default, or empty string if not defined
                # Only load default if the field is currently empty or 'N/A'
                if not current_value or current_value == "N/A":
                    self.entry_vars[field_key].set(default_value)
        self.status_var.set("Default values loaded. Calculating financials...")
        self.calculate_projections()  # Calculate after loading defaults

    def update_fields(self, extracted_data):
        """Update UI fields with extracted data, overwriting existing values."""
        for field, value in extracted_data.items():
            if field in self.entry_vars and value is not None:
                self.entry_vars[field].set(value)

    def calculate_projections(self):
        """Calculate and update financial projection outputs."""
        # Get all current input values
        inputs = {}
        for key, var in self.entry_vars.items():
            value = var.get().strip().replace('$', '').replace(',', '')
            if value == "":
                inputs[key] = None
            else:
                try:
                    # Use a general numeric conversion for safety before specific type casting
                    numeric_value = float(value)
                    if key in INTEGER_FIELDS:  # Use imported INTEGER_FIELDS
                        inputs[key] = int(numeric_value)
                    elif key in PERCENTAGE_FIELDS:  # Use imported PERCENTAGE_FIELDS
                        inputs[key] = numeric_value
                    elif key in NUMERIC_FIELDS:  # Use imported NUMERIC_FIELDS
                        inputs[key] = numeric_value
                    else:  # Fallback for any other unexpected field types
                        inputs[key] = numeric_value
                except ValueError:
                    inputs[key] = None  # Mark as invalid if conversion fails

        # Reset all calculated outputs to N/A
        for key in self.calculated_outputs:
            self.calculated_outputs[key].set("N/A")

        try:
            # 1. Gross Potential Income (GPI)
            # Prioritize Gross Scheduled Income if available, otherwise use units * monthly rent
            gross_scheduled_income = inputs.get('gross_scheduled_income')
            num_units = inputs.get('number_of_units')
            monthly_rent_per_unit = inputs.get('monthly_rent_per_unit')
            purchase_price = inputs.get('purchase_price')

            gpi = None
            if gross_scheduled_income is not None:
                gpi = gross_scheduled_income
                self.status_var.set("Using Gross Scheduled Income for GPI.")
            elif num_units is not None and monthly_rent_per_unit is not None:
                gpi = num_units * monthly_rent_per_unit * 12

            if gpi is None:  # Exit if GPI cannot be calculated
                self.status_var.set(
                    "Cannot calculate GPI. Needs 'Number of Units' AND 'Monthly Rent per Unit' OR 'Gross Scheduled Income'.")
                return
            self.calculated_outputs['gpi'].set(f"${gpi:,.2f}")

            # 2. Vacancy and Credit Loss (V&C)
            vacancy_rate = inputs.get('vacancy_rate')
            # If vacancy rate is not extracted, use the default from config.py
            if vacancy_rate is None:
                try:
                    vacancy_rate = float(DEFAULT_VALUES.get('vacancy_rate', '0'))
                    # No need to update GUI here, load_defaults handles it on startup/extract
                except ValueError:
                    vacancy_rate = 0.0  # Fallback if default is also invalid

            vc = gpi * (vacancy_rate / 100)
            self.calculated_outputs['vc'].set(f"${vc:,.2f}")

            # 3. Effective Gross Income (EGI)
            egi = gpi - vc
            self.calculated_outputs['egi'].set(f"${egi:,.2f}")

            # 4. Net Operating Income (NOI)
            # Fetch all expenses, ensuring they are numbers, defaulting to 0 if not present/invalid
            property_taxes = inputs.get('property_taxes') or float(DEFAULT_VALUES.get('property_taxes', '0') or '0')
            insurance = inputs.get('insurance') or float(DEFAULT_VALUES.get('insurance', '0') or '0')
            property_management_fees = inputs.get('property_management_fees') or float(
                DEFAULT_VALUES.get('property_management_fees', '0') or '0')
            maintenance_repairs = inputs.get('maintenance_repairs') or float(
                DEFAULT_VALUES.get('maintenance_repairs', '0') or '0')
            utilities = inputs.get('utilities') or float(DEFAULT_VALUES.get('utilities', '0') or '0')

            expenses = (property_taxes + insurance + property_management_fees +
                        maintenance_repairs + utilities)

            noi = egi - expenses
            self.calculated_outputs['noi'].set(f"${noi:,.2f}")

            # 5. Capitalization Rate (Cap Rate)
            if purchase_price is None:  # purchase_price might not be extracted from PDF
                purchase_price = float(DEFAULT_VALUES.get('purchase_price', '0') or '0')

            if purchase_price > 0:
                cap_rate = (noi / purchase_price) * 100
                self.calculated_outputs['cap_rate'].set(f"{cap_rate:.2f}%")
            else:
                self.calculated_outputs['cap_rate'].set("N/A (Purchase Price Missing/Zero)")

            # 6. Debt Service (Mortgage Payment)
            down_payment_percent = inputs.get('down_payment') or float(DEFAULT_VALUES.get('down_payment', '0') or '0')
            interest_rate = inputs.get('interest_rate') or float(DEFAULT_VALUES.get('interest_rate', '0') or '0')
            loan_terms_years = inputs.get('loan_terms_years') or int(
                float(DEFAULT_VALUES.get('loan_terms_years', '0') or '0'))

            mortgage_payment = None
            if purchase_price is not None and purchase_price > 0 and down_payment_percent is not None and \
                    interest_rate is not None and loan_terms_years is not None and loan_terms_years > 0:

                down_payment_amount = purchase_price * (down_payment_percent / 100)
                loan_amount = purchase_price - down_payment_amount

                if loan_amount <= 0:
                    self.calculated_outputs['debt_service'].set("N/A (Loan Amount Zero/Negative)")
                else:
                    if interest_rate == 0:
                        mortgage_payment = loan_amount / (loan_terms_years * 12) if (loan_terms_years * 12) > 0 else 0
                    else:
                        monthly_interest_rate = (interest_rate / 100) / 12
                        num_payments = loan_terms_years * 12

                        if monthly_interest_rate == 0:
                            mortgage_payment = loan_amount / num_payments if num_payments > 0 else 0
                        else:
                            try:
                                mortgage_payment = loan_amount * (
                                            monthly_interest_rate * (1 + monthly_interest_rate) ** num_payments) / \
                                                   ((1 + monthly_interest_rate) ** num_payments - 1)
                            except ZeroDivisionError:
                                mortgage_payment = float('inf')

                if mortgage_payment is not None and mortgage_payment != float('inf'):
                    self.calculated_outputs['debt_service'].set(f"${mortgage_payment:,.2f}")
                else:
                    self.calculated_outputs['debt_service'].set("N/A (Loan Calculation Issue)")
            else:
                self.calculated_outputs['debt_service'].set("N/A (Loan Inputs Missing/Invalid)")

            # 7. Cash Flow Before Taxes (CFBT)
            cfbt = None
            debt_service_str = self.calculated_outputs['debt_service'].get()
            if debt_service_str and "N/A" not in debt_service_str and noi is not None:
                try:
                    monthly_mortgage_payment = float(debt_service_str.replace('$', '').replace(',', ''))
                    cfbt = noi - (monthly_mortgage_payment * 12)
                    self.calculated_outputs['cfbt'].set(f"${cfbt:,.2f}")
                except ValueError:
                    self.calculated_outputs['cfbt'].set("N/A (Invalid Debt Service Value)")
            else:
                self.calculated_outputs['cfbt'].set("N/A (NOI or Debt Service Missing)")

            # 8. Cash-on-Cash Return (CoC)
            coc_return = None
            if cfbt is not None and purchase_price is not None and purchase_price > 0 and down_payment_percent is not None:
                initial_equity_invested = purchase_price * (down_payment_percent / 100)
                if initial_equity_invested > 0:
                    coc_return = (cfbt / initial_equity_invested) * 100
                    self.calculated_outputs['coc_return'].set(f"{coc_return:.2f}%")
                else:
                    self.calculated_outputs['coc_return'].set("N/A (Initial Equity Zero/Negative)")
            else:
                self.calculated_outputs['coc_return'].set("N/A (CFBT or Equity Inputs Missing)")

            # 9. Gross Rent Multiplier (GRM)
            grm = None
            if purchase_price is not None and purchase_price > 0 and gpi is not None and gpi > 0:
                grm = purchase_price / gpi
                self.calculated_outputs['grm'].set(f"{grm:.2f}")
            else:
                self.calculated_outputs['grm'].set("N/A (Purchase Price or GPI Missing/Zero)")

            # 10. Debt Service Coverage Ratio (DSCR)
            dscr = None
            if noi is not None and debt_service_str and "N/A" not in debt_service_str:
                try:
                    monthly_mortgage_payment = float(debt_service_str.replace('$', '').replace(',', ''))
                    annual_debt_service = monthly_mortgage_payment * 12
                    if annual_debt_service > 0:
                        dscr = noi / annual_debt_service
                        self.calculated_outputs['dscr'].set(f"{dscr:.2f}")
                    else:
                        self.calculated_outputs['dscr'].set("N/A (Annual Debt Service Zero/Negative)")
                except ValueError:
                    self.calculated_outputs['dscr'].set("N/A (Invalid Debt Service Value)")
            else:
                self.calculated_outputs['dscr'].set("N/A (NOI or Debt Service Missing/Zero)")

            self.status_var.set("Financial projections updated.")

        except ValueError as ve:
            self.status_var.set(f"Calculation Error: {ve}")
            logger.warning(f"Calculation error: {ve}")
        except Exception as e:
            self.status_var.set(f"An unexpected calculation error occurred: {str(e)}")
            logger.error(f"Unexpected calculation error: {e}")

    def save_data(self):
        """Save extracted and current input data to JSON file"""
        # Get all current input data
        data_to_save = {field: var.get() for field, var in self.entry_vars.items()}

        # Validate data first
        errors = self.validator.validate_all_fields(data_to_save)

        if errors:
            if not messagebox.askyesno("Validation Errors",
                                       "There are validation errors. Save anyway?"):
                return

        # Add metadata
        data_to_save['extraction_date'] = datetime.now().isoformat()
        data_to_save['source_file'] = self.file_path_var.get()
        data_to_save['app_version'] = APP_VERSION

        # Add calculated outputs to the saved data
        calculated_data = {key: var.get() for key, var in self.calculated_outputs.items()}
        data_to_save['calculated_financials'] = calculated_data

        # Default filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"mls_data_{timestamp}.json"

        filename = filedialog.asksaveasfilename(
            title="Save Extracted Data",
            initialdir=EXPORTS_DIR,
            initialfile=default_filename,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            try:
                # Ensure the export directory exists
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                with open(filename, 'w') as f:
                    json.dump(data_to_save, f, indent=2)
                messagebox.showinfo("Success", f"Data saved to {filename}")
                logger.info(f"Data saved to {filename}")
            except Exception as e:
                error_msg = f"Failed to save data: {str(e)}"
                messagebox.showerror("Error", error_msg)
                logger.error(error_msg)

    def clear_data(self):
        """Clear all fields"""
        for var in self.entry_vars.values():
            var.set("")
        for var in self.calculated_outputs.values():
            var.set("N/A")  # Clear calculated outputs too
        self.content_text.delete(1.0, tk.END)
        self.file_path_var.set("")  # Clear file path as well
        self.status_var.set("Ready")

    def run(self):
        """Start the application"""
        if not self.pdf_processor.supported_library:
            messagebox.showwarning(
                "Missing Dependencies",
                "PDF processing library not found.\n\nPlease install required packages:\n"
                "pip install pdfplumber\n\nThe application will still run but PDF extraction will not work."
            )

        logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
        self.root.mainloop()


def main():
    app = MLSDataExtractor()
    app.run()


if __name__ == "__main__":
    main()
