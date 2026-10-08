"""Debug the actual handler call."""
import asyncio
import sys
import tempfile
import os
import fitz

sys.path.insert(0, '.')

from converter import DocumentConverter

async def test():
    converter = DocumentConverter()
    
    # Create test PDF
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((100, 100), 'Test PDF for debug')
    test_pdf = os.path.join(tempfile.gettempdir(), 'debug_test.pdf')
    doc.save(test_pdf)
    doc.close()
    
    # Get the PDF handler
    from converter.formats.pdf_handler import PDFHandler
    handler = PDFHandler()
    
    print('Handler _libs:', handler._libs)
    fitz_mod = handler._get_fitz()
    print('Handler _get_fitz():', fitz_mod, type(fitz_mod))
    
    # Try to use it
    if fitz_mod:
        print('fitz_mod.open exists:', hasattr(fitz_mod, 'open'))
    
    # Now test the actual conversion through DocumentConverter
    result = converter.convert(test_pdf, 'docx')
    print(f"Result: success={result.success}, error={result.error}")
    
    os.remove(test_pdf)

asyncio.run(test())