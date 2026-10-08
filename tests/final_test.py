"""Final comprehensive test."""
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
from converter import DocumentConverter

def create_test_files():
    test_files = {}
    tmpdir = tempfile.gettempdir()
    
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((100, 100), 'Test PDF content')
    pdf_path = os.path.join(tmpdir, 'test_input.pdf')
    doc.save(pdf_path)
    doc.close()
    test_files['pdf'] = pdf_path
    
    docx_doc = Document()
    docx_doc.add_paragraph('Test DOCX content')
    docx_path = os.path.join(tmpdir, 'test_input.docx')
    docx_doc.save(docx_path)
    test_files['docx'] = docx_path
    
    txt_path = os.path.join(tmpdir, 'test_input.txt')
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write('Test TXT content\nLine 2\nLine 3')
    test_files['txt'] = txt_path
    
    html_path = os.path.join(tmpdir, 'test_input.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write('<html><body><h1>Test HTML</h1><p>Content here</p></body></html>')
    test_files['html'] = html_path
    
    png_path = os.path.join(tmpdir, 'test_input.png')
    img = Image.new('RGB', (200, 200), color='red')
    img.save(png_path)
    test_files['png'] = png_path
    
    jpg_path = os.path.join(tmpdir, 'test_input.jpg')
    img = Image.new('RGB', (200, 200), color='blue')
    img.save(jpg_path, 'JPEG')
    test_files['jpeg'] = jpg_path
    test_files['jpg'] = jpg_path
    
    tiff_path = os.path.join(tmpdir, 'test_input.tiff')
    img = Image.new('RGB', (200, 200), color='green')
    img.save(tiff_path, 'TIFF')
    test_files['tiff'] = tiff_path
    
    bmp_path = os.path.join(tmpdir, 'test_input.bmp')
    img = Image.new('RGB', (200, 200), color='yellow')
    img.save(bmp_path, 'BMP')
    test_files['bmp'] = bmp_path
    
    webp_path = os.path.join(tmpdir, 'test_input.webp')
    img = Image.new('RGB', (200, 200), color='purple')
    img.save(webp_path, 'WEBP')
    test_files['webp'] = webp_path
    
    gif_path = os.path.join(tmpdir, 'test_input.gif')
    img = Image.new('P', (200, 200), color=1)
    img.save(gif_path, 'GIF')
    test_files['gif'] = gif_path
    
    return test_files

def test_conversion(input_fmt, input_path, output_fmt):
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    with open(input_path, 'rb') as f:
        file_data = f.read()
    
    body_parts = [
        b'--' + boundary.encode(),
        b'Content-Disposition: form-data; name="file"; filename="test.' + input_fmt.encode() + b'"',
        b'Content-Type: application/octet-stream',
        b'',
        file_data,
        b'--' + boundary.encode(),
        b'Content-Disposition: form-data; name="output_format"',
        b'',
        output_fmt.encode(),
        b'--' + boundary.encode(),
        b'Content-Disposition: form-data; name="options"',
        b'',
        b'{"quality":85,"dpi":150}',
        b'--' + boundary.encode() + b'--'
    ]
    body = b'\r\n'.join(body_parts)
    
    conn = http.client.HTTPConnection('localhost', 8080, timeout=30)
    try:
        conn.request('POST', '/api/convert', body, {
            'Content-Type': 'multipart/form-data; boundary=' + boundary,
            'Content-Length': str(len(body))
        })
        resp = conn.getresponse()
        data = json.loads(resp.read().decode())
        conn.close()
        return data
    except Exception as e:
        conn.close()
        return {'success': False, 'error': f'Connection error: {e}'}

converter = DocumentConverter()
input_formats = converter.get_supported_input_formats()

print('Starting server...')
proc = subprocess.Popen([sys.executable, 'main.py'], cwd=r'D:\Downloads\Go fr\File converter')
time.sleep(4)

try:
    print('Creating test files...')
    test_files = create_test_files()
    
    total = 0
    passed = 0
    
    for input_fmt in input_formats:
        if input_fmt not in test_files:
            print(f'SKIP {input_fmt}: no test file')
            continue
            
        input_path = test_files[input_fmt]
        output_formats = converter.get_supported_output_formats(input_fmt)
        
        print(f'\n{input_fmt} -> {output_formats}')
        
        for output_fmt in output_formats:
            total += 1
            print(f'  {input_fmt} -> {output_fmt}... ', end='', flush=True)
            result = test_conversion(input_fmt, input_path, output_fmt)
            
            if result.get('success'):
                print(f'OK ({result.get("output_size", 0)} bytes)')
                passed += 1
            else:
                print(f'FAIL: {result.get("error", "Unknown")[:80]}')
    
    print(f'\n=== RESULT: {passed}/{total} passed ===')
    
finally:
    proc.terminate()
    proc.wait(timeout=5)
    for path in test_files.values():
        try:
            os.remove(path)
        except:
            pass