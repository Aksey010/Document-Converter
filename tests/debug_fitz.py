"""Debug the fitz issue."""
from converter.libraries import get_libraries

libs = get_libraries()
fitz = libs.get_fitz()
print('Direct call fitz:', fitz, type(fitz))

# Now simulate what pdf_handler does
from converter.libraries import get_libraries as get_libs2
libs2 = get_libs2()
print('Second call libs is same:', libs is libs2)
fitz2 = libs2.get_fitz()
print('Second call fitz:', fitz2, type(fitz2))

# Check the _available dict
print('_available:', libs._available)