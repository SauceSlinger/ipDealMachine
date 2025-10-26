# MLS PDF Data Extractor

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A modern desktop application for extracting real estate data from MLS PDF documents and performing comprehensive financial projections. Built with CustomTkinter for a beautiful, responsive interface.

## ✨ Features

### 🎨 Modern UI with CustomTkinter
- Beautiful off-white theme with mint and gold accents
- Rounded corners and modern styling
- Responsive three-column layout
- Color-coded input fields and financial projections

### 📊 Dynamic Data Visualization
- **Input Fields**: Color-coded by data source
  - 🟡 Yellow: Default values
  - 🔵 Blue: Manually adjusted data
  - 🟢 Green: PDF-extracted data
- **Financial Projections**: 7-color gradient system
  - 🔴 Red: Poor performance
  - ⚪ White: Break-even
  - 🟢 Green: Excellent performance

### 🤖 Advanced PDF Processing
- Intelligent pattern recognition for MLS documents
- Support for multiple PDF formats and layouts
- Fallback processing with PyPDF2
- Comprehensive data extraction including:
  - Property details (address, MLS number, community)
  - Financial data (purchase price, taxes, expenses)
  - Property specifications (sqft, units, year built)

### 💰 Financial Analysis
Comprehensive real estate investment calculations:
- **GPI** - Gross Potential Income
- **V&C** - Vacancy and Credit Loss
- **EGI** - Effective Gross Income
- **NOI** - Net Operating Income
- **Cap Rate** - Capitalization Rate
- **Debt Service** - Mortgage Payment
- **CFBT** - Cash Flow Before Taxes
- **CoC Return** - Cash-on-Cash Return
- **GRM** - Gross Rent Multiplier
- **DSCR** - Debt Service Coverage Ratio

### 🗄️ Data Management
- SQLite database for persistent storage
- Save/load property data and projections
- JSON export functionality
- Property list with search and filtering

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- Tkinter (usually included with Python)

### Quick Start
```bash
# Clone the repository
git clone https://github.com/yourusername/ipDealMachine.git
cd ipDealMachine

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python Main.py
```

### Dependencies
- `customtkinter` - Modern UI framework
- `pdfplumber` - Primary PDF processing
- `PyPDF2` - Fallback PDF processing
- `pillow` - Image processing
- `tkinter-tooltip` - Enhanced tooltips

## 📖 Usage

1. **Launch the Application**
   ```bash
   python Main.py
   ```

2. **Load a PDF**
   - Click "Browse" to select an MLS PDF file
   - Click "Extract Data" to automatically parse the document

3. **Review & Adjust Data**
   - Observe color-coded input fields
   - Manually adjust values as needed
   - Watch real-time financial projections update

4. **Save & Manage Properties**
   - Click "Save Current Data" to store in database
   - Use the property list to load saved properties
   - Export data as JSON files

## 🏗️ Project Structure

```
ipDealMachine/
├── Main.py                 # Main application GUI and logic
├── config.py               # Configuration settings and defaults
├── patterns.py             # Regex patterns for PDF extraction
├── requirements.txt        # Python dependencies
├── setup.py               # Package setup script
├── build.sh               # Build script for distribution
├── README.md              # This file
├── .gitignore            # Git ignore rules
├── data/                  # Data directory (ignored by git)
│   ├── mls_properties.db  # SQLite database (auto-created)
│   ├── exports/           # JSON export files
│   └── sample_pdfs/       # Sample PDF files
├── utils/                 # Utility modules
│   ├── __init__.py
│   ├── pdf_processor.py   # PDF text extraction
│   ├── data_validator.py  # Data validation logic
│   └── database.py        # Database operations
└── tests/                 # Unit tests
    ├── __init__.py
    └── test_extractor.py  # Test cases
```

## 🔧 Configuration

Customize default values in `config.py`:
- Default financial assumptions
- Color schemes and themes
- Database settings
- UI layout parameters

## 🧪 Testing

Run the test suite:
```bash
python -m pytest tests/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- PDF processing powered by [pdfplumber](https://github.com/jsvine/pdfplumber)
- Inspired by real estate investment analysis needs

## 📞 Support

If you encounter issues or have questions:
- Open an [issue](https://github.com/yourusername/ipDealMachine/issues) on GitHub
- Check the troubleshooting section in the wiki
- Review the FAQ for common questions

---

**Happy Investing! 🏠💰**