"""Direct test of PDF text extraction."""
import fitz
import tempfile
import os

# Test 1: PDF with text
doc = fitz.open()
page = doc.new_page()
page.insert_text((100, 100), 'Test PDF with text content for extraction')
text_pdf = os.path.join(tempfile.gettempdir(), 'test_text.pdf')
doc.save(text_pdf)
doc.close()

# Test 2: Empty PDF
doc = fitz.open()
page = doc.new_page()
empty_pdf = os.path.join(tempfile.gettempdir(), 'test_empty.pdf')
doc.save(empty_pdf)
doc.close()

# Test 3: Scanned PDF (image-based)
from PIL import Image
doc = fitz.open()
page = doc.new_page()
img = Image.new('RGB', (200, 200), color='red')
img_path = os.path.join(tempfile.gettempdir(), 'temp_img.png')
img = Image.new('RGB', (200, 200), color='red')
img.save(img_path)
page.insert_image(page.rect, filename=img_path)
scanned_pdf = os.path.join(tempfile.gettempdir(), 'test_scanned.pdf')
doc.save(scanned_pdf)
doc.close()
os.remove(img_path)

def test_extract(pdf_path, name):
    print(f"\n=== Testing {name} ===")
    doc = fitz.open(pdf_path)
    text_parts = []
    
    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text()
        print(f"  Page {i+1} text: {text!r}")
        if text.strip():
            text_parts.append(text)
    
    doc.close()
    
    print(f"  text_parts: {text_parts}")
    print(f"  bool(text_parts): {bool(text_parts)}")
    
    if not text_parts:
        print("  -> Would raise error!")
    else:
        print("  -> Would succeed")

test_extract(text_pdf, "PDF with text")
test_extract(empty_pdf, "Empty PDF")
test_extract(scanned_pdf, "Scanned PDF")

# Cleanup
for p in [text_pdf, empty_pdf, scanned_pdf]:
    try:
        os.remove(p)
    except:
        pass