"""Debug the web conversion flow."""
import subprocess
import sys
import time
import tempfile
import os
import http.client
import json
import fitz

# Create test PDFs
tmpdir = tempfile.gettempdir()

# Empty PDF
doc = fitz.open()
page = doc.new_page()
empty_pdf = os.path.join(tmpdir, 'test_empty.pdf')
doc.save(empty_pdf)
doc.close()

# Start server
proc = subprocess.Popen([sys.executable, 'main.py'], cwd=r'D:\Downloads\Go fr\File converter')
time.sleep(4)

try:
    # Test conversion
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    with open(empty_pdf, 'rb') as f:
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
        b'txt',
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
    
    print('Response:', json.dumps(data, indent=2))
    
    if data.get('success') and data.get('task_id'):
        # Check progress
        task_id = data['task_id']
        for _ in range(20):
            time.sleep(0.5)
            conn = http.client.HTTPConnection('localhost', 8080, timeout=10)
            conn.request('GET', f'/api/convert/progress/{task_id}')
            resp = conn.getresponse()
            data = resp.read().decode()
            print('Progress:', data)
            conn.close()
            try:
                progress_data = json.loads(data.split('\n')[-2])  # Last complete event
                if progress_data.get('status') in ('completed', 'error'):
                    break
            except:
                pass
        
finally:
    proc.terminate()
    proc.wait(timeout=5)
    os.remove(empty_pdf)