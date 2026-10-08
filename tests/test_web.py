"""Test the web application."""
import subprocess
import sys
import time
import tempfile
import os
import http.client
import json
import fitz

# Create a test PDF
doc = fitz.open()
page = doc.new_page()
page.insert_text((100, 100), 'Test PDF for web app')
test_pdf = os.path.join(tempfile.gettempdir(), 'web_test.pdf')
doc.save(test_pdf)
doc.close()

# Start server
proc = subprocess.Popen([sys.executable, 'main.py'], cwd=r'D:\Downloads\Go fr\File converter')
time.sleep(4)

try:
    # Test 1: API formats
    conn = http.client.HTTPConnection('localhost', 8080, timeout=10)
    conn.request('GET', '/api/formats')
    resp = conn.getresponse()
    data = json.loads(resp.read().decode())
    print('API formats OK:', 'pdf' in data['input_formats'])
    conn.close()
    
    # Test 2: Status endpoint
    conn = http.client.HTTPConnection('localhost', 8080, timeout=10)
    conn.request('GET', '/api/status')
    resp = conn.getresponse()
    data = json.loads(resp.read().decode())
    print('Status endpoint OK:', data.get('status'))
    print('  Conversions max:', data.get('conversions_max'))
    print('  Libraries loaded:', data.get('libraries'))
    conn.close()
    
    # Test 3: Conversion
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    with open(test_pdf, 'rb') as f:
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
        b'docx',
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
    print('Conversion result:', data.get('success'), data.get('error', ''))
    conn.close()
    
finally:
    proc.terminate()
    proc.wait(timeout=5)
    os.remove(test_pdf)

print('All web tests passed!')