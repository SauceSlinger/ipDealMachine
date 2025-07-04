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
from utils.data_validator import DataValidator # Note: This is your general validator, not the specific comparison logic
from utils.database import DatabaseManager

# Setup logging - Ensure this is DEBUG for full visibility
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class MLSDataExtractor:
    def __init__(self):
        # Initialize processors FIRST to ensure they exist
        self.pdf_processor = PDFProcessor()
        self.validator = DataValidator() # This isn't directly used in main for field validation, but good to keep if needed elsewhere

        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry(WINDOW_SIZE)

        # Initialize Database Manager - pass the full path to the DB file
        db_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', DATABASE_NAME)

        self.db_manager = DatabaseManager(db_file_path)

        # New: Store the original extracted data for comparison
        self.original_extracted_data = {}

        # Apply a theme for a modern look
        self.style = ttk.Style()
        # self.style.theme_use('clam')

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

        self.style.configure('C21.TButton',
                             font=('Arial', 10, 'bold'), # Inherit or redefine font
                             padding=8, # Inherit or redefine padding
                             relief='flat', # Inherit or redefine relief
                             background=C21_GOLD, # Make C21_GOLD the default for C21.TButton
                             foreground=C21_BLACK,
                             borderwidth=1,
                             focusthickness=0)
        self.style.map('C21.TButton',
                       background=[('active', '#B8860B'), ('pressed', '#A07000')], # Darker gold on hover/pressed
                       foreground=[('active', C21_BLACK)])

        # Define the Danger style for the delete button with a simpler name
        self.style.configure('Red.TButton', background='#FF4500', foreground='white') # Simpler name
        self.style.map('Red.TButton',
                       background=[('active', '#CC3700')],
                       foreground=[('active', 'white')])

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

        # Entry Fields - Base style.
        self.style.configure('TEntry',
                             foreground=C21_BLACK,
                             relief='solid',
                             borderwidth=1,
                             padding=3)

        # Define specific styles for input field colors using map for fieldbackground
        self.style.map('Default.TEntry', fieldbackground=[('!disabled', INPUT_COLOR_DEFAULT)])
        self.style.map('Manual.TEntry', fieldbackground=[('!disabled', INPUT_COLOR_MANUAL)])
        self.style.map('Extracted.TEntry', fieldbackground=[('!disabled', INPUT_COLOR_EXTRACTED)])

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

        # --- REPLACE YOUR PREVIOUS DIAGNOSTIC LINES WITH THESE ---
        print("\n--- DEBUG: Checking for Red.TButton style ---") # Update this line
        try:
            self.style.lookup('Red.TButton', 'background') # Update this line
            print("RESULT: Red.TButton style IS present and discoverable.") # Update this line
        except tk.TclError as e:
            print(f"RESULT: Red.TButton style IS NOT present. Error: {e}") # Update this line
            print("This confirms the style is not registered. Double-check its definition and placement.")
        print("--------------------------------------------------")
        # --- END CORRECTED DIAGNOSTIC LINES ---

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
        # Store original configured defaults (from config.py) for the "Reset to Original" button
        self.original_config_defaults = DEFAULT_VALUES.copy()
        self.defaults_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'user_defaults.json')
        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.current_property_id = None
        # --- THIS LINE MUST BE AFTER defaults_file_path IS DEFINED ---
        self.root.after(100, self._load_persistent_defaults)

    def _on_closing(self):
        """Called when the window is closed. Database connections are now managed per-operation,
        so no global close is strictly necessary here, but keeping for consistency."""
        if self.db_manager:
            self.db_manager.close()
        self.root.destroy()

        # ... (inside MLSDataExtractor class, after __init__ or other methods) ...

    def _load_persistent_defaults(self):
        """Loads default values from a user_defaults.json file, or falls back to config.py defaults."""
        if os.path.exists(self.defaults_file_path):
            try:
                with open(self.defaults_file_path, 'r', encoding='utf-8') as f:
                    loaded_defaults = json.load(f)
                self.current_default_values = loaded_defaults
                logger.info("Loaded persistent defaults from user_defaults.json")
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding user_defaults.json: {e}. Falling back to config defaults.")
                self.current_default_values = self.original_config_defaults.copy()
                self._save_persistent_defaults()  # Save initial config defaults to file if corrupted
            except Exception as e:
                logger.error(f"Error loading persistent defaults: {e}. Falling back to config defaults.")
                self.current_default_values = self.original_config_defaults.copy()
                self._save_persistent_defaults()  # Save initial config defaults to file if error
        else:
            logger.info("user_defaults.json not found. Using config defaults and saving them.")
            self.current_default_values = self.original_config_defaults.copy()
            self._save_persistent_defaults()  # Create the file with initial config defaults

        # After loading, ensure all GUI fields are updated and calculations run
        self.load_defaults_and_calculate()  # This method will now be called after defaults are correctly set

    def _save_persistent_defaults(self):
        """Saves the current_default_values to the user_defaults.json file."""
        try:
            # Ensure the 'data' directory exists
            os.makedirs(os.path.dirname(self.defaults_file_path), exist_ok=True)
            with open(self.defaults_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.current_default_values, f, indent=4)
            logger.info(f"Saved current defaults to {self.defaults_file_path}")
        except Exception as e:
            logger.error(f"Failed to save persistent defaults to {self.defaults_file_path}: {e}")
            messagebox.showerror("Save Error", f"Could not save default settings: {e}")

    # ... (rest of your existing class methods) ...

    def load_defaults_and_calculate(self):
        """Loads defaults and then triggers a calculation. Used on app start."""
        self.load_defaults()
        self.calculate_projections()
        self.populate_file_list()

    def setup_ui(self):
        # Toolbar Frame - Remains at the top, packed directly into root
        toolbar_frame = ttk.Frame(self.root, relief='raised', borderwidth=1, style='TFrame')
        toolbar_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))

        settings_btn = ttk.Button(toolbar_frame, text="Settings (Defaults)", command=self._open_default_settings_window)
        settings_btn.pack(side=tk.LEFT, padx=5, pady=5)

        export_btn = ttk.Button(toolbar_frame, text="Export Current", command=self._export_current_data)
        export_btn.pack(side=tk.LEFT, padx=5, pady=5)

        about_btn = ttk.Button(toolbar_frame, text="About", command=self._show_about_dialog)
        about_btn.pack(side=tk.RIGHT, padx=5, pady=5)

        # Main container for the title and the three-column content
        main_container = ttk.Frame(self.root, padding="10", style='TFrame')  # Adjusted padding slightly
        main_container.pack(expand=True, fill=tk.BOTH)  # main_container fills the remaining space

        # Configure main_container's grid for the title row (row 0) and the columns row (row 1)
        main_container.grid_rowconfigure(0, weight=0)  # Title row, fixed height
        main_container.grid_rowconfigure(1, weight=1)  # Columns row, expands vertically
        main_container.grid_columnconfigure(0, weight=1)  # Left column
        main_container.grid_columnconfigure(1, weight=1)  # Middle column
        main_container.grid_columnconfigure(2, weight=1)  # Right column

        # Title Label - now spans all three columns at the top of main_container
        title_label = ttk.Label(main_container, text=f"{APP_NAME} v{APP_VERSION}",
                                font=('Arial', 20, 'bold'), anchor='center',
                                background=C21_GOLD, foreground=C21_BLACK,
                                relief='flat', padding=15)
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 15), sticky=tk.E + tk.W)

        # --- Create the three main column frames ---
        # These will replace your original left_panel and right_panel
        left_column_frame = ttk.Frame(main_container, padding="15", style='TFrame')
        middle_column_frame = ttk.Frame(main_container, padding="15", style='TFrame')
        right_column_frame = ttk.Frame(main_container, padding="15", style='TFrame')

        # Place the column frames in the main_container grid (in row 1)
        left_column_frame.grid(row=1, column=0, sticky=tk.NSEW, padx=(0, 5))  # Leftmost column
        middle_column_frame.grid(row=1, column=1, sticky=tk.NSEW, padx=5)  # Middle column
        right_column_frame.grid(row=1, column=2, sticky=tk.NSEW, padx=(5, 0))  # Rightmost column

        # --- LEFT COLUMN CONTENT (PDF Extraction & Input Data) ---
        # All widgets previously parented to 'left_panel' are now parented to 'left_column_frame'
        # Their internal grid layout logic is retained within this new parent.
        left_column_frame.columnconfigure(1, weight=1)  # Ensures input fields expand
        left_column_frame.grid_rowconfigure(5, weight=1)  # This row contains fields_frame, allow it to expand

        current_row = 0  # Renamed for clarity within this column context

        # PDF File and Controls
        ttk.Label(left_column_frame, text="PDF File:", font=('Arial', 10, 'bold'), foreground=C21_DARK_GRAY).grid(
            row=current_row, column=0, sticky=tk.W, pady=5)
        self.file_path_var = tk.StringVar()
        self.file_entry = ttk.Entry(left_column_frame, textvariable=self.file_path_var,
                                    width=50)  # width is a suggestion, grid will control
        self.file_entry.grid(row=current_row, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 5))

        browse_btn = ttk.Button(left_column_frame, text="Browse", command=self.browse_file)
        browse_btn.grid(row=current_row, column=2, pady=5)
        current_row += 1

        extract_btn = ttk.Button(left_column_frame, text="Extract Data",
                                 command=self.extract_data_threaded, style='Accent.TButton')
        extract_btn.grid(row=current_row, column=0, columnspan=3, pady=15, sticky=tk.E + tk.W)
        current_row += 1

        self.progress = ttk.Progressbar(left_column_frame, mode='indeterminate')
        self.progress.grid(row=current_row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        current_row += 1

        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(left_column_frame, textvariable=self.status_var, font=('Arial', 9, 'italic'),
                                 foreground=C21_DARK_GRAY)
        status_label.grid(row=current_row, column=0, columnspan=3, pady=5)
        current_row += 1

        # Input Data Fields
        fields_frame = ttk.LabelFrame(left_column_frame, text="Input Data", padding="15")
        fields_frame.grid(row=current_row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 5))
        fields_frame.columnconfigure(1, weight=1)  # Allows entry fields to expand within fields_frame

        self.entry_vars = {}
        self.entries = {}
        self.trace_ids = {}

        for i, (label, key) in enumerate(GUI_FIELD_ORDER):
            ttk.Label(fields_frame, text=label + ":", foreground=C21_DARK_GRAY).grid(row=i, column=0, sticky=tk.W,
                                                                                     pady=3)
            var = tk.StringVar()
            entry = ttk.Entry(fields_frame, textvariable=var, width=40)
            entry.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=3, padx=(10, 0))

            self.entry_vars[key] = var
            self.entries[key] = entry

            trace_id = var.trace_add("write", lambda name, index, mode, k=key: self._on_input_change(k))
            self.trace_ids[key] = trace_id

        # Note: current_row is not incremented directly after this loop to allow other widgets to stack below fields_frame
        # It's incremented to point to the row *after* fields_frame for subsequent widgets in this column.
        current_row += 1

        # Input Data Key
        input_key_frame = ttk.Frame(left_column_frame, style='TFrame')
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

        # Action Buttons for Input Data
        buttons_frame = ttk.Frame(left_column_frame, style='TFrame')
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

        # --- MIDDLE COLUMN CONTENT (Financial Projections & Output Value Key) ---
        # These were previously in 'right_panel', now reparented to 'middle_column_frame'
        # Using pack for simple vertical stacking within this column.

        # Financial Projections
        output_frame = ttk.LabelFrame(middle_column_frame, text="Financial Projections", padding="15")
        output_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))  # Use pack to fill column space
        output_frame.columnconfigure(1, weight=1)  # Make value labels expand within output_frame

        output_fields = [
            ("Gross Potential Income (GPI)", "gpi"), ("Vacancy and Credit Loss (V&C)", "vc"),
            ("Effective Gross Income (EGI)", "egi"), ("Net Operating Income (NOI)", "noi"),
            ("Capitalization Rate (Cap Rate)", "cap_rate"), ("Debt Service (Mortgage Payment)", "debt_service"),
            ("Cash Flow Before Taxes (CFBT)", "cfbt"), ("Cash-on-Cash Return (CoC)", "coc_return"),
            ("Gross Rent Multiplier (GRM)", "grm"), ("Debt Service Coverage Ratio (DSCR)", "dscr")
        ]

        # Ensure self.calculated_outputs and self.output_labels are initialized (e.g., in __init__)
        # If not, you might need to add:
        # self.calculated_outputs = {key: tk.StringVar(value="N/A") for _, key in output_fields}
        # self.output_labels = {}

        for i, (label, key) in enumerate(output_fields):
            ttk.Label(output_frame, text=label + ":", font=('Arial', 10, 'bold'), foreground=C21_DARK_GRAY).grid(row=i,
                                                                                                                 column=0,
                                                                                                                 sticky=tk.W,
                                                                                                                 pady=3)
            # Ensure the StringVar exists before trying to use it
            if key not in self.calculated_outputs:
                self.calculated_outputs[key] = tk.StringVar(value="N/A")

            output_label = tk.Label(output_frame, textvariable=self.calculated_outputs[key],
                                    font=('Arial', 10, 'bold'), foreground=C21_BLACK,
                                    background=C21_WHITE,
                                    relief='solid', borderwidth=1, padx=5, pady=2)
            output_label.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=3, padx=(10, 0))
            self.output_labels[key] = output_label

        # Output Value Key
        output_key_frame = ttk.Frame(middle_column_frame, style='TFrame')
        output_key_frame.pack(fill=tk.X, pady=(5, 15))  # Packs below output_frame
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

        # --- RIGHT COLUMN CONTENT (Processed Properties & PDF Content Preview) ---
        # These were previously in 'right_panel', now reparented to 'right_column_frame'
        # This column uses grid to split vertically between the two sections.
        right_column_frame.grid_rowconfigure(0, weight=1)  # Processed Properties section expands
        right_column_frame.grid_rowconfigure(1, weight=1)  # PDF Preview section expands
        right_column_frame.grid_columnconfigure(0, weight=1)  # Ensures content fills horizontally

        # Processed Properties List
        list_frame = ttk.LabelFrame(right_column_frame, text="Processed Properties", padding="15")
        list_frame.grid(row=0, column=0, sticky=tk.NSEW, pady=(0, 10))  # Top half of right column
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(1, weight=1)  # Treeview itself will expand within list_frame

        # Toolbar Frame for the "Processed Properties" pane
        self.property_list_toolbar_frame = ttk.Frame(list_frame, style='C21.TFrame')
        self.property_list_toolbar_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))

        self.delete_button = ttk.Button(
            self.property_list_toolbar_frame,
            text="Delete Selected Property",
            command=self.delete_selected_property,
            style='Red.TButton'
        )
        self.delete_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Treeview for property list
        self.property_list_treeview = ttk.Treeview(list_frame,
                                                   columns=("ID", "Address", "City", "State", "Zip", "Price",
                                                            "FileName", "ExtractionDate"),
                                                   show="headings")

        self.property_list_treeview.heading("ID", text="ID")
        self.property_list_treeview.heading("Address", text="Address")
        self.property_list_treeview.heading("City", text="City")
        self.property_list_treeview.heading("State", text="State")
        self.property_list_treeview.heading("Zip", text="Zip")
        self.property_list_treeview.heading("Price", text="Price")
        self.property_list_treeview.heading("FileName", text="File Name")
        self.property_list_treeview.heading("ExtractionDate", text="Extracted On")

        self.property_list_treeview.column("ID", width=40, stretch=tk.NO)
        self.property_list_treeview.column("Address", stretch=tk.YES)
        self.property_list_treeview.column("City", width=100, stretch=tk.NO)
        self.property_list_treeview.column("State", width=50, stretch=tk.NO)
        self.property_list_treeview.column("Zip", width=70, stretch=tk.NO)
        self.property_list_treeview.column("Price", width=100, stretch=tk.NO, anchor='e')
        self.property_list_treeview.column("FileName", width=0, stretch=tk.NO)
        self.property_list_treeview.column("ExtractionDate", width=0, stretch=tk.NO)

        self.property_list_treeview.grid(row=1, column=0, sticky=tk.NSEW)  # Treeview in row 1 of list_frame

        tree_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.property_list_treeview.yview)
        self.property_list_treeview.configure(yscrollcommand=tree_scrollbar.set)
        tree_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))

        self.property_list_treeview.bind("<<TreeviewSelect>>", self.on_property_select)
        self.property_list_treeview.bind("<Delete>", lambda event: self.delete_selected_property())

        # PDF Content Preview
        preview_frame = ttk.LabelFrame(right_column_frame, text="PDF Content Preview", padding="15")
        preview_frame.grid(row=1, column=0, sticky=tk.NSEW, pady=(10, 0))  # Bottom half of right column
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)

        self.content_text = scrolledtext.ScrolledText(preview_frame, height=10, width=70, wrap=tk.WORD,
                                                      font=('Courier New', 9),
                                                      background=C21_WHITE,
                                                      foreground=C21_BLACK,
                                                      relief='solid', borderwidth=1)
        self.content_text.grid(row=0, column=0, sticky=tk.NSEW)

        # Main container's row 1 is already configured to expand, handling all columns
        # main_container.rowconfigure(1, weight=1) # This line is redundant given grid_rowconfigure(1, weight=1) above

        # Final setup calls that might be in your original setup_ui and should remain:
        # self._update_output_field_colors() # Needs to be called after output_labels are created
        # self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        # self.current_property_id = None # Should be initialized in __init__
        # self.root.after(100, self._load_persistent_defaults) # If this method exists
        # self.refresh_property_list() # If this exists and is needed at startup
    def _set_input_field_value(self, key, value, source_type):
        """
        Sets the value of an input field and its source type,
        temporarily disabling the trace to prevent _on_input_change from firing.
        """
        var = self.entry_vars.get(key)
        if var:
            trace_id = self.trace_ids.get(key)
            if trace_id:
                var.trace_remove("write", trace_id)  # Temporarily remove trace

            var.set(value if value is not None else "")  # Ensure it's a string
            self.input_source_status[key] = source_type

            if trace_id:
                # Re-add the trace and store the new ID (trace_add returns a new ID)
                new_trace_id = var.trace_add("write", lambda name, index, mode, k=key: self._on_input_change(k))
                self.trace_ids[key] = new_trace_id
        self._update_input_field_colors()  # Update colors after setting value

    def _on_input_change(self, key):
        """
        This method is ONLY triggered by actual user input (typing).
        Programmatic updates are handled by _set_input_field_value.
        """
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

        if (max_val - min_val) == 0:  # Avoid division by zero if range is zero
            return OUTPUT_GRADIENT_COLORS[num_colors // 2] # Return middle color

        if direction == 'positive':
            # Normalize value to a 0-1 range based on the given min/max
            normalized_value = (clamped_value - min_val) / (max_val - min_val)
        elif direction == 'negative':
            # Reverse normalization for negative direction (e.g., lower is better)
            normalized_value = 1 - (clamped_value - min_val) / (max_val - min_val)
        else:
            return C21_WHITE  # Default color if direction is unknown

        color_index = int(normalized_value * (num_colors - 1))
        color_index = max(0, min(num_colors - 1, color_index))

        return OUTPUT_GRADIENT_COLORS[color_index]

    def _update_output_field_colors(self):
        # --- ADD THIS LINE FOR DEBUGGING ---
        print("--- DEBUG: _update_output_field_colors called ---")
        # --- END ADDITION ---

        for key, label_widget in self.output_labels.items():
            value_str = self.calculated_outputs[key].get()
            # --- ADD THIS LINE FOR DEBUGGING ---
            print(f"--- DEBUG: Coloring {key}. Raw value string: '{value_str}'")
            # --- END ADDITION ---

            if "N/A" in value_str:
                label_widget.config(background=C21_LIGHT_GRAY)
                # --- ADD THIS LINE FOR DEBUGGING ---
                print(f"--- DEBUG: {key} is N/A. Set to C21_LIGHT_GRAY. Continuing.")
                # --- END ADDITION ---
                continue

            try:
                clean_value = value_str.replace('$', '').replace('%', '').replace(',', '').strip()
                # --- ADD THIS LINE FOR DEBUGGING ---
                print(f"--- DEBUG: {key}. Cleaned value for float conversion: '{clean_value}'")
                # --- END ADDITION ---
                value = float(clean_value)
                # --- ADD THIS LINE FOR DEBUGGING ---
                print(f"--- DEBUG: {key}. Converted float value: {value}")
                # --- END ADDITION ---

                range_info = OUTPUT_RANGES.get(key)
                if not range_info:
                    label_widget.config(background=C21_LIGHT_GRAY)
                    # --- ADD THIS LINE FOR DEBUGGING ---
                    print(f"--- DEBUG: No range_info found for {key}. Set to C21_LIGHT_GRAY. Continuing.")
                    # --- END ADDITION ---
                    continue

                color = self._get_gradient_color(
                    value,
                    range_info['min'],
                    range_info['mid'],
                    range_info['max'],
                    range_info['direction']
                )
                # --- ADD THIS LINE FOR DEBUGGING ---
                print(f"--- DEBUG: {key}. Color calculated by _get_gradient_color: {color}")
                # --- END ADDITION ---
                label_widget.config(background=color)
            except ValueError as ve:
                # --- MODIFY THIS LINE FOR DEBUGGING ---
                print(f"--- ERROR: ValueError for {key} ('{value_str}'). Details: {ve}. Set to C21_LIGHT_GRAY.")
                # --- END MODIFICATION ---
                label_widget.config(background=C21_LIGHT_GRAY)
            except Exception as e:
                # --- MODIFY THIS LINE FOR DEBUGGING ---
                print(f"--- ERROR: General Exception for {key}. Details: {e}. Set to C21_LIGHT_GRAY.")
                # --- END MODIFICATION ---
                label_widget.config(background=C21_LIGHT_GRAY)

    def populate_file_list(self):
        for iid in self.property_list_treeview.get_children():
            self.property_list_treeview.delete(iid)

        properties = self.db_manager.get_all_properties_summary()
        for prop in properties:
            self.property_list_treeview.insert("", "end", iid=prop['id'],
                                               values=(prop['file_name'], prop['extraction_date']))

    def delete_selected_property(self):
        """Deletes the currently selected property from the database and Treeview."""
        selected_item_id = self.property_list_treeview.selection()

        if not selected_item_id:
            messagebox.showwarning("No Selection", "Please select a property to delete.")
            return

        # Treeview selection returns a tuple of item IDs, we only expect one for single selection
        item_id = selected_item_id[0]
        values = self.property_list_treeview.item(item_id, 'values')

        # Ensure values are not empty and ID is present (ID is now at index 0)
        if not values or len(values) < 1:
            messagebox.showerror("Error", "Could not retrieve property ID for deletion.")
            return

        property_db_id = values[0]  # The first column is now the database ID

        # Get display info for confirmation message using the new column indices
        display_address = values[1] if len(values) > 1 else "Unknown Address"  # Address is at index 1
        display_city = values[2] if len(values) > 2 else "Unknown City"  # City is at index 2

        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete the property:\n{display_address}, {display_city} (ID: {property_db_id})?\n\n"
            "This action cannot be undone."
        )

        if confirm:
            try:
                # Delete from database
                db = DatabaseManager(DATABASE_NAME)
                db.delete_property(property_db_id)
                db.close()  # Ensure the database connection is closed

                # Remove from Treeview
                self.property_list_treeview.delete(item_id)
                self.status_var.set(f"Property ID {property_db_id} deleted.")
                logger.info(f"Property ID {property_db_id} deleted successfully.")

                # Clear input/output fields if the deleted property was the one currently loaded
                if self.current_property_id == property_db_id:
                    self.clear_data()  # This method already clears input/output and resets current_property_id
                    self.status_var.set(f"Property ID {property_db_id} deleted and fields cleared.")

            except Exception as e:
                messagebox.showerror("Deletion Error", f"Failed to delete property: {e}")
                logger.error(f"Error deleting property ID {property_db_id}: {e}", exc_info=True)

    def load_properties_to_treeview(self):
        """Loads all properties from the database into the Treeview."""
        # Clear existing items in the treeview
        for item in self.property_list_treeview.get_children():
            self.property_list_treeview.delete(item)

        db = DatabaseManager(DATABASE_NAME)
        properties = db.get_all_properties()
        db.close()

        for prop in properties:
            # Ensure the order of values inserted matches the treeview columns defined in setup_ui
            # ("ID", "Address", "City", "State", "Zip", "Price", "FileName", "ExtractionDate")
            self.property_list_treeview.insert(
                "", tk.END,
                values=(
                    prop.get('id'),  # The database ID
                    prop.get('property_address', 'N/A'),
                    prop.get('city', 'N/A'),
                    prop.get('state', 'N/A'),
                    prop.get('zip_code', 'N/A'),
                    f"${prop.get('listing_price', 0):,.2f}" if prop.get('listing_price') is not None else "N/A",
                    prop.get('file_name', 'N/A'),  # Hidden column
                    prop.get('extracted_at', 'N/A')  # Hidden column
                )
            )

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
            # Clear input fields first, which also resets their status to 'default'
            self.clear_input_fields()

            # Populate original_extracted_data for validation reference
            # This 'original_extracted_data' here refers to the state saved in the DB
            # which *should* be the snapshot of the GUI after initial extraction/user save.
            self.original_extracted_data = details['original_extracted_data']
            logger.debug(f"DEBUG: self.original_extracted_data loaded from DB: {self.original_extracted_data}")
            print(
                f"--- DEBUG PRINT: self.original_extracted_data loaded from DB: {self.original_extracted_data}")  # Added print

            # Populate GUI fields with user_input_data using the new helper
            for label, key in GUI_FIELD_ORDER:  # Iterate through GUI_FIELD_ORDER to ensure all fields are handled
                user_value = details['user_input_data'].get(key)
                original_value = self.original_extracted_data.get(key)

                # Determine initial source type based on comparison
                if user_value is not None and user_value != "":
                    # Clean values for comparison before deciding source type
                    def clean_val_for_comparison(val):
                        if val is None: return ""
                        if isinstance(val, (int, float)): return str(val)
                        val = str(val).replace('$', '').replace('%', '').replace(',', '').strip()
                        val = re.sub(r'\s+', ' ', val)
                        return val.lower()

                    cleaned_user = clean_val_for_comparison(user_value)
                    cleaned_original = clean_val_for_comparison(original_value)

                    if cleaned_user == cleaned_original:
                        self._set_input_field_value(key, user_value, 'extracted')
                    else:
                        self._set_input_field_value(key, user_value, 'manual')
                else:
                    # If user_value is empty/None, set to default
                    self._set_input_field_value(key, self.current_default_values.get(key, ''), 'default')

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
        """Clears all input fields and resets their source status to 'default'."""
        for label, key in GUI_FIELD_ORDER:
            self._set_input_field_value(key, self.current_default_values.get(key, ''), 'default')

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
            # Clear original_extracted_data when a new file is browsed
            self.original_extracted_data = {}
            logger.debug("DEBUG: self.original_extracted_data cleared in browse_file.")
            print("--- DEBUG PRINT: self.original_extracted_data cleared in browse_file.")  # Added print
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

            raw_text_preview = text_content[:2000] + "\n..." if len(text_content) > 2000 else text_content
            self.root.after(0, lambda: self.content_text.delete(1.0, tk.END))
            self.root.after(0, lambda: self.content_text.insert(1.0, raw_text_preview))

            extracted_data = extract_data_with_patterns(text_content)
            logger.debug(f"DEBUG: Extracted data from patterns: {extracted_data}")
            print(f"--- DEBUG PRINT: Extracted data from patterns: {extracted_data}")  # Added print

            # Update GUI fields with extracted data using the new helper
            for label, key in GUI_FIELD_ORDER:
                self._set_input_field_value(key, extracted_data.get(key, self.current_default_values.get(key, '')), 'extracted')

            # --- CRITICAL CHANGE HERE ---
            # After populating GUI with extracted data AND defaults, capture the FULL current state
            # This ensures 'original_extracted_data' matches what's displayed in the GUI after extraction
            self.original_extracted_data = {key: var.get() for key, var in self.entry_vars.items()}
            logger.debug(f"DEBUG: self.original_extracted_data SET TO CURRENT GUI STATE after extraction: {self.original_extracted_data}")
            print(f"--- DEBUG PRINT: self.original_extracted_data SET TO CURRENT GUI STATE after extraction: {self.original_extracted_data}") # Added print
            # --- END CRITICAL CHANGE ---

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
                    raw_text_preview,
                    user_input_data=current_inputs,
                    calculated_financials=current_outputs
                )
                if not success:
                    messagebox.showwarning("Database Update",
                                           f"Failed to update property for {base_file_name}. It might have been deleted or an error occurred.")
            else:
                new_id = self.db_manager.insert_property(
                    file_name=base_file_name,
                    original_file_path=file_path,
                    raw_text_preview=raw_text_preview,
                    original_extracted_data=self.original_extracted_data, # This will now store the full GUI snapshot
                    user_input_data=current_inputs,
                    calculated_financials=current_outputs
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

    def _show_validation_differences_popup(self, differences):
        """Displays validation differences in a custom, formatted Toplevel window."""
        popup = tk.Toplevel(self.root)
        popup.title("Validation Differences Found")
        popup.transient(self.root)  # Make it appear on top of the main window
        popup.grab_set()  # Make it modal
        popup.geometry("600x400")
        popup.resizable(False, False)
        popup.config(bg=C21_LIGHT_GRAY)

        # Center the popup window
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (popup.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (popup.winfo_height() // 2)
        popup.geometry(f"+{x}+{y}")


        header_label = ttk.Label(popup, text="Differences Between Current Input and Original Extracted Data:",
                                 font=('Arial', 12, 'bold'), foreground=C21_GOLD, background=C21_LIGHT_GRAY, padding=10)
        header_label.pack(pady=(10, 5))

        text_area = scrolledtext.ScrolledText(popup, wrap=tk.WORD, font=('Courier New', 10),
                                              bg=C21_WHITE, fg=C21_BLACK,
                                              relief='flat', borderwidth=1, padx=10, pady=10)
        text_area.pack(expand=True, fill='both', padx=15, pady=10)

        # Configure tags for formatting
        text_area.tag_config('field_label', font=('Courier New', 10, 'bold'), foreground=C21_DARK_GRAY)
        text_area.tag_config('current_val', foreground='blue')
        text_area.tag_config('original_val', foreground='red')
        text_area.tag_config('info', foreground=C21_BLACK)
        text_area.tag_config('separator', foreground=C21_LIGHT_GRAY)


        for diff_info in differences:
            # Example diff_info format:
            # {'label': 'Property Taxes ($)', 'key': 'property_taxes',
            #  'current_raw': '5,339.00', 'original_raw': '5,300.00',
            #  'type': 'Numerical difference'}

            field_label = diff_info.get('label', 'Unknown Field')
            current_raw = diff_info.get('current_raw', 'N/A')
            original_raw = diff_info.get('original_raw', 'N/A')
            diff_type = diff_info.get('type', 'General difference')


            text_area.insert(tk.END, f"Field: ", 'info')
            text_area.insert(tk.END, f"{field_label}\n", 'field_label')

            text_area.insert(tk.END, f"  Current GUI Value: ", 'info')
            text_area.insert(tk.END, f"'{current_raw}'\n", 'current_val')

            text_area.insert(tk.END, f"  Original Extracted Value: ", 'info')
            text_area.insert(tk.END, f"'{original_raw}'\n", 'original_val')

            text_area.insert(tk.END, f"  Type of Difference: {diff_type}\n\n", 'info')
            text_area.insert(tk.END, "-" * 60 + "\n\n", 'separator')


        text_area.config(state=tk.DISABLED) # Make text read-only

        ok_button = ttk.Button(popup, text="OK", command=popup.destroy, style='Accent.TButton')
        ok_button.pack(pady=10)

        # Focus the popup and wait until it's closed
        popup.wait_window()


    def validate_data(self):
        """
        Validates current GUI input data against the originally extracted data.
        """
        logger.debug(
            f"DEBUG: self.original_extracted_data at start of validate_data (via logger): {self.original_extracted_data}")
        print(
            f"--- DEBUG PRINT: self.original_extracted_data at start of validate_data: {self.original_extracted_data}")  # Added print

        # Check if original_extracted_data is empty or contains only empty values
        if not self.original_extracted_data or all(
                value == '' or value is None for value in self.original_extracted_data.values()):
            messagebox.showinfo("Validation",
                                "No original extracted data available for comparison. Please extract data from a PDF first or load a saved property.")
            return

        current_inputs = {key: var.get() for key, var in self.entry_vars.items()}
        logger.debug(f"DEBUG: Current inputs from GUI: {current_inputs}")
        print(f"--- DEBUG PRINT: Current inputs from GUI: {current_inputs}")  # Added print
        differences = []

        # Enhanced clean_value function for robust comparison
        def clean_value_for_comparison(val):
            if val is None:
                return ""
            val_str = str(val)
            # Remove currency, percentage, commas
            val_str = val_str.replace('$', '').replace('%', '').replace(',', '').strip()
            # Replace multiple spaces with a single space, then strip again
            val_str = re.sub(r'\s+', ' ', val_str).strip()
            # Convert to lowercase for case-insensitive comparison
            return val_str.lower()

        for label, key in GUI_FIELD_ORDER:
            current_value_raw = current_inputs.get(key, '') # Get raw value from GUI
            original_value_raw = self.original_extracted_data.get(key, '') # Get raw value from original data

            cleaned_current = clean_value_for_comparison(current_value_raw)
            cleaned_original = clean_value_for_comparison(original_value_raw)

            logger.debug(
                f"DEBUG: Comparing '{label}' ({key}): RAW Current='{current_value_raw}', RAW Original='{original_value_raw}'")
            logger.debug(
                f"DEBUG: Comparing '{label}' ({key}): CLEANED Current='{cleaned_current}', CLEANED Original='{cleaned_original}'")
            print(
                f"--- DEBUG PRINT: Comparing '{label}' ({key}): RAW Current='{current_value_raw}', RAW Original='{original_value_raw}'") # Added print
            print(
                f"--- DEBUG PRINT: Comparing '{label}' ({key}): CLEANED Current='{cleaned_current}', CLEANED Original='{cleaned_original}'") # Added print

            diff_entry = {
                'label': label,
                'key': key,
                'current_raw': current_value_raw,
                'original_raw': original_value_raw,
                'type': ''
            }

            # Special handling for numerical fields to allow for minor float differences
            if key in NUMERIC_FIELDS + PERCENTAGE_FIELDS + INTEGER_FIELDS:
                try:
                    # Attempt to convert cleaned values to float for numerical comparison
                    float_current = float(cleaned_current) if cleaned_current else None
                    float_original = float(cleaned_original) if cleaned_original else None

                    # If both are None/empty, they are considered equal
                    if float_current is None and float_original is None:
                        continue
                    # If one is None/empty and the other is not, it's a difference
                    if (float_current is None and float_original is not None) or \
                       (float_current is not None and float_original is None):
                        diff_entry['type'] = '(One value is empty/N/A)'
                        differences.append(diff_entry)
                        continue
                    # Compare numerical values with a tolerance
                    # Use a slightly higher tolerance or round for display
                    if abs(float_current - float_original) > 0.001: # Reduced tolerance from 0.01 to 0.001 for precision
                        diff_entry['type'] = '(Numerical difference)'
                        differences.append(diff_entry)
                except ValueError:
                    # If conversion to float fails for either, treat as string mismatch
                    if cleaned_current != cleaned_original:
                        diff_entry['type'] = '(Non-numeric mismatch after cleaning)'
                        differences.append(diff_entry)
            else:
                # For non-numeric fields, direct cleaned string comparison
                if cleaned_current != cleaned_original:
                    diff_entry['type'] = '(Text mismatch)'
                    differences.append(diff_entry)

        if differences:
            self._show_validation_differences_popup(differences) # Call the custom popup
        else:
            messagebox.showinfo("Validation Success",
                                "Current input matches original extracted data (or no significant differences found).")

        self.status_var.set("Validation completed.")

    def load_defaults(self):
        """Loads default values into input fields and sets their source status to 'default'."""
        for label, field_key in GUI_FIELD_ORDER:
            # Use current_default_values here instead of static DEFAULT_VALUES
            default_value = self.current_default_values.get(field_key, '')
            self._set_input_field_value(field_key, default_value, 'default')
        self.status_var.set("Default values loaded. Calculating financials...")
        self.calculate_projections()

    def calculate_projections(self):
        self.status_var.set("Calculating projections...")
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

        # Reset all outputs to N/A initially before calculations
        for key in self.calculated_outputs:
            self.calculated_outputs[key].set("N/A")

        try:
            gross_scheduled_income = inputs.get('gross_scheduled_income')
            num_units = inputs.get('number_of_units')
            monthly_rent_per_unit = inputs.get('monthly_rent_per_unit')
            purchase_price = inputs.get('purchase_price') # Retrieve here for use in multiple calculations

            # --- GPI Calculation ---
            gpi = None
            if gross_scheduled_income is not None:
                gpi = gross_scheduled_income
                self.status_var.set("Using Gross Scheduled Income for GPI.")
            elif num_units is not None and monthly_rent_per_unit is not None:
                gpi = num_units * monthly_rent_per_unit * 12

            if gpi is None:
                self.status_var.set(
                    "Cannot calculate GPI. Needs 'Number of Units' AND 'Monthly Rent per Unit' OR 'Gross Scheduled Income'.")
                # Removed the 'return' and the _update_output_field_colors call here.
                # The main finally block will handle the color update for all outputs (including 'N/A's).
            else:
                self.calculated_outputs['gpi'].set(f"${gpi:,.2f}")

            # --- Vacancy Cost (VC) Calculation ---
            vacancy_rate = inputs.get('vacancy_rate')
            if vacancy_rate is None:
                try:
                    # Use current_default_values for defaults here
                    vacancy_rate = float(self.current_default_values.get('vacancy_rate', '0') or '0')
                except ValueError:
                    vacancy_rate = 0.0 # Default to 0 if no valid vacancy rate

            vc = gpi * (vacancy_rate / 100) if gpi is not None else None
            if vc is not None:
                self.calculated_outputs['vc'].set(f"${vc:,.2f}")

            # --- Effective Gross Income (EGI) Calculation ---
            egi = gpi - vc if gpi is not None and vc is not None else None
            if egi is not None:
                self.calculated_outputs['egi'].set(f"${egi:,.2f}")

            # --- Expenses Calculation ---
            # Using 'or 0.0' (or appropriate type) to ensure these are numbers for sum
            property_taxes = inputs.get('property_taxes') or float(self.current_default_values.get('property_taxes', '0') or '0')
            insurance = inputs.get('insurance') or float(self.current_default_values.get('insurance', '0') or '0')
            property_management_fees = inputs.get('property_management_fees') or float(
                self.current_default_values.get('property_management_fees', '0') or '0')
            maintenance_repairs = inputs.get('maintenance_repairs') or float(
                self.current_default_values.get('maintenance_repairs', '0') or '0')
            utilities = inputs.get('utilities') or float(self.current_default_values.get('utilities', '0') or '0')

            expenses = (property_taxes + insurance + property_management_fees +
                        maintenance_repairs + utilities)

            # --- Net Operating Income (NOI) Calculation ---
            noi = egi - expenses if egi is not None else None
            if noi is not None:
                self.calculated_outputs['noi'].set(f"${noi:,.2f}")

            # --- Cap Rate Calculation ---
            # Ensure purchase_price is used from inputs, or a default
            if purchase_price is None or purchase_price <= 0:
                purchase_price = float(self.current_default_values.get('purchase_price', '0') or '0')

            if noi is not None and purchase_price > 0:
                cap_rate = (noi / purchase_price) * 100
                self.calculated_outputs['cap_rate'].set(f"{cap_rate:.2f}%")
            else:
                self.calculated_outputs['cap_rate'].set("N/A (Purchase Price/NOI Missing/Zero)")

            # --- Loan Inputs ---
            down_payment_percent = inputs.get('down_payment') or float(self.current_default_values.get('down_payment', '0') or '0')
            interest_rate = inputs.get('interest_rate') or float(self.current_default_values.get('interest_rate', '0') or '0')
            loan_terms_years = inputs.get('loan_terms_years') or int(
                float(self.current_default_values.get('loan_terms_years', '0') or '0'))


            # --- Debt Service Calculation ---
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
                                mortgage_payment = float('inf') # Set to infinity on zero division

                if mortgage_payment is not None and mortgage_payment != float('inf'):
                    self.calculated_outputs['debt_service'].set(f"${mortgage_payment:,.2f}")
                else:
                    self.calculated_outputs['debt_service'].set("N/A (Loan Calculation Issue)")
            else:
                self.calculated_outputs['debt_service'].set("N/A (Loan Inputs Missing/Invalid)")

            # --- Cash Flow Before Tax (CFBT) Calculation ---
            cfbt = None
            debt_service_str = self.calculated_outputs['debt_service'].get()
            if debt_service_str and "N/A" not in debt_service_str and noi is not None:
                try:
                    # Convert monthly debt service to annual for CFBT calculation
                    annual_debt_service_val = float(debt_service_str.replace('$', '').replace(',', '')) * 12
                    cfbt = noi - annual_debt_service_val
                    self.calculated_outputs['cfbt'].set(f"${cfbt:,.2f}")
                except ValueError:
                    self.calculated_outputs['cfbt'].set("N/A (Invalid Debt Service Value)")
            else:
                self.calculated_outputs['cfbt'].set("N/A (NOI or Debt Service Missing)")

            # --- Cash on Cash Return (COC Return) Calculation ---
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

            # --- Gross Rent Multiplier (GRM) Calculation ---
            grm = None
            if purchase_price is not None and purchase_price > 0 and gpi is not None and gpi > 0:
                grm = purchase_price / gpi
                self.calculated_outputs['grm'].set(f"{grm:.2f}")
            else:
                self.calculated_outputs['grm'].set("N/A (Purchase Price or GPI Missing/Zero)")

            # --- Debt Service Coverage Ratio (DSCR) Calculation ---
            dscr = None
            if noi is not None and debt_service_str and "N/A" not in debt_service_str:
                try:
                    # Assuming debt_service_str (from output) is monthly, convert to annual for DSCR
                    monthly_mortgage_payment_val = float(debt_service_str.replace('$', '').replace(',', ''))
                    annual_debt_service = monthly_mortgage_payment_val * 12

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
            # Ensure all outputs show N/A on calculation error
            for key in self.calculated_outputs:
                self.calculated_outputs[key].set("N/A")
        except Exception as e:
            self.status_var.set(f"An unexpected calculation error occurred: {str(e)}")
            logger.error(f"Unexpected calculation error: {e}", exc_info=True)
            # Ensure all outputs show N/A on calculation error
            for key in self.calculated_outputs:
                self.calculated_outputs[key].set("N/A")
        finally:
            # --- CRITICAL CHANGE: This ensures colors are always updated ---
            self.root.after(0, self._update_output_field_colors)
            # Keep your existing progress stop line
            self.root.after(0, lambda: self.progress.stop())
    def save_current_property(self):
        """
        Saves the current data (inputs and calculated outputs) to the database.
        It updates the 'user_input_data' for existing properties
        and inserts a new record (with both original and user data) for new properties.
        """
        current_inputs = {key: var.get() for key, var in self.entry_vars.items()}
        current_outputs = {key: var.get() for key, var in self.calculated_outputs.items()}
        file_path = self.file_path_var.get()
        base_file_name = os.path.basename(file_path) if file_path else "New Property"

        if not file_path and not current_inputs.get('purchase_price') and not current_inputs.get('number_of_units'):
            messagebox.showwarning("Cannot Save",
                                   "Please extract data from a PDF or enter at least a Purchase Price or Number of Units before saving.")
            return

        raw_text_preview_content = self.content_text.get(1.0, tk.END).strip()

        if self.current_property_id:
            success = self.db_manager.update_property(
                self.current_property_id,
                base_file_name,
                file_path,
                raw_text_preview_content,
                user_input_data=current_inputs,
                calculated_financials=current_outputs
            )
            if success:
                messagebox.showinfo("Save Successful",
                                    f"Property '{base_file_name}' (ID: {self.current_property_id}) updated in database.")
                self.populate_file_list()
            else:
                messagebox.showerror("Save Error", f"Failed to update property '{base_file_name}'.")
        else:
            new_id = self.db_manager.insert_property(
                file_name=base_file_name,
                original_file_path=file_path,
                raw_text_preview=raw_text_preview_content,
                original_extracted_data=self.original_extracted_data, # This will now store the full GUI snapshot
                user_input_data=current_inputs,
                calculated_financials=current_outputs
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
        """Clears all input fields, output fields, and resets current property context."""
        self.current_property_id = None
        self.clear_input_fields()
        self.file_path_var.set("")
        self.original_extracted_data = {}
        logger.debug("DEBUG: self.original_extracted_data cleared in clear_data.")
        print("--- DEBUG PRINT: self.original_extracted_data cleared in clear_data.")  # Added print
        for var in self.calculated_outputs.values():
            var.set("N/A")
        for label_widget in self.output_labels.values():
            label_widget.config(background=C21_LIGHT_GRAY)
        self.content_text.delete(1.0, tk.END)
        self.status_var.set("Ready")
        self.property_list_treeview.selection_remove(self.property_list_treeview.selection())

    def _open_default_settings_window(self):
        """Opens a new window to allow editing of default input variables."""
        settings_popup = tk.Toplevel(self.root)
        settings_popup.title("Edit Default Settings")
        settings_popup.transient(self.root)
        settings_popup.grab_set()
        settings_popup.geometry("450x600")
        settings_popup.resizable(False, True) # Allow vertical resizing for more fields
        settings_popup.config(bg=C21_LIGHT_GRAY)

        # Center the popup
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (settings_popup.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (settings_popup.winfo_height() // 2)
        settings_popup.geometry(f"+{x}+{y}")


        header_label = ttk.Label(settings_popup, text="Adjust Default Input Values:",
                                 font=('Arial', 12, 'bold'), foreground=C21_GOLD, background=C21_LIGHT_GRAY, padding=10)
        header_label.pack(pady=(10, 5))

        # Use a Canvas with a Scrollbar for many fields
        canvas = tk.Canvas(settings_popup, bg=C21_LIGHT_GRAY, highlightthickness=0)
        # Pack canvas first, so buttons can be reliably placed below it
        canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=15, pady=(0, 10)) # Adjusted pady

        scrollbar = ttk.Scrollbar(settings_popup, orient=tk.VERTICAL, command=canvas.yview)
        # Ensure scrollbar is associated with the popup (settings_popup) and positioned correctly
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.configure(yscrollcommand=scrollbar.set)

        # Frame inside canvas to hold the actual input widgets
        defaults_frame = ttk.Frame(canvas, style='TFrame', padding=10)
        # Use create_window to put the frame inside the canvas
        canvas.create_window((0, 0), window=defaults_frame, anchor="nw", tags="defaults_frame")

        # Bind the canvas's size to update the scrollregion
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        defaults_frame.bind("<Configure>", on_frame_configure)
        # Also bind canvas resize to update scrollregion for when window is resized
        canvas.bind('<Configure>', on_frame_configure)


        defaults_frame.columnconfigure(1, weight=1)

        temp_entry_vars = {} # To store StringVar for the popup
        for i, (label, key) in enumerate(GUI_FIELD_ORDER):
            if key in self.current_default_values: # Only show fields that have a default value
                ttk.Label(defaults_frame, text=f"{label}:", foreground=C21_BLACK).grid(row=i, column=0, sticky=tk.W, pady=2)
                var = tk.StringVar(value=str(self.current_default_values.get(key, '')))
                entry = ttk.Entry(defaults_frame, textvariable=var, width=30)
                entry.grid(row=i, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
                temp_entry_vars[key] = var

        def save_defaults():
            updated_defaults = {}
            for key, var in temp_entry_vars.items():
                val = var.get()
                # Ensure numeric fields are stored as numbers if possible
                if val:
                    try:
                        if key in NUMERIC_FIELDS or key in PERCENTAGE_FIELDS:
                            updated_defaults[key] = float(val)
                        elif key in INTEGER_FIELDS:
                            updated_defaults[key] = int(float(val)) # Use float first to handle decimals like "5.0"
                        else:
                            updated_defaults[key] = val # Keep as string for other types
                    except ValueError:
                        updated_defaults[key] = val # Keep as string if conversion fails
                else:
                    updated_defaults[key] = val # Handle empty string

            self.current_default_values.update(updated_defaults)
            # --- NEW: Save to file after updating in memory ---
            self._save_persistent_defaults()
            # --- END NEW ---
            messagebox.showinfo("Settings Saved", "Default values updated and saved for all sessions.")
            self.load_defaults() # Reload defaults into main GUI
            settings_popup.destroy()

        # --- NEW: Function to reset defaults to original config values ---
        def reset_defaults_to_original():
            confirmed = messagebox.askyesno("Confirm Reset",
                                            "Are you sure you want to reset all defaults to their original configured values? This change will be permanent across sessions.")
            if confirmed:
                self.current_default_values = self.original_config_defaults.copy() # Reset to original config values
                # --- NEW: Save this reset state to file ---
                self._save_persistent_defaults()
                # --- END NEW ---
                # Update the StringVars in the popup to reflect the reset
                for key, var in temp_entry_vars.items():
                    var.set(str(self.current_default_values.get(key, '')))
                messagebox.showinfo("Defaults Reset", "Default values have been reset to original settings and saved.")
                self.load_defaults() # Reload these original defaults into the main GUI
        # --- END NEW ---

        def cancel_defaults():
            settings_popup.destroy()

        # Create a separate frame for buttons and pack it at the bottom
        buttons_frame = ttk.Frame(settings_popup, style='TFrame')
        buttons_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10) # Packed at the bottom of the popup

        save_btn = ttk.Button(buttons_frame, text="Save Changes", command=save_defaults, style='Accent.TButton')
        save_btn.pack(side=tk.LEFT, padx=5)

        # --- NEW: Reset button ---
        reset_btn = ttk.Button(buttons_frame, text="Reset to Original", command=reset_defaults_to_original)
        reset_btn.pack(side=tk.LEFT, padx=5)
        # --- END NEW ---

        cancel_btn = ttk.Button(buttons_frame, text="Cancel", command=cancel_defaults)
        cancel_btn.pack(side=tk.LEFT, padx=5)

        settings_popup.wait_window()

    def _export_current_data(self):
        """Exports current input data and calculated financials to a file."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")],
            title="Export Current Data"
        )
        if not file_path:
            return

        export_data = {
            "input_data": {key: var.get() for key, var in self.entry_vars.items()},
            "calculated_financials": {key: var.get() for key, var in self.calculated_outputs.items()},
            "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=4)
            messagebox.showinfo("Export Successful", f"Data successfully exported to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data: {e}")

    def _show_about_dialog(self):
        """Displays an About dialog with application information."""
        about_message = (
            f"{APP_NAME} v{APP_VERSION}\n\n"
            "A desktop application for extracting real estate data from MLS PDF files "
            "and calculating financial projections.\n\n"
            "Developed by [Your Name/Organization Here]\n"
            "Contact: your.email@example.com\n\n"
            "Data extraction powered by PDF parsing techniques and regular expressions.\n"
            "Financial calculations based on standard real estate metrics."
        )
        messagebox.showinfo("About " + APP_NAME, about_message)


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