"""Test all fixes."""
import subprocess
import sys
import time
import tempfile
import os
import http.client
import json
import fitz
from PIL import Image
from docx import Document

def create_test_files():
    test_files = {}
    tmpdir = tempfile.gettempdir()
    
    # PDF with text
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((100, 100), 'Test PDF with text content for extraction')
    pdf_path = os.path.join(tmpdir, 'test_text.pdf')
    doc.save(pdf_path)
    doc.close()
    
    # PDF without text (empty)
    doc = fitz.open()
    page = doc.new_page()
    # Don't add any text
    empty_pdf_path = os.path.join(tmpdir, 'test_empty.pdf')
    doc.save(empty_pdf_path)
    doc.close()
    
    # Image-based PDF (create from image)
    doc = fitz.open()
    page = doc.new_page()
    img = Image.new('RGB', (200, 200), color='red')
    img_path = os.path.join(tmpdir, 'temp_img.png')
    img.save(img_path)
    page.insert_image(page.rect, filename=img_path)
    scanned_pdf_path = os.path.join(tmpdir, 'test_scanned.pdf')
    doc.save(scanned_pdf_path)
    doc.close()
    os.remove(img_path)
    
    return {
        'text_pdf': pdf_path,
        'empty_pdf': empty_pdf_path,
        'scanned_pdf': scanned_pdf_path
    }

def test_conversion(input_path, output_format):
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    with open(input_path, 'rb') as f:
        file_data = f.read()
    
    body_parts = [
        b'--' + boundary.encode(),
        b'Content-Disposition: form-data; name="file"; filename="test.pdf"',
        b'Content-Type: application/pdf',
        b'',
        file_data,
        b'--' + boundary.encode(),
        b'Content-Disposition: form-data; name="output_format"',
        b'',
        output_format.encode(),
        b'--' + boundary.encode(),
        b'Content-Disposition: form-data; name="options"',
        b'',
        b'{"quality":85,"dpi":150}',
        b'--' + boundary.encode() + b'--'
    ]
    body = b'\r\n'.join(body_parts)
    
    conn = http.client.HTTPConnection('localhost', 8080, timeout=60)
    conn.request('POST', '/api/convert', body, {
        'Content-Type': 'multipart/form-data; boundary=' + boundary,
        'Content-Length': str(len(body))
    })
    resp = conn.getresponse()
    data = json.loads(resp.read().decode())
    conn.close()
    return data

def main():
    from converter import DocumentConverter
    
    print("Starting server...")
    proc = subprocess.Popen([sys.executable, 'main.py'], cwd=r'D:\Downloads\Go fr\File converter')
    time.sleep(4)
    
    try:
        print("Creating test files...")
        test_files = create_test_files()
        
        converter = DocumentConverter()
        print("Supported formats:", converter.get_supported_output_formats('pdf'))
        
        print("\n=== Testing PDF -> TXT ===")
        
        # Test 1: PDF with text
        print("1. PDF with text content:")
        result = test_conversion(test_files['text_pdf'], 'txt')
        print(f"   Success: {result.get('success')}, Error: {result.get('error', 'N/A')}")
        if result.get('success'):
            print(f"   Output size: {result.get('output_size', 0)} bytes")
        
        # Test 2: Empty PDF
        print("2. Empty PDF (no text):")
        result = test_conversion(test_files['empty_pdf'], 'txt')
        print(f"   Success: {result.get('success')}, Error: {result.get('error', 'N/A')}")
        
        # Test 3: Scanned PDF (image-based)
        print("3. Image-based PDF (scanned):")
        result = test_conversion(test_files['scanned_pdf'], 'txt')
        print(f"   Success: {result.get('success')}, Error: {result.get('error', 'N/A')}")
        
        # Test 4: Normal conversions still work
        print("\n=== Testing other conversions ===")
        for fmt in ['docx', 'html', 'png']:
            result = test_conversion(test_files['text_pdf'], fmt)
            print(f"   PDF -> {fmt}: {'OK' if result.get('success') else 'FAIL'} ({result.get('error', 'OK')})")
        
    finally:
        proc.terminate()
        proc.wait(timeout=5)
        for path in test_files.values():
            try:
                os.remove(path)
            except:
                pass

if __name__ == '__main__':
    main()