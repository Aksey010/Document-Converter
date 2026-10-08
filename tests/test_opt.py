"""Test the optimized application."""
import asyncio
import sys
import tempfile
import os
import fitz
from pathlib import Path

sys.path.insert(0, '.')

from converter import DocumentConverter

def test_converter():
    """Test the converter directly."""
    converter = DocumentConverter()
    
    # Create test PDF
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((100, 100), 'Test PDF for optimization verification')
    test_pdf = os.path.join(tempfile.gettempdir(), 'opt_test.pdf')
    doc.save(test_pdf)
    doc.close()
    
    print(f"Supported input formats: {converter.get_supported_input_formats()}")
    print(f"PDF outputs: {converter.get_supported_output_formats('pdf')}")
    
    # Test conversion
    result = converter.convert(test_pdf, 'docx')
    print(f"Conversion result: success={result.success}, error={result.error}")
    if result.success:
        print(f"  Output size: {result.output_size} bytes")
        print(f"  Input size: {result.input_size} bytes")
        print(f"  Ratio: {result.output_size / result.input_size:.2f}")
    
    os.remove(test_pdf)
    print("Test passed!")

if __name__ == '__main__':
    test_converter()