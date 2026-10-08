"""Format handlers package."""

from .base import BaseHandler
from .pdf_handler import PDFHandler
from .docx_handler import DOCXHandler
from .txt_handler import TXTHandler
from .html_handler import HTMLHandler
from .image_handler import ImageHandler
from .djvu_handler import DJVUHandler

__all__ = [
    "BaseHandler",
    "PDFHandler",
    "DOCXHandler",
    "TXTHandler",
    "HTMLHandler",
    "ImageHandler",
    "DJVUHandler",
]