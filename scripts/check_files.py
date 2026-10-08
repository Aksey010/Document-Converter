import os
root = r'D:\Downloads\Go fr\File converter'
files = ['main.py', 'requirements.txt', 'venv_converter\\Scripts\\python.exe']
for f in files:
    p = os.path.join(root, f)
    print(f'{f}: {"EXISTS" if os.path.exists(p) else "MISSING"}')