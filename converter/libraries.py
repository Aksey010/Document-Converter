"""Shared library manager - singleton instances for heavy libraries."""

import threading
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class LibraryManager:
    """Thread-safe singleton manager for heavy libraries."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        # Library instances (lazy loaded)
        self._fitz = None
        self._pillow = None
        self._docx = None
        self._docx_shared = None  # Inches, etc.
        self._pdf2image = None
        self._bs4 = None
        self._html2docx = None
        self._pytesseract = None
        self._mammoth = None
        self._weasyprint = None
        
        # Loading state tracking
        self._load_locks = {
            'fitz': threading.Lock(),
            'pillow': threading.Lock(),
            'docx': threading.Lock(),
            'pdf2image': threading.Lock(),
            'bs4': threading.Lock(),
            'html2docx': threading.Lock(),
            'pytesseract': threading.Lock(),
            'mammoth': threading.Lock(),
            'weasyprint': threading.Lock(),
        }
        
        # Availability flags
        self._available = {}
    
    def _load_with_lock(self, name: str, loader, default=None):
        """Thread-safe lazy loading."""
        if name in self._available:
            return self._available[name]
        
        with self._load_locks[name]:
            if name in self._available:
                return self._available[name]
            
            try:
                result = loader()
                setattr(self, f'_{name}', result)
                self._available[name] = result
                logger.debug(f"Loaded library: {name}")
                return result
            except Exception as e:
                logger.warning(f"Failed to load {name}: {e}")
                self._available[name] = None
                return None
    
    # --- fitz (PyMuPDF) ---
    def get_fitz(self):
        """Get fitz module."""
        if not self._load_with_lock('fitz', lambda: __import__('fitz')):
            return None
        return self._fitz
    
    # --- Pillow ---
    def get_pillow(self):
        """Get PIL.Image module."""
        def _load_pillow():
            import PIL.Image
            return PIL.Image
        if not self._load_with_lock('pillow', _load_pillow):
            return None
        return self._pillow
    
    # --- python-docx ---
    def get_docx(self):
        """Get docx.Document class."""
        if not self._load_with_lock('docx', lambda: __import__('docx').Document):
            return None
        return self._docx
    
    def get_docx_shared(self):
        """Get docx.shared.Inches."""
        if self._docx_shared is None and self.get_docx():
            try:
                from docx.shared import Inches
                self._docx_shared = Inches
            except ImportError:
                pass
        return self._docx_shared
    
    # --- pdf2image ---
    def get_pdf2image(self):
        """Get pdf2image.convert_from_path function."""
        if not self._load_with_lock('pdf2image', lambda: __import__('pdf2image').convert_from_path):
            return None
        return self._pdf2image
    
    # --- BeautifulSoup4 ---
    def get_bs4(self):
        """Get BeautifulSoup class."""
        if not self._load_with_lock('bs4', lambda: __import__('bs4').BeautifulSoup):
            return None
        return self._bs4
    
    # --- html2docx ---
    def get_html2docx(self):
        """Get html2docx function."""
        if not self._load_with_lock('html2docx', lambda: __import__('html2docx').html2docx):
            return None
        return self._html2docx
    
    # --- pytesseract ---
    def get_pytesseract(self):
        """Get pytesseract module."""
        if not self._load_with_lock('pytesseract', lambda: __import__('pytesseract')):
            return None
        return self._pytesseract
    
    # --- mammoth ---
    def get_mammoth(self):
        """Get mammoth module."""
        if not self._load_with_lock('mammoth', lambda: __import__('mammoth')):
            return None
        return self._mammoth
    
    # --- weasyprint ---
    def get_weasyprint(self):
        """Get weasyprint.HTML class."""
        if not self._load_with_lock('weasyprint', lambda: __import__('weasyprint').HTML):
            return None
        return self._weasyprint
    
    # --- Availability checks ---
    def is_available(self, name: str) -> bool:
        """Check if library is available (triggers load)."""
        return self._load_with_lock(name, lambda: True) is not None
    
    def get_status(self) -> dict:
        """Get status of all libraries."""
        # Trigger all loads with actual loaders
        def _load_pillow():
            import PIL.Image
            return PIL.Image
        
        loaders = {
            'fitz': lambda: __import__('fitz'),
            'pillow': _load_pillow,
            'docx': lambda: __import__('docx').Document,
            'pdf2image': lambda: __import__('pdf2image').convert_from_path,
            'bs4': lambda: __import__('bs4').BeautifulSoup,
            'html2docx': lambda: __import__('html2docx').html2docx,
            'pytesseract': lambda: __import__('pytesseract'),
            'mammoth': lambda: __import__('mammoth'),
            'weasyprint': lambda: __import__('weasyprint').HTML,
        }
        for name in self._load_locks:
            loader = loaders.get(name, lambda: True)
            self._load_with_lock(name, loader)
        return {k: v is not None for k, v in self._available.items()}


# Global instance
library_manager = LibraryManager()


def get_libraries() -> LibraryManager:
    """Get the global library manager instance."""
    return library_manager