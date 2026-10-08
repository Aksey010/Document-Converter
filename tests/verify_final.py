"""Final verification test."""
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
page.insert_text((100, 100), 'Final verification test')
test_pdf = os.path.join(tempfile.gettempdir(), 'final_verify.pdf')
doc.save(test_pdf)
doc.close()

# Start server
proc = subprocess.Popen([sys.executable, 'main.py'], cwd=r'D:\Downloads\Go fr\File converter')
time.sleep(3)

try:
    # Test conversion
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
    
    conn = http.client.HTTPConnection('localhost', 8080, timeout=30)
    conn.request('POST', '/api/convert', body, {
        'Content-Type': 'multipart/form-data; boundary=' + boundary,
        'Content-Length': str(len(body))
    })
    resp = conn.getresponse()
    data = json.loads(resp.read().decode())
    conn.close()
    
    if data.get('success'):
        print('Final verification: PASSED')
    else:
        print('Final verification: FAILED -', data.get('error', ''))
    
finally:
    proc.terminate()
    proc.wait(timeout=5)
    os.remove(test_pdf)