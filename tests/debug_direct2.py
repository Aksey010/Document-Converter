"""Test with debug prints in the handler."""
import sys
sys.path.insert(0, r'D:\Downloads\Go fr\File converter')

from converter import DocumentConverter

converter = DocumentConverter()

import fitz
import tempfile
import os

# Create empty PDF
doc = fitz.open()
page = doc.new_page()
empty_pdf = os.path.join(tempfile.gettempdir(), 'test_empty.pdf')
doc.save(empty_pdf)
doc.close()

print("Testing converter.convert() directly...")
result = converter.convert(empty_pdf, 'txt')
print(f"Result: success={result.success}, error={result.error}, output_size={result.output_size}")

if result.success and result.output_path:
    with open(result.output_path, 'r') as f:
        content = f.read()
        print(f"Output content: {content!r}")

os.remove(empty_pdf)