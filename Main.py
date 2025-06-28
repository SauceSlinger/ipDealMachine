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
    GUI_FIELD_ORDER, NUMERIC_FIELDS, PERCENTAGE_FIELDS, INTEGER_FIELDS,
    # --- IMPORT COLOR CONSTANTS ---
    C21_GOLD, C21_BLACK, C21_DARK_GRAY, C21_WHITE, C21_LIGHT_GRAY
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
        self.root.geometry(WINDOW_SIZE)  # Use WINDOW_SIZE from config

        # Define Century 21 inspired color palette - NOW IMPORTED FROM CONFIG
        # self.C21_GOLD = '#DAA520' # No longer needed here
        # etc.

        # Apply a theme for a modern look
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Configure styles for various widgets with Century 21 colors
        self.style.configure('TFrame', background=C21_LIGHT_GRAY)
        self.style.configure('TLabel', background=C21_LIGHT_GRAY, foreground=C21_DARK_GRAY, font=('Arial', 10))

        # Standard Buttons (Save, Validate, Clear, Load Defaults)
        self.style.configure('TButton',
                             font=('Arial', 10, 'bold'),
                             padding=8,
                             relief='flat',
                             background=C21_DARK_GRAY,
                             foreground=C21_WHITE,
                             borderwidth=1,
                             focusthickness=0)
        self.style.map('TButton',
                       background=[('active', '#555555'), ('pressed', '#111111')],
                       foreground=[('active', C21_WHITE)])

        # Accent Buttons (Extract Data, Calculate Financials)
        self.style.configure('Accent.TButton',
                             background=C21_GOLD,
                             foreground=C21_BLACK,
                             relief='flat',
                             font=('Arial', 10, 'bold'),
                             padding=8,
                             borderwidth=1,
                             focusthickness=0)
        self.style.map('Accent.TButton',
                       background=[('active', '#C09010'), ('pressed', '#A07000')],
                       foreground=[('active', C21_BLACK)])

        # Entry Fields
        self.style.configure('TEntry',
                             fieldbackground=C21_WHITE,
                             foreground=C21_BLACK,
                             relief='solid',
                             borderwidth=1,
                             padding=3)

        # Label Frames
        self.style.configure('TLabelframe',
                             background=C21_LIGHT_GRAY,
                             relief='solid',
                             borderwidth=1,
                             padding=15)
        self.style.configure('TLabelframe.Label',
                             background=C21_LIGHT_GRAY,
                             foreground=C21_GOLD,
                             font=('Arial', 13, 'bold'))

        # Progress Bar
        self.style.configure('TProgressbar',
                             thickness=10,
                             background=C21_GOLD,
                             troughcolor=C21_LIGHT_GRAY)

        # Initialize processors
        self.pdf_processor = PDFProcessor()
        self.validator = DataValidator()

        # Data structure for extracted information (input fields)
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
        self.root.after(100, self.load_defaults_and_calculate)

    def load_defaults_and_calculate(self):
        """Loads defaults and then triggers a calculation. Used on app start."""
        self.load_defaults()
        self.calculate_projections()

    def setup_ui(self):
        # Main container frame for overall padding
        main_container = ttk.Frame(self.root, padding="20", style='TFrame')
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Title at the top, spanning both columns
        title_label = ttk.Label(main_container, text=f"{APP_NAME} v{APP_VERSION}",
                                font=('Arial', 20, 'bold'), anchor='center',
                                background=C21_GOLD, foreground=C21_BLACK,
                                relief='flat', padding=15)
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 25), sticky=tk.E + tk.W)

        # Create two main columns within the main_container
        left_panel = ttk.Frame(main_container, padding="15", style='TFrame')
        left_panel.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 15))
        left_panel.columnconfigure(1, weight=1)
        main_container.columnconfigure(0, weight=1)

        right_panel = ttk.Frame(main_container, padding="15", style='TFrame')
        right_panel.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(15, 0))
        right_panel.columnconfigure(1, weight=1)
        main_container.columnconfigure(1, weight=1)

        # --- Left Panel Content ---
        current_row = 0

        # File selection
        ttk.Label(left_panel, text="PDF File:", font=('Arial', 10, 'bold'), foreground=C21_DARK_GRAY).grid(
            row=current_row, column=0, sticky=tk.W, pady=5)
        self.file_path_var = tk.StringVar()
        self.file_entry = ttk.Entry(left_panel, textvariable=self.file_path_var, width=50)
        self.file_entry.grid(row=current_row, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 5))

        browse_btn = ttk.Button(left_panel, text="Browse", command=self.browse_file)
        browse_btn.grid(row=current_row, column=2, pady=5)
        current_row += 1

        # Extract button
        extract_btn = ttk.Button(left_panel, text="Extract Data",
                                 command=self.extract_data_threaded, style='Accent.TButton')
        extract_btn.grid(row=current_row, column=0, columnspan=3, pady=15, sticky=tk.E + tk.W)
        current_row += 1

        # Progress bar
        self.progress = ttk.Progressbar(left_panel, mode='indeterminate')
        self.progress.grid(row=current_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        current_row += 1

        # Status label
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(left_panel, textvariable=self.status_var, font=('Arial', 9, 'italic'),
                                 foreground=C21_DARK_GRAY)
        status_label.grid(row=current_row, column=0, columnspan=3, pady=5)
        current_row += 1

        # Input Data fields frame
        fields_frame = ttk.LabelFrame(left_panel, text="Input Data", padding="15")
        fields_frame.grid(row=current_row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 20))
        fields_frame.columnconfigure(1, weight=1)
        left_panel.rowconfigure(current_row, weight=1)

        # Create entry fields for each data point using GUI_FIELD_ORDER
        self.entry_vars = {}
        self.entries = {}

        for i, (label, key) in enumerate(GUI_FIELD_ORDER):
            ttk.Label(fields_frame, text=label + ":", foreground=C21_DARK_GRAY).grid(row=i, column=0, sticky=tk.W,
                                                                                     pady=3)
            var = tk.StringVar()
            entry = ttk.Entry(fields_frame, textvariable=var, width=40)
            entry.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=3, padx=(10, 0))

            self.entry_vars[key] = var
            self.entries[key] = entry

            var.trace_add("write", lambda name, index, mode, var=var: self.calculate_projections())
        current_row += 1

        # Buttons frame (for Save, Clear, Validate, Load Defaults, Calculate)
        buttons_frame = ttk.Frame(left_panel, style='TFrame')
        buttons_frame.grid(row=current_row, column=0, columnspan=3, pady=15)

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

        # --- Right Panel Content ---
        right_panel_row = 0

        # Financial Projections Output Pane
        output_frame = ttk.LabelFrame(right_panel, text="Financial Projections", padding="15")
        output_frame.grid(row=right_panel_row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))
        output_frame.columnconfigure(1, weight=1)
        right_panel.rowconfigure(right_panel_row, weight=1)

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
            ttk.Label(output_frame, text=label + ":", font=('Arial', 10, 'bold'), foreground=C21_DARK_GRAY).grid(row=i,
                                                                                                                 column=0,
                                                                                                                 sticky=tk.W,
                                                                                                                 pady=3)
            ttk.Label(output_frame, textvariable=self.calculated_outputs[key], font=('Arial', 10, 'bold'),
                      foreground=C21_BLACK).grid(row=i, column=1, sticky=tk.W, pady=3, padx=(10, 0))
        right_panel_row += 1

        # PDF content preview
        preview_frame = ttk.LabelFrame(right_panel, text="PDF Content Preview", padding="15")
        preview_frame.grid(row=right_panel_row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 0))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        right_panel.rowconfigure(right_panel_row, weight=1)

        self.content_text = scrolledtext.ScrolledText(preview_frame, height=10, width=70, wrap=tk.WORD,
                                                      font=('Courier New', 9),
                                                      background=C21_WHITE,
                                                      foreground=C21_BLACK,
                                                      relief='solid', borderwidth=1)
        self.content_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Final main_container row configuration to allow content to expand
        main_container.rowconfigure(1, weight=1)

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
            self.root.after(0, self.load_defaults)
            self.root.after(0, lambda: self.update_fields(extracted))

            self.root.after(0, lambda: self.status_var.set("Data extraction completed. Calculating financials..."))
            self.root.after(0, self.calculate_projections)

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
            self.calculate_projections()

    def load_defaults(self):
        """Load default values for common fields"""
        for field_label, field_key in GUI_FIELD_ORDER:
            if field_key in self.entry_vars:
                current_value = self.entry_vars[field_key].get()
                default_value = DEFAULT_VALUES.get(field_key, '')
                if not current_value or current_value == "N/A":
                    self.entry_vars[field_key].set(default_value)
        self.status_var.set("Default values loaded. Calculating financials...")
        self.calculate_projections()

    def update_fields(self, extracted_data):
        """Update UI fields with extracted data, overwriting existing values."""
        for field, value in extracted_data.items():
            if field in self.entry_vars and value is not None:
                self.entry_vars[field].set(value)

    def calculate_projections(self):
        """Calculate and update financial projection outputs."""
        inputs = {}
        for key, var in self.entry_vars.items():
            value = var.get().strip().replace('$', '').replace(',', '')
            if value == "":
                inputs[key] = None
            else:
                try:
                    numeric_value = float(value)
                    if key in INTEGER_FIELDS:
                        inputs[key] = int(numeric_value)
                    elif key in PERCENTAGE_FIELDS:
                        inputs[key] = numeric_value
                    elif key in NUMERIC_FIELDS:
                        inputs[key] = numeric_value
                    else:
                        inputs[key] = numeric_value
                except ValueError:
                    inputs[key] = None

        for key in self.calculated_outputs:
            self.calculated_outputs[key].set("N/A")

        try:
            # 1. Gross Potential Income (GPI)
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

            if gpi is None:
                self.status_var.set(
                    "Cannot calculate GPI. Needs 'Number of Units' AND 'Monthly Rent per Unit' OR 'Gross Scheduled Income'.")
                return
            self.calculated_outputs['gpi'].set(f"${gpi:,.2f}")

            # 2. Vacancy and Credit Loss (V&C)
            vacancy_rate = inputs.get('vacancy_rate')
            if vacancy_rate is None:
                try:
                    vacancy_rate = float(DEFAULT_VALUES.get('vacancy_rate', '0'))
                except ValueError:
                    vacancy_rate = 0.0

            vc = gpi * (vacancy_rate / 100)
            self.calculated_outputs['vc'].set(f"${vc:,.2f}")

            # 3. Effective Gross Income (EGI)
            egi = gpi - vc
            self.calculated_outputs['egi'].set(f"${egi:,.2f}")

            # 4. Net Operating Income (NOI)
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
            if purchase_price is None:
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
        data_to_save = {field: var.get() for field, var in self.entry_vars.items()}

        errors = self.validator.validate_all_fields(data_to_save)

        if errors:
            if not messagebox.askyesno("Validation Errors",
                                       "There are validation errors. Save anyway?"):
                return

        data_to_save['extraction_date'] = datetime.now().isoformat()
        data_to_save['source_file'] = self.file_path_var.get()
        data_to_save['app_version'] = APP_VERSION

        calculated_data = {key: var.get() for key, var in self.calculated_outputs.items()}
        data_to_save['calculated_financials'] = calculated_data

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
            var.set("N/A")
        self.content_text.delete(1.0, tk.END)
        self.file_path_var.set("")
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
