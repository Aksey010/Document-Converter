"""Debug the actual handler in web context."""
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
page.insert_text((100, 100), 'Test BMP for debug')
test_bmp = os.path.join(tempfile.gettempdir(), 'debug.bmp')
img = fitz.open()  # just to have fitz available
from PIL import Image
img = Image.new('RGB', (100, 100), color='red')
img.save(test_bmp)

# Start server with debug
proc = subprocess.Popen([sys.executable, '-c', '''
import sys
sys.path.insert(0, r"D:\\Downloads\\Go fr\\File converter")
from web_converter.app import converter
print("Converter instance:", id(converter))
print("Converter handlers:", list(converter._handlers.keys()))
for fmt, handler in converter._handlers.items():
    if fmt in ("bmp", "png", "jpeg", "jpg", "tiff", "webp", "gif"):
        print(f"  Handler {fmt}: {type(handler).__name__}")
        if hasattr(handler, "_libs"):
            pillow = handler._get_pillow()
            print(f"    {fmt} _get_pillow(): {pillow} ({type(pillow)})")
            print(f"    has open: {hasattr(pillow, 'open')}")
'''], cwd=r'D:\Downloads\Go fr\File converter', stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

stdout, stderr = proc.communicate(timeout=10)
print("STDOUT:")
print(stdout)
print("STDERR:")
print(stderr)