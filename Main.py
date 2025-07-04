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
import re

# Import our custom modules
from config import (
    APP_NAME, APP_VERSION, WINDOW_SIZE, EXPORTS_DIR, DEFAULT_VALUES,
    GUI_FIELD_ORDER, NUMERIC_FIELDS, PERCENTAGE_FIELDS, INTEGER_FIELDS,
    C21_GOLD, C21_BLACK, C21_DARK_GRAY, C21_WHITE, C21_LIGHT_GRAY,
    DATABASE_NAME,
    INPUT_COLOR_DEFAULT, INPUT_COLOR_MANUAL, INPUT_COLOR_EXTRACTED,
    OUTPUT_GRADIENT_COLORS, OUTPUT_RANGES
)
from patterns import extract_data_with_patterns
from utils.pdf_processor import PDFProcessor
from utils.data_validator import DataValidator
from utils.database import DatabaseManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLSDataExtractor:
    def __init__(self):
        # Initialize processors FIRST to ensure they exist
        self.pdf_processor = PDFProcessor()
        self.validator = DataValidator()

        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry(WINDOW_SIZE)

        # Initialize Database Manager - pass the full path to the DB file
        db_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', DATABASE_NAME)
        self.db_manager = DatabaseManager(db_file_path)
        self.current_property_id = None

        # Apply a theme for a modern look
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Configure styles for various widgets with Century 21 colors
        self.style.configure('TFrame', background=C21_LIGHT_GRAY)
        self.style.configure('TLabel', background=C21_LIGHT_GRAY, foreground=C21_DARK_GRAY, font=('Arial', 10))

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

        # Entry Fields - Base style. Removed direct background setting here.
        # This style applies to all TEntry widgets by default, but its background
        # will be overridden by specific named styles.
        self.style.configure('TEntry',
                             # Removed: background=C21_WHITE,
                             foreground=C21_BLACK,
                             relief='solid',
                             borderwidth=1,
                             padding=3)

        # --- NEW: Define specific styles for input field colors using map for fieldbackground ---
        # This maps the 'fieldbackground' option of the 'Entry.field' element.
        self.style.map('Default.TEntry', fieldbackground=[('!disabled', INPUT_COLOR_DEFAULT)])
        self.style.map('Manual.TEntry', fieldbackground=[('!disabled', INPUT_COLOR_MANUAL)])
        self.style.map('Extracted.TEntry', fieldbackground=[('!disabled', INPUT_COLOR_EXTRACTED)])
        # --- END NEW ---

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

        # Treeview (for file list)
        self.style.configure('Treeview',
                             background=C21_WHITE,
                             foreground=C21_DARK_GRAY,
                             fieldbackground=C21_WHITE,
                             rowheight=25)
        self.style.map('Treeview',
                       background=[('selected', C21_GOLD)],
                       foreground=[('selected', C21_BLACK)])
        self.style.configure('Treeview.Heading',
                             font=('Arial', 10, 'bold'),
                             background=C21_DARK_GRAY,
                             foreground=C21_WHITE,
                             relief='flat')
        self.style.map('Treeview.Heading',
                       background=[('active', '#555555')])

        self.extracted_data = {key: '' for label, key in GUI_FIELD_ORDER}
        self.input_source_status = {key: 'default' for label, key in GUI_FIELD_ORDER}

        self.calculated_outputs = {
            'gpi': tk.StringVar(value="N/A"), 'vc': tk.StringVar(value="N/A"),
            'egi': tk.StringVar(value="N/A"), 'noi': tk.StringVar(value="N/A"),
            'cap_rate': tk.StringVar(value="N/A"), 'debt_service': tk.StringVar(value="N/A"),
            'cfbt': tk.StringVar(value="N/A"), 'coc_return': tk.StringVar(value="N/A"),
            'grm': tk.StringVar(value="N/A"), 'dscr': tk.StringVar(value="N/A")
        }

        self.output_labels = {}

        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.root.after(100, self.load_defaults_and_calculate)

    def _on_closing(self):
        """Called when the window is closed. Database connections are now managed per-operation,
        so no global close is strictly necessary here, but keeping for consistency."""
        if self.db_manager:
            self.db_manager.close()
        self.root.destroy()

    def load_defaults_and_calculate(self):
        """Loads defaults and then triggers a calculation. Used on app start."""
        self.load_defaults()
        self.calculate_projections()
        self.populate_file_list()

    def setup_ui(self):
        main_container = ttk.Frame(self.root, padding="20", style='TFrame')
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        title_label = ttk.Label(main_container, text=f"{APP_NAME} v{APP_VERSION}",
                                font=('Arial', 20, 'bold'), anchor='center',
                                background=C21_GOLD, foreground=C21_BLACK,
                                relief='flat', padding=15)
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 25), sticky=tk.E + tk.W)

        left_panel = ttk.Frame(main_container, padding="15", style='TFrame')
        left_panel.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 15))
        left_panel.columnconfigure(1, weight=1)
        main_container.columnconfigure(0, weight=1)

        right_panel = ttk.Frame(main_container, padding="15", style='TFrame')
        right_panel.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(15, 0))
        right_panel.columnconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=1)

        current_row = 0

        ttk.Label(left_panel, text="PDF File:", font=('Arial', 10, 'bold'), foreground=C21_DARK_GRAY).grid(
            row=current_row, column=0, sticky=tk.W, pady=5)
        self.file_path_var = tk.StringVar()
        self.file_entry = ttk.Entry(left_panel, textvariable=self.file_path_var, width=50)
        self.file_entry.grid(row=current_row, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 5))

        browse_btn = ttk.Button(left_panel, text="Browse", command=self.browse_file)
        browse_btn.grid(row=current_row, column=2, pady=5)
        current_row += 1

        extract_btn = ttk.Button(left_panel, text="Extract Data",
                                 command=self.extract_data_threaded, style='Accent.TButton')
        extract_btn.grid(row=current_row, column=0, columnspan=3, pady=15, sticky=tk.E + tk.W)
        current_row += 1

        self.progress = ttk.Progressbar(left_panel, mode='indeterminate')
        self.progress.grid(row=current_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        current_row += 1

        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(left_panel, textvariable=self.status_var, font=('Arial', 9, 'italic'),
                                 foreground=C21_DARK_GRAY)
        status_label.grid(row=current_row, column=0, columnspan=3, pady=5)
        current_row += 1

        fields_frame = ttk.LabelFrame(left_panel, text="Input Data", padding="15")
        fields_frame.grid(row=current_row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 5))
        fields_frame.columnconfigure(1, weight=1)
        left_panel.rowconfigure(current_row, weight=1)

        self.entry_vars = {}
        self.entries = {}

        for i, (label, key) in enumerate(GUI_FIELD_ORDER):
            ttk.Label(fields_frame, text=label + ":", foreground=C21_DARK_GRAY).grid(row=i, column=0, sticky=tk.W,
                                                                                     pady=3)
            var = tk.StringVar()
            # No style specified here initially; it will be set by _update_input_field_colors
            entry = ttk.Entry(fields_frame, textvariable=var, width=40)
            entry.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=3, padx=(10, 0))

            self.entry_vars[key] = var
            self.entries[key] = entry

            var.trace_add("write", lambda name, index, mode, k=key: self._on_input_change(k))
        current_row += 1

        input_key_frame = ttk.Frame(left_panel, style='TFrame')
        input_key_frame.grid(row=current_row, column=0, columnspan=3, sticky=tk.W, pady=(5, 15), padx=(15, 0))
        ttk.Label(input_key_frame, text="Input Data Key:", font=('Arial', 9, 'bold'), foreground=C21_DARK_GRAY,
                  background=C21_LIGHT_GRAY).pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(input_key_frame, text="Default", background=INPUT_COLOR_DEFAULT, foreground=C21_BLACK, relief='solid',
                 borderwidth=1, padx=5, pady=2).pack(side=tk.LEFT, padx=5)
        tk.Label(input_key_frame, text="Manual", background=INPUT_COLOR_MANUAL, foreground=C21_BLACK, relief='solid',
                 borderwidth=1, padx=5, pady=2).pack(side=tk.LEFT, padx=5)
        tk.Label(input_key_frame, text="Extracted", background=INPUT_COLOR_EXTRACTED, foreground=C21_BLACK,
                 relief='solid', borderwidth=1, padx=5, pady=2).pack(side=tk.LEFT, padx=5)
        current_row += 1

        buttons_frame = ttk.Frame(left_panel, style='TFrame')
        buttons_frame.grid(row=current_row, column=0, columnspan=3, pady=15)

        save_btn = ttk.Button(buttons_frame, text="Save Current Data", command=self.save_current_property)
        save_btn.grid(row=0, column=0, padx=5)

        validate_btn = ttk.Button(buttons_frame, text="Validate Data", command=self.validate_data)
        validate_btn.grid(row=0, column=1, padx=5)

        clear_btn = ttk.Button(buttons_frame, text="Clear All", command=self.clear_data)
        clear_btn.grid(row=0, column=2, padx=5)

        defaults_btn = ttk.Button(buttons_frame, text="Load Defaults", command=self.load_defaults)
        defaults_btn.grid(row=0, column=3, padx=5)

        calculate_btn = ttk.Button(buttons_frame, text="Recalculate", command=self.calculate_projections,
                                   style='Accent.TButton')
        calculate_btn.grid(row=0, column=4, padx=5)

        right_panel_row = 0

        output_frame = ttk.LabelFrame(right_panel, text="Financial Projections", padding="15")
        output_frame.grid(row=right_panel_row, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 5))
        output_frame.columnconfigure(1, weight=1)
        right_panel.rowconfigure(right_panel_row, weight=1)

        output_fields = [
            ("Gross Potential Income (GPI)", "gpi"), ("Vacancy and Credit Loss (V&C)", "vc"),
            ("Effective Gross Income (EGI)", "egi"), ("Net Operating Income (NOI)", "noi"),
            ("Capitalization Rate (Cap Rate)", "cap_rate"), ("Debt Service (Mortgage Payment)", "debt_service"),
            ("Cash Flow Before Taxes (CFBT)", "cfbt"), ("Cash-on-Cash Return (CoC)", "coc_return"),
            ("Gross Rent Multiplier (GRM)", "grm"), ("Debt Service Coverage Ratio (DSCR)", "dscr")
        ]

        for i, (label, key) in enumerate(output_fields):
            ttk.Label(output_frame, text=label + ":", font=('Arial', 10, 'bold'), foreground=C21_DARK_GRAY).grid(row=i,
                                                                                                                 column=0,
                                                                                                                 sticky=tk.W,
                                                                                                                 pady=3)
            output_label = tk.Label(output_frame, textvariable=self.calculated_outputs[key],
                                    font=('Arial', 10, 'bold'), foreground=C21_BLACK,
                                    background=C21_WHITE,
                                    relief='solid', borderwidth=1, padx=5, pady=2)
            output_label.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=3, padx=(10, 0))
            self.output_labels[key] = output_label
        right_panel_row += 1

        output_key_frame = ttk.Frame(right_panel, style='TFrame')
        output_key_frame.grid(row=right_panel_row, column=0, sticky=tk.W, pady=(5, 15), padx=(15, 0))
        ttk.Label(output_key_frame, text="Output Value Key:", font=('Arial', 9, 'bold'), foreground=C21_DARK_GRAY,
                  background=C21_LIGHT_GRAY).pack(side=tk.LEFT, padx=(0, 10))

        for i, color in enumerate(OUTPUT_GRADIENT_COLORS):
            text = ""
            if i == 0:
                text = "Worst"
            elif i == len(OUTPUT_GRADIENT_COLORS) - 1:
                text = "Best"
            elif i == len(OUTPUT_GRADIENT_COLORS) // 2:
                text = "Neutral"

            tk.Label(output_key_frame, text=text, background=color, foreground=C21_BLACK, relief='solid', borderwidth=1,
                     padx=5, pady=2).pack(side=tk.LEFT, padx=2)
        right_panel_row += 1

        list_frame = ttk.LabelFrame(right_panel, text="Processed Properties", padding="15")
        list_frame.grid(row=right_panel_row, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self.property_list_treeview = ttk.Treeview(list_frame, columns=("FileName", "ExtractionDate"), show="headings")
        self.property_list_treeview.heading("FileName", text="File Name")
        self.property_list_treeview.heading("ExtractionDate", text="Extracted On")
        self.property_list_treeview.column("FileName", stretch=tk.YES)
        self.property_list_treeview.column("ExtractionDate", width=150, stretch=tk.NO)
        self.property_list_treeview.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        tree_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.property_list_treeview.yview)
        self.property_list_treeview.configure(yscrollcommand=tree_scrollbar.set)
        tree_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        self.property_list_treeview.bind("<<TreeviewSelect>>", self.on_property_select)
        right_panel_row += 1

        preview_frame = ttk.LabelFrame(right_panel, text="PDF Content Preview", padding="15")
        preview_frame.grid(row=right_panel_row, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 0))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        right_panel.rowconfigure(right_panel_row, weight=1)

        self.content_text = scrolledtext.ScrolledText(preview_frame, height=10, width=70, wrap=tk.WORD,
                                                      font=('Courier New', 9),
                                                      background=C21_WHITE,
                                                      foreground=C21_BLACK,
                                                      relief='solid', borderwidth=1)
        self.content_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        main_container.rowconfigure(1, weight=1)

    def _on_input_change(self, key):
        self.input_source_status[key] = 'manual'
        self._update_input_field_colors()
        self.calculate_projections()

    def _update_input_field_colors(self):
        """Applies colors to input fields based on their source status using named styles."""
        for key, entry_widget in self.entries.items():
            source = self.input_source_status.get(key, 'default')
            if source == 'default':
                entry_widget.config(style='Default.TEntry')
            elif source == 'manual':
                entry_widget.config(style='Manual.TEntry')
            elif source == 'extracted':
                entry_widget.config(style='Extracted.TEntry')

    def _get_gradient_color(self, value, min_val, mid_val, max_val, direction='positive'):
        num_colors = len(OUTPUT_GRADIENT_COLORS)

        clamped_value = max(min_val, min(max_val, value))

        if direction == 'positive':
            if (mid_val - min_val) == 0:
                normalized_value = 0.5
            elif clamped_value <= mid_val:
                normalized_value = (clamped_value - min_val) / (mid_val - min_val) / 2
            else:
                if (max_val - mid_val) == 0:
                    normalized_value = 0.5
                else:
                    normalized_value = 0.5 + (clamped_value - mid_val) / (max_val - mid_val) / 2
        elif direction == 'negative':
            if (mid_val - min_val) == 0:
                normalized_value = 0.5
            elif clamped_value <= mid_val:
                normalized_value = 0.5 + (mid_val - clamped_value) / (mid_val - min_val) / 2
            else:
                if (max_val - mid_val) == 0:
                    normalized_value = 0.5
                else:
                    normalized_value = (max_val - clamped_value) / (max_val - mid_val) / 2
        else:
            return C21_WHITE

        color_index = int(normalized_value * (num_colors - 1))
        color_index = max(0, min(num_colors - 1, color_index))

        return OUTPUT_GRADIENT_COLORS[color_index]

    def _update_output_field_colors(self):
        for key, label_widget in self.output_labels.items():
            value_str = self.calculated_outputs[key].get()

            if "N/A" in value_str:
                label_widget.config(background=C21_LIGHT_GRAY)
                continue

            try:
                clean_value = value_str.replace('$', '').replace('%', '').replace(',', '').strip()
                value = float(clean_value)

                range_info = OUTPUT_RANGES.get(key)
                if not range_info:
                    label_widget.config(background=C21_LIGHT_GRAY)
                    continue

                color = self._get_gradient_color(
                    value,
                    range_info['min'],
                    range_info['mid'],
                    range_info['max'],
                    range_info['direction']
                )
                label_widget.config(background=color)
            except ValueError:
                label_widget.config(background=C21_LIGHT_GRAY)
            except Exception as e:
                logger.error(f"Error coloring output field {key}: {e}")
                label_widget.config(background=C21_LIGHT_GRAY)

    def populate_file_list(self):
        for iid in self.property_list_treeview.get_children():
            self.property_list_treeview.delete(iid)

        properties = self.db_manager.get_all_properties_summary()
        for prop in properties:
            self.property_list_treeview.insert("", "end", iid=prop['id'],
                                               values=(prop['file_name'], prop['extraction_date']))

    def on_property_select(self, event):
        selected_items = self.property_list_treeview.selection()
        if not selected_items:
            self.clear_data()
            self.status_var.set("No property selected.")
            return

        selected_id = int(selected_items[0])
        self.current_property_id = selected_id

        details = self.db_manager.get_property_details(selected_id)
        if details:
            self.clear_input_fields()

            for key, value in details['extracted_data'].items():
                if key in self.entry_vars and value is not None:
                    self.entry_vars[key].set(value)
                    self.input_source_status[key] = 'extracted'
                else:
                    if key in self.entry_vars:
                        self.entry_vars[key].set(DEFAULT_VALUES.get(key, ''))
                        self.input_source_status[key] = 'default'

            self._update_input_field_colors()

            self.content_text.delete(1.0, tk.END)
            self.content_text.insert(1.0, details['raw_text_preview'])

            self.file_path_var.set(details['original_file_path'])

            self.status_var.set(f"Loaded property: {os.path.basename(details['original_file_path'])}")
            self.calculate_projections()
        else:
            messagebox.showerror("Error", "Could not load property details.")
            self.status_var.set("Error loading property.")
            self.clear_data()

    def clear_input_fields(self):
        for key, var in self.entry_vars.items():
            var.set("")
            self.input_source_status[key] = 'default'
        self._update_input_field_colors()

    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select MLS PDF File",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filename:
            self.file_path_var.set(filename)
            self.status_var.set(f"Selected: {os.path.basename(filename)}")
            self.current_property_id = None
            self.clear_input_fields()
            for label_widget in self.output_labels.values():
                label_widget.config(background=C21_LIGHT_GRAY)
            for var in self.calculated_outputs.values():
                var.set("N/A")

    def extract_data_threaded(self):
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

            text_content = self.pdf_processor.extract_text(file_path)

            preview_text = text_content[:2000] + "\n..." if len(text_content) > 2000 else text_content
            self.root.after(0, lambda: self.content_text.delete(1.0, tk.END))
            self.root.after(0, lambda: self.content_text.insert(1.0, preview_text))

            extracted_data = extract_data_with_patterns(text_content)

            self.root.after(0, self.load_defaults)
            self.root.after(0, lambda: self.update_fields(extracted_data))

            self.root.after(0, lambda: self.status_var.set("Data extraction completed. Calculating financials..."))
            self.root.after(0, self.calculate_projections)

            current_inputs = {key: var.get() for key, var in self.entry_vars.items()}
            current_outputs = {key: var.get() for key, var in self.calculated_outputs.items()}

            base_file_name = os.path.basename(file_path)

            if self.current_property_id:
                success = self.db_manager.update_property(
                    self.current_property_id,
                    base_file_name,
                    file_path,
                    preview_text,
                    current_inputs,
                    current_outputs
                )
                if not success:
                    messagebox.showwarning("Database Update",
                                           f"Failed to update property for {base_file_name}. It might have been deleted or an error occurred.")
            else:
                new_id = self.db_manager.insert_property(
                    base_file_name,
                    file_path,
                    preview_text,
                    current_inputs,
                    current_outputs
                )
                if new_id:
                    self.current_property_id = new_id
                else:
                    messagebox.showwarning("Database Insert",
                                           f"Property '{base_file_name}' already exists or could not be inserted.")

            self.root.after(0, self.populate_file_list)
            logger.info(f"Successfully extracted data from {file_path}")

        except Exception as e:
            error_msg = f"Failed to extract data: {str(e)}"
            logger.error(error_msg)
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            self.root.after(0, lambda: self.status_var.set("Extraction failed"))
        finally:
            self.root.after(0, lambda: self.progress.stop())

    def validate_data(self):
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
        for field_label, field_key in GUI_FIELD_ORDER:
            if field_key in self.entry_vars:
                current_value = self.entry_vars[field_key].get()
                default_value = DEFAULT_VALUES.get(field_key, '')
                if not current_value or current_value == "N/A":
                    self.entry_vars[field_key].set(default_value)
                    self.input_source_status[field_key] = 'default'
        self._update_input_field_colors()
        self.status_var.set("Default values loaded. Calculating financials...")
        self.calculate_projections()

    def update_fields(self, extracted_data):
        for field, value in extracted_data.items():
            if field in self.entry_vars and value is not None:
                self.entry_vars[field].set(value)
                self.input_source_status[field] = 'extracted'
        self._update_input_field_colors()

    def calculate_projections(self):
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
                self.root.after(0, self._update_output_field_colors)
                return
            self.calculated_outputs['gpi'].set(f"${gpi:,.2f}")

            vacancy_rate = inputs.get('vacancy_rate')
            if vacancy_rate is None:
                try:
                    vacancy_rate = float(DEFAULT_VALUES.get('vacancy_rate', '0'))
                except ValueError:
                    vacancy_rate = 0.0

            vc = gpi * (vacancy_rate / 100)
            self.calculated_outputs['vc'].set(f"${vc:,.2f}")

            egi = gpi - vc
            self.calculated_outputs['egi'].set(f"${egi:,.2f}")

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

            if purchase_price is None:
                purchase_price = float(DEFAULT_VALUES.get('purchase_price', '0') or '0')

            if purchase_price > 0:
                cap_rate = (noi / purchase_price) * 100
                self.calculated_outputs['cap_rate'].set(f"{cap_rate:.2f}%")
            else:
                self.calculated_outputs['cap_rate'].set("N/A (Purchase Price Missing/Zero)")

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

            grm = None
            if purchase_price is not None and purchase_price > 0 and gpi is not None and gpi > 0:
                grm = purchase_price / gpi
                self.calculated_outputs['grm'].set(f"{grm:.2f}")
            else:
                self.calculated_outputs['grm'].set("N/A (Purchase Price or GPI Missing/Zero)")

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
        finally:
            self.root.after(0, self._update_output_field_colors)

    def save_current_property(self):
        current_inputs = {}
        for key, var in self.entry_vars.items():
            current_inputs[key] = var.get()

        current_outputs = {key: var.get() for key, var in self.calculated_outputs.items()}
        file_path = self.file_path_var.get()
        base_file_name = os.path.basename(file_path) if file_path else "New Property"

        if not file_path and not current_inputs.get('purchase_price') and not current_inputs.get('number_of_units'):
            messagebox.showwarning("Cannot Save",
                                   "Please extract data from a PDF or enter at least a Purchase Price or Number of Units before saving.")
            return

        raw_text_preview = self.content_text.get(1.0, tk.END).strip()

        if self.current_property_id:
            success = self.db_manager.update_property(
                self.current_property_id,
                base_file_name,
                file_path,
                raw_text_preview,
                current_inputs,
                current_outputs
            )
            if success:
                messagebox.showinfo("Save Successful", f"Property '{base_file_name}' updated in database.")
                self.populate_file_list()
            else:
                messagebox.showerror("Save Error", f"Failed to update property '{base_file_name}'.")
        else:
            new_id = self.db_manager.insert_property(
                base_file_name,
                file_path,
                raw_text_preview,
                current_inputs,
                current_outputs
            )
            if new_id:
                self.current_property_id = new_id
                messagebox.showinfo("Save Successful",
                                    f"Property '{base_file_name}' saved as new record (ID: {new_id}).")
                self.populate_file_list()
            else:
                messagebox.showwarning("Save Warning",
                                       f"Property '{base_file_name}' already exists or could not be inserted.")

    def clear_data(self):
        self.current_property_id = None
        self.clear_input_fields()
        self.file_path_var.set("")
        for var in self.calculated_outputs.values():
            var.set("N/A")
        for label_widget in self.output_labels.values():
            label_widget.config(background=C21_LIGHT_GRAY)
        self.content_text.delete(1.0, tk.END)
        self.status_var.set("Ready")
        self.property_list_treeview.selection_remove(self.property_list_treeview.selection())

    def run(self):
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
