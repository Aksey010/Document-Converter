"""DOCX format handler."""

import os
import tempfile
import subprocess
from typing import Optional
from .base import BaseHandler
from ..core import ConversionOptions
from ..libraries import get_libraries


class DOCXHandler(BaseHandler):
    """Handler for DOCX files."""
    
    def __init__(self):
        self._libs = get_libraries()
    
    def _get_docx(self):
        return self._libs.get_docx()
    
    def _get_docx_shared(self):
        return self._libs.get_docx_shared()
    
    def _get_pillow(self):
        return self._libs.get_pillow()
    
    def _get_fitz(self):
        return self._libs.get_fitz()
    
    def _get_pdf2image(self):
        return self._libs.get_pdf2image()
    
    def _get_mammoth(self):
        return self._libs.get_mammoth()
    
    def convert(
        self,
        input_path: str,
        output_path: str,
        output_format: str,
        options: ConversionOptions
    ) -> Optional[str]:
        """Convert DOCX to target format."""
        output_format = output_format.lower()
        
        if output_format == 'pdf':
            return self._convert_docx_to_pdf(input_path, output_path, options)
        elif output_format == 'txt':
            return self._convert_docx_to_text(input_path, output_path, options)
        elif output_format == 'html':
            return self._convert_docx_to_html(input_path, output_path, options)
        elif output_format in ('png', 'jpeg', 'jpg', 'tiff', 'bmp', 'webp'):
            return self._convert_docx_to_images(input_path, output_path, output_format, options)
        
        return None
    
    def _convert_docx_to_pdf(self, input_path: str, output_path: str, options: ConversionOptions) -> Optional[str]:
        """Convert DOCX to PDF using LibreOffice or python-docx2pdf."""
        # Try using docx2pdf first
        try:
            from docx2pdf import convert
            convert(input_path, output_path)
            return output_path
        except ImportError:
            pass
        
        # Try using LibreOffice headless
        try:
            result = subprocess.run([
                'libreoffice', '--headless', '--convert-to', 'pdf',
                '--outdir', os.path.dirname(output_path), input_path
            ], capture_output=True, text=True, timeout=120)
            if result.returncode == 0:
                # LibreOffice names output same as input but with .pdf
                expected = os.path.splitext(os.path.basename(input_path))[0] + '.pdf'
                expected_path = os.path.join(os.path.dirname(output_path), expected)
                if os.path.exists(expected_path) and expected_path != output_path:
                    os.rename(expected_path, output_path)
                return output_path
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Fallback: basic text extraction to PDF using fitz
        fitz = self._get_fitz()
        docx_cls = self._get_docx()
        if fitz and docx_cls:
            return self._docx_to_pdf_via_fitz(input_path, output_path, options)
        
        raise RuntimeError("No PDF conversion method available. Install docx2pdf or LibreOffice.")
    
    def _docx_to_pdf_via_fitz(self, input_path: str, output_path: str, options: ConversionOptions) -> Optional[str]:
        """Fallback: extract text and create simple PDF."""
        fitz = self._get_fitz()
        docx_cls = self._get_docx()
        if not fitz or not docx_cls:
            raise RuntimeError("PyMuPDF and python-docx required")
        
        doc = docx_cls(input_path)
        pdf_doc = fitz.open()
        
        try:
            for para in doc.paragraphs:
                if para.text.strip():
                    page = pdf_doc.new_page()
                    page.insert_text((72, 72), para.text, fontsize=11)
        finally:
            pdf_doc.save(output_path, garbage=3, deflate=True)
            pdf_doc.close()
        return output_path
    
    def _convert_docx_to_text(self, input_path: str, output_path: str, options: ConversionOptions) -> Optional[str]:
        """Extract text from DOCX."""
        docx_cls = self._get_docx()
        if not docx_cls:
            raise RuntimeError("python-docx not installed")
        
        doc = docx_cls(input_path)
        text_parts = []
        
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)
        
        # Also extract text from tables
        for table in doc.tables:
            for row in table.rows:
                row_text = ' | '.join(cell.text for cell in row.cells)
                if row_text.strip():
                    text_parts.append(row_text)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(text_parts))
        
        return output_path
    
    def _convert_docx_to_html(self, input_path: str, output_path: str, options: ConversionOptions) -> Optional[str]:
        """Convert DOCX to HTML."""
        mammoth = self._get_mammoth()
        
        if mammoth:
            try:
                with open(input_path, "rb") as docx_file:
                    result = mammoth.convert_to_html(docx_file)
                    html_content = result.value
                    
                    full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Converted DOCX</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 2cm; line-height: 1.6; }}
        table {{ border-collapse: collapse; width: 100%; margin: 1em 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
{html_content}
</body>
</html>"""
                    
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(full_html)
                    
                    return output_path
            except ImportError:
                pass
        
        # Fallback: basic HTML from text
        docx_cls = self._get_docx()
        if docx_cls:
            doc = docx_cls(input_path)
            text_parts = []
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(f'<p>{para.text}</p>')
            
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Converted DOCX</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 2cm; line-height: 1.6; }}
    </style>
</head>
<body>
{''.join(text_parts)}
</body>
</html>"""
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return output_path
        
        raise RuntimeError("No HTML conversion method available (install mammoth)")
    
    def _convert_docx_to_images(
        self,
        input_path: str,
        output_path: str,
        output_format: str,
        options: ConversionOptions
    ) -> Optional[str]:
        """Convert DOCX to images via PDF."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            pdf_path = tmp.name
        
        try:
            pdf_result = self._convert_docx_to_pdf(input_path, pdf_path, options)
            if not pdf_result:
                return None
            
            # Now use PDF handler to convert to images
            from .pdf_handler import PDFHandler
            pdf_handler = PDFHandler()
            return pdf_handler.convert(pdf_path, output_path, output_format, options)
        finally:
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)