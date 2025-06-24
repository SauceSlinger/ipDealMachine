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


def load_defaults(self):
    """Load default values for common fields"""
    for field, default_value in DEFAULT_VALUES.items():
        if field in self.entry_vars and not self.entry_vars[field].get():
            self.entry_vars[field].set(default_value)
    self.status_var.set("Default values loaded")


def update_fields(self, extracted_data):
    """Update UI fields with extracted data"""
    for field, value in extracted_data.items():
        if field in self.entry_vars and value:
            self.entry_vars[field].set(value)  # !/usr/bin/env python3


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

# Import our custom modules
from config import APP_NAME, APP_VERSION, WINDOW_SIZE, EXPORTS_DIR, DEFAULT_VALUES
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

        # Initialize processors
        self.pdf_processor = PDFProcessor()
        self.validator = DataValidator()

        # Data structure for extracted information
        self.extracted_data = {
            'number_of_units': '',
            'monthly_rent_per_unit': '',
            'vacancy_rate': '',
            'property_taxes': '',
            'insurance': '',
            'property_management_fees': '',
            'maintenance_repairs': '',
            'utilities': '',
            'purchase_price': '',
            'down_payment': '',
            'interest_rate': '',
            'loan_terms_years': ''
        }

        self.setup_ui()

    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Title
        title_label = ttk.Label(main_frame, text=f"{APP_NAME} v{APP_VERSION}",
                                font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

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
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.grid(row=4, column=0, columnspan=3, pady=5)

        # Data fields frame
        fields_frame = ttk.LabelFrame(main_frame, text="Extracted Data", padding="10")
        fields_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=20)
        fields_frame.columnconfigure(1, weight=1)

        # Create entry fields for each data point
        self.entry_vars = {}
        self.entries = {}

        fields = [
            ("Number of Units", "number_of_units"),
            ("Monthly Rent per Unit ($)", "monthly_rent_per_unit"),
            ("Vacancy Rate (%)", "vacancy_rate"),
            ("Property Taxes ($)", "property_taxes"),
            ("Insurance ($)", "insurance"),
            ("Property Management Fees ($)", "property_management_fees"),
            ("Maintenance and Repairs ($)", "maintenance_repairs"),
            ("Utilities ($)", "utilities"),
            ("Purchase Price ($)", "purchase_price"),
            ("Down Payment ($)", "down_payment"),
            ("Interest Rate (%)", "interest_rate"),
            ("Loan Terms (Years)", "loan_terms_years")
        ]

        for i, (label, key) in enumerate(fields):
            ttk.Label(fields_frame, text=label + ":").grid(row=i, column=0, sticky=tk.W, pady=2)
            var = tk.StringVar()
            entry = ttk.Entry(fields_frame, textvariable=var, width=30)
            entry.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=2, padx=(10, 0))

            self.entry_vars[key] = var
            self.entries[key] = entry

        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=6, column=0, columnspan=3, pady=20)

        # Save, Clear, and Validate buttons
        save_btn = ttk.Button(buttons_frame, text="Save to JSON", command=self.save_data)
        save_btn.grid(row=0, column=0, padx=5)

        validate_btn = ttk.Button(buttons_frame, text="Validate Data", command=self.validate_data)
        validate_btn.grid(row=0, column=1, padx=5)

        clear_btn = ttk.Button(buttons_frame, text="Clear All", command=self.clear_data)
        clear_btn.grid(row=0, column=2, padx=5)

        defaults_btn = ttk.Button(buttons_frame, text="Load Defaults", command=self.load_defaults)
        defaults_btn.grid(row=0, column=3, padx=5)

        # PDF content preview
        preview_frame = ttk.LabelFrame(main_frame, text="PDF Content Preview", padding="10")
        preview_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(20, 0))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)

        self.content_text = scrolledtext.ScrolledText(preview_frame, height=10, width=70)
        self.content_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights for resizing
        main_frame.rowconfigure(5, weight=1)
        main_frame.rowconfigure(7, weight=1)

    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select MLS PDF File",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filename:
            self.file_path_var.set(filename)

    def extract_data_threaded(self):
        # Run extraction in a separate thread to prevent UI freezing
        thread = threading.Thread(target=self.extract_data)
        thread.daemon = True
        thread.start()

    def extract_data(self):
        if not self.pdf_processor.supported_library:
            messagebox.showerror("Error",
                                 "PDF processing library not found. Please install pdfplumber or PyPDF2:\npip install pdfplumber")
            return

        file_path = self.file_path_var.get()
        if not file_path:
            messagebox.showerror("Error", "Please select a PDF file")
            return

        try:
            self.progress.start()
            self.status_var.set("Extracting data from PDF...")

            # Extract text from PDF using our processor
            text_content = self.pdf_processor.extract_text(file_path)

            # Update preview
            preview_text = text_content[:2000] + "..." if len(text_content) > 2000 else text_content
            self.root.after(0, lambda: self.content_text.delete(1.0, tk.END))
            self.root.after(0, lambda: self.content_text.insert(1.0, preview_text))

            # Extract data using our patterns
            extracted = extract_data_with_patterns(text_content)

            # Update UI with extracted data
            self.root.after(0, lambda: self.update_fields(extracted))
            self.root.after(0, lambda: self.status_var.set("Data extraction completed"))

            logger.info(f"Successfully extracted data from {file_path}")

        except Exception as e:
            error_msg = f"Failed to extract data: {str(e)}"
            logger.error(error_msg)
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            self.root.after(0, lambda: self.status_var.set("Extraction failed"))
        finally:
            self.root.after(0, lambda: self.progress.stop())

    def extract_pdf_text(self, file_path):
        text = ""

        if PDF_LIBRARY == "pdfplumber":
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

        elif PDF_LIBRARY == "PyPDF2":
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"

        return text

    def parse_mls_data(self, text):
        """Parse MLS data using regex patterns"""
        extracted = {}

        # Define regex patterns for common MLS fields
        patterns = {
            'number_of_units': [
                r'units?\s*[:=]\s*(\d+)',
                r'(\d+)\s*units?',
                r'unit\s*count\s*[:=]\s*(\d+)',
                r'total\s*units?\s*[:=]\s*(\d+)'
            ],
            'monthly_rent_per_unit': [
                r'rent\s*per\s*unit\s*[:=]\s*\$?([\d,]+)',
                r'monthly\s*rent\s*[:=]\s*\$?([\d,]+)',
                r'rental\s*income\s*[:=]\s*\$?([\d,]+)',
                r'\$?([\d,]+)\s*per\s*month'
            ],
            'vacancy_rate': [
                r'vacancy\s*rate?\s*[:=]\s*(\d+(?:\.\d+)?)\s*%?',
                r'vacant\s*[:=]\s*(\d+(?:\.\d+)?)\s*%?'
            ],
            'property_taxes': [
                r'property\s*tax(?:es)?\s*[:=]\s*\$?([\d,]+)',
                r'taxes?\s*[:=]\s*\$?([\d,]+)',
                r'annual\s*tax(?:es)?\s*[:=]\s*\$?([\d,]+)'
            ],
            'insurance': [
                r'insurance\s*[:=]\s*\$?([\d,]+)',
                r'property\s*insurance\s*[:=]\s*\$?([\d,]+)'
            ],
            'property_management_fees': [
                r'management\s*fee?s?\s*[:=]\s*\$?([\d,]+)',
                r'property\s*management\s*[:=]\s*\$?([\d,]+)',
                r'mgmt\s*fee?s?\s*[:=]\s*\$?([\d,]+)'
            ],
            'maintenance_repairs': [
                r'maintenance\s*(?:and\s*)?repairs?\s*[:=]\s*\$?([\d,]+)',
                r'repair\s*(?:and\s*)?maintenance\s*[:=]\s*\$?([\d,]+)',
                r'maint\s*[:=]\s*\$?([\d,]+)'
            ],
            'utilities': [
                r'utilities\s*[:=]\s*\$?([\d,]+)',
                r'utility\s*costs?\s*[:=]\s*\$?([\d,]+)'
            ],
            'purchase_price': [
                r'purchase\s*price\s*[:=]\s*\$?([\d,]+)',
                r'asking\s*price\s*[:=]\s*\$?([\d,]+)',
                r'list\s*price\s*[:=]\s*\$?([\d,]+)',
                r'price\s*[:=]\s*\$?([\d,]+)'
            ],
            'down_payment': [
                r'down\s*payment\s*[:=]\s*\$?([\d,]+)',
                r'down\s*[:=]\s*\$?([\d,]+)'
            ],
            'interest_rate': [
                r'interest\s*rate\s*[:=]\s*(\d+(?:\.\d+)?)\s*%?',
                r'rate\s*[:=]\s*(\d+(?:\.\d+)?)\s*%?'
            ],
            'loan_terms_years': [
                r'loan\s*term\s*[:=]\s*(\d+)\s*years?',
                r'term\s*[:=]\s*(\d+)\s*years?',
                r'(\d+)\s*year\s*loan'
            ]
        }

        # Clean text for better matching
        text_clean = re.sub(r'\s+', ' ', text.lower())

        for field, field_patterns in patterns.items():
            for pattern in field_patterns:
                match = re.search(pattern, text_clean, re.IGNORECASE)
                if match:
                    value = match.group(1).replace(',', '')
                    extracted[field] = value
                    break  # Use first match found

        return extracted

    def save_data(self):
        """Save extracted data to JSON file"""
        # Validate data first
        data = {field: var.get() for field, var in self.entry_vars.items()}
        errors = self.validator.validate_all_fields(data)

        if errors:
            if not messagebox.askyesno("Validation Errors",
                                       "There are validation errors. Save anyway?"):
                return

        # Add metadata
        data['extraction_date'] = datetime.now().isoformat()
        data['source_file'] = self.file_path_var.get()
        data['app_version'] = APP_VERSION

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
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
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
        self.content_text.delete(1.0, tk.END)
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