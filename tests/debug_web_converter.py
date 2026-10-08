"""Debug the web app converter."""
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
page.insert_text((100, 100), 'Test PDF for debug')
test_pdf = os.path.join(tempfile.gettempdir(), 'debug_web.pdf')
doc.save(test_pdf)
doc.close()

# Start server with debug
proc = subprocess.Popen([sys.executable, '-c', '''
import sys
sys.path.insert(0, r"D:\\Downloads\\Go fr\\File converter")
from web_converter.app import converter
print("Converter instance:", id(converter))
print("Converter handlers:", list(converter._handlers.keys()))
for fmt, handler in converter._handlers.items():
    print(f"  Handler {fmt}: {type(handler).__name__}")
    if hasattr(handler, "_libs"):
        fitz = handler._get_fitz()
        print(f"    {fmt} _get_fitz(): {fitz} ({type(fitz)})")
'''], cwd=r'D:\Downloads\Go fr\File converter', stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

stdout, stderr = proc.communicate(timeout=10)
print("STDOUT:")
print(stdout)
print("STDERR:")
print(stderr)