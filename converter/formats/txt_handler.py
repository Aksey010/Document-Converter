"""TXT format handler."""

import os
import html
from typing import Optional
from .base import BaseHandler
from ..core import ConversionOptions
from ..libraries import get_libraries


class TXTHandler(BaseHandler):
    """Handler for plain text files."""
    
    def __init__(self):
        self._libs = get_libraries()
    
    def _get_fitz(self):
        return self._libs.get_fitz()
    
    def _get_docx(self):
        return self._libs.get_docx()
    
    def _get_pillow(self):
        return self._libs.get_pillow()
    
    def convert(
        self,
        input_path: str,
        output_path: str,
        output_format: str,
        options: ConversionOptions
    ) -> Optional[str]:
        """Convert TXT to target format."""
        output_format = output_format.lower()
        
        # Read input text
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        
        if output_format == 'pdf':
            return self._text_to_pdf(text, output_path, options)
        elif output_format == 'docx':
            return self._text_to_docx(text, output_path, options)
        elif output_format == 'html':
            return self._text_to_html(text, output_path, options)
        elif output_format in ('png', 'jpeg', 'jpg', 'tiff', 'bmp', 'webp'):
            return self._text_to_image(text, output_path, output_format, options)
        
        return None
    
    def _text_to_pdf(self, text: str, output_path: str, options: ConversionOptions) -> Optional[str]:
        """Convert text to PDF."""
        fitz = self._get_fitz()
        if not fitz:
            raise RuntimeError("PyMuPDF (fitz) not installed")
        
        doc = fitz.open()
        
        # Split text into pages (roughly 3000 chars per page)
        chars_per_page = 3000
        pages = [text[i:i+chars_per_page] for i in range(0, len(text), chars_per_page)]
        
        # Handle empty text - create at least one page
        if not pages or not any(p.strip() for p in pages):
            pages = ['']
        
        for page_text in pages:
            page = doc.new_page()
            if page_text.strip():
                page.insert_text((72, 72), page_text, fontsize=11)
        
        doc.save(output_path, garbage=3, deflate=True)
        doc.close()
        return output_path
    
    def _text_to_docx(self, text: str, output_path: str, options: ConversionOptions) -> Optional[str]:
        """Convert text to DOCX."""
        docx_cls = self._get_docx()
        if not docx_cls:
            raise RuntimeError("python-docx not installed")
        
        doc = docx_cls()
        
        # Split by double newlines for paragraphs
        paragraphs = text.split('\n\n')
        for para in paragraphs:
            if para.strip():
                doc.add_paragraph(para.strip())
        
        doc.save(output_path)
        return output_path
    
    def _text_to_html(self, text: str, output_path: str, options: ConversionOptions) -> Optional[str]:
        """Convert text to HTML."""
        # Escape HTML
        escaped = html.escape(text)
        # Convert newlines to <br> and paragraphs
        paragraphs = escaped.split('\n\n')
        html_paragraphs = [f'<p>{p.replace(chr(10), "<br>")}</p>' for p in paragraphs if p.strip()]
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Converted Text</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 2cm; line-height: 1.6; }}
        p {{ margin: 0.5em 0; }}
    </style>
</head>
<body>
{''.join(html_paragraphs)}
</body>
</html>"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
    
    def _text_to_image(
        self,
        text: str,
        output_path: str,
        output_format: str,
        options: ConversionOptions
    ) -> Optional[str]:
        """Convert text to image."""
        pillow = self._get_pillow()
        if not pillow:
            raise RuntimeError("Pillow not installed")
        
        # Create image with text
        # Estimate size needed
        lines = text.split('\n')
        line_height = 20
        padding = 40
        width = 800
        height = max(len(lines) * line_height + padding * 2, 400)
        
        img = pillow.new('RGB', (width, height), color='white')
        
        # Try to get ImageDraw and ImageFont
        try:
            ImageDraw = __import__('PIL.ImageDraw', fromlist=['ImageDraw']).ImageDraw
            ImageFont = __import__('PIL.ImageFont', fromlist=['ImageFont']).ImageFont
        except ImportError:
            raise RuntimeError("PIL.ImageDraw or PIL.ImageFont not available")
        
        draw = ImageDraw.Draw(img)
        
        # Try to use a nice font
        font = None
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except Exception:
            try:
                font = ImageFont.load_default()
            except Exception:
                pass
        
        y = padding
        for line in lines:
            if y > height - line_height:
                break
            draw.text((padding, y), line, fill='black', font=font)
            y += line_height
        
        # Apply options
        img = self._apply_image_options(img, options)
        self._save_image(img, output_path, output_format, options)
        
        return output_path