"""Debug the PDF text extraction in the web context."""
import subprocess
import sys
import time
import tempfile
import os
import fitz

# Test the handler directly
from converter.formats.pdf_handler import PDFHandler
from converter.core import ConversionOptions

handler = PDFHandler()

# Create test PDFs
tmpdir = tempfile.gettempdir()

# Empty PDF
doc = fitz.open()
page = doc.new_page()
empty_pdf = os.path.join(tmpdir, 'test_empty.pdf')
doc.save(empty_pdf)
doc.close()

# Test the handler directly
options = ConversionOptions()
try:
    result = handler._convert_pdf_to_text(empty_pdf, os.path.join(tmpdir, 'output.txt'), options)
    print(f"Result: {result}")
    with open(os.path.join(tmpdir, 'output.txt'), 'r') as f:
        content = f.read()
        print(f"Output content: {content!r}")
except Exception as e:
    print(f"Exception raised: {type(e).__name__}: {e}")

# Cleanup
for p in [empty_pdf, os.path.join(tmpdir, 'output.txt')]:
    try:
        os.remove(p)
    except:
        pass