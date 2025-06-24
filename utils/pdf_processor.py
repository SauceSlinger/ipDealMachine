# PDF processing utilities

import os
import logging

try:
    import pdfplumber

    PDF_LIBRARY = "pdfplumber"
except ImportError:
    try:
        import PyPDF2

        PDF_LIBRARY = "PyPDF2"
    except ImportError:
        PDF_LIBRARY = None

from config import MAX_FILE_SIZE_MB, SUPPORTED_FORMATS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFProcessor:
    def __init__(self):
        self.supported_library = PDF_LIBRARY

    def validate_file(self, file_path):
        """Validate PDF file"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Check file extension
        _, ext = os.path.splitext(file_path.lower())
        if ext not in SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported file format: {ext}")

        # Check file size
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            raise ValueError(f"File too large: {file_size_mb:.1f}MB (max: {MAX_FILE_SIZE_MB}MB)")

        return True

    def extract_text(self, file_path):
        """Extract text from PDF file"""
        if not self.supported_library:
            raise RuntimeError("No PDF processing library available")

        self.validate_file(file_path)

        text = ""
        try:
            if self.supported_library == "pdfplumber":
                text = self._extract_with_pdfplumber(file_path)
            elif self.supported_library == "PyPDF2":
                text = self._extract_with_pypdf2(file_path)
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            raise

        return text

    def _extract_with_pdfplumber(self, file_path):
        """Extract text using pdfplumber"""
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text

    def _extract_with_pypdf2(self, file_path):
        """Extract text using PyPDF2"""
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text