"""HTML format handler."""

import os
import tempfile
from typing import Optional
from .base import BaseHandler
from ..core import ConversionOptions
from ..libraries import get_libraries


class HTMLHandler(BaseHandler):
    """Handler for HTML files."""
    
    def __init__(self):
        self._libs = get_libraries()
    
    def _get_fitz(self):
        return self._libs.get_fitz()
    
    def _get_docx(self):
        return self._libs.get_docx()
    
    def _get_pillow(self):
        return self._libs.get_pillow()
    
    def _get_pdf2image(self):
        return self._libs.get_pdf2image()
    
    def _get_html2docx(self):
        return self._libs.get_html2docx()
    
    def _get_bs4(self):
        return self._libs.get_bs4()
    
    def convert(
        self,
        input_path: str,
        output_path: str,
        output_format: str,
        options: ConversionOptions
    ) -> Optional[str]:
        """Convert HTML to target format."""
        output_format = output_format.lower()
        
        if output_format == 'pdf':
            return self._html_to_pdf(input_path, output_path, options)
        elif output_format == 'docx':
            return self._html_to_docx(input_path, output_path, options)
        elif output_format == 'txt':
            return self._html_to_text(input_path, output_path, options)
        elif output_format in ('png', 'jpeg', 'jpg', 'tiff', 'bmp', 'webp'):
            return self._html_to_images(input_path, output_path, output_format, options)
        
        return None
    
    def _html_to_pdf(self, input_path: str, output_path: str, options: ConversionOptions) -> Optional[str]:
        """Convert HTML to PDF using wkhtmltopdf or fallback."""
        # Try wkhtmltopdf (no GTK dependency)
        import subprocess
        try:
            result = subprocess.run([
                'wkhtmltopdf', input_path, output_path
            ], capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                return output_path
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Fallback: extract text and create simple PDF
        return self._html_to_pdf_fallback(input_path, output_path, options)
    
    def _html_to_pdf_fallback(self, input_path: str, output_path: str, options: ConversionOptions) -> Optional[str]:
        """Fallback: extract text from HTML and create PDF."""
        fitz = self._get_fitz()
        if not fitz:
            raise RuntimeError("PyMuPDF (fitz) required for fallback")
        
        text = self._extract_text_from_html(input_path)
        return self._text_to_pdf(text, output_path, options)
    
    def _html_to_docx(self, input_path: str, output_path: str, options: ConversionOptions) -> Optional[str]:
        """Convert HTML to DOCX using html2docx or fallback."""
        html2docx = self._get_html2docx()
        
        # Try html2docx (API: html2docx(html_content: str, title: str) -> BytesIO)
        if html2docx:
            try:
                with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
                    html_content = f.read()
                title = os.path.splitext(os.path.basename(input_path))[0]
                buffer = html2docx(html_content, title)
                with open(output_path, 'wb') as f:
                    f.write(buffer.getvalue())
                return output_path
            except Exception:
                # html2docx may fail on complex HTML
                pass
        
        # Fallback: extract text and create DOCX
        text = self._extract_text_from_html(input_path)
        docx_cls = self._get_docx()
        if docx_cls:
            doc = docx_cls()
            for para in text.split('\n\n'):
                if para.strip():
                    doc.add_paragraph(para.strip())
            doc.save(output_path)
            return output_path
        
        raise RuntimeError("No HTML to DOCX conversion method available (install html2docx)")
    
    def _html_to_text(self, input_path: str, output_path: str, options: ConversionOptions) -> Optional[str]:
        """Extract text from HTML."""
        text = self._extract_text_from_html(input_path)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        return output_path
    
    def _html_to_images(
        self,
        input_path: str,
        output_path: str,
        output_format: str,
        options: ConversionOptions
    ) -> Optional[str]:
        """Convert HTML to images via PDF."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            pdf_path = tmp.name
        
        try:
            pdf_result = self._html_to_pdf(input_path, pdf_path, options)
            if not pdf_result:
                return None
            
            from .pdf_handler import PDFHandler
            pdf_handler = PDFHandler()
            return pdf_handler.convert(pdf_path, output_path, output_format, options)
        finally:
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)
    
    def _extract_text_from_html(self, input_path: str) -> str:
        """Extract plain text from HTML file."""
        bs4 = self._get_bs4()
        if not bs4:
            # Fallback to simple text extraction
            with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            # Very basic tag removal
            import re
            content = re.sub(r'<[^>]+>', '', content)
            return content
        
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        soup = bs4(content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up whitespace
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n\n'.join(lines)
    
    def _text_to_pdf(self, text: str, output_path: str, options: ConversionOptions) -> Optional[str]:
        """Convert text to PDF using fitz."""
        fitz = self._get_fitz()
        if not fitz:
            raise RuntimeError("PyMuPDF (fitz) not installed")
        
        doc = fitz.open()
        chars_per_page = 3000
        pages = [text[i:i+chars_per_page] for i in range(0, len(text), chars_per_page)]
        
        for page_text in pages:
            page = doc.new_page()
            page.insert_text((72, 72), page_text, fontsize=11)
        
        doc.save(output_path, garbage=3, deflate=True)
        doc.close()
        return output_path