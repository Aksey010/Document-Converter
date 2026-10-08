"""PDF format handler."""

import os
import tempfile
from typing import Optional, List
from .base import BaseHandler
from ..core import ConversionOptions
from ..libraries import get_libraries


class PDFHandler(BaseHandler):
    """Handler for PDF files."""
    
    def __init__(self):
        self._libs = get_libraries()
    
    def _get_fitz(self):
        return self._libs.get_fitz()
    
    def _get_pdf2image(self):
        return self._libs.get_pdf2image()
    
    def _get_pillow(self):
        return self._libs.get_pillow()
    
    def _get_docx(self):
        return self._libs.get_docx()
    
    def _get_docx_shared(self):
        return self._libs.get_docx_shared()
    
    def convert(
        self,
        input_path: str,
        output_path: str,
        output_format: str,
        options: ConversionOptions
    ) -> Optional[str]:
        """Convert PDF to target format."""
        output_format = output_format.lower()
        
        if output_format == 'pdf':
            return self._convert_pdf_to_pdf(input_path, output_path, options)
        elif output_format in ('png', 'jpeg', 'jpg', 'tiff', 'bmp', 'webp'):
            return self._convert_pdf_to_images(input_path, output_path, output_format, options)
        elif output_format == 'txt':
            return self._convert_pdf_to_text(input_path, output_path, options)
        elif output_format == 'html':
            return self._convert_pdf_to_html(input_path, output_path, options)
        elif output_format == 'docx':
            return self._convert_pdf_to_docx(input_path, output_path, options)
        
        return None
    
    def _convert_pdf_to_pdf(self, input_path: str, output_path: str, options: ConversionOptions) -> Optional[str]:
        """Re-save PDF with compression."""
        fitz = self._get_fitz()
        if not fitz:
            raise RuntimeError("PyMuPDF (fitz) not installed")
        
        doc = fitz.open(input_path)
        
        # Apply compression
        if options.pdf_compression == "high":
            doc.save(output_path, garbage=4, deflate=True, clean=True)
        elif options.pdf_compression == "medium":
            doc.save(output_path, garbage=3, deflate=True, clean=True)
        else:  # low
            doc.save(output_path, garbage=1, deflate=True)
        
        doc.close()
        return output_path
    
    def _convert_pdf_to_images(
        self,
        input_path: str,
        output_path: str,
        output_format: str,
        options: ConversionOptions
    ) -> Optional[str]:
        """Convert PDF pages to images."""
        pdf2image = self._get_pdf2image()
        pillow = self._get_pillow()
        
        if not pdf2image or not pillow:
            raise RuntimeError("pdf2image and/or Pillow not installed")
        
        # Parse page range
        page_range = self._parse_page_range(options.page_range)
        
        # Convert PDF to images - process page by page to save memory
        images = pdf2image(
            input_path,
            dpi=options.dpi,
            first_page=page_range[0] if page_range else None,
            last_page=page_range[1] if page_range else None,
            fmt=output_format if output_format != 'jpg' else 'jpeg'
        )
        
        if not images:
            return None
        
        try:
            # If single page or output format doesn't support multi-page, save first page
            if len(images) == 1 or output_format in ('jpeg', 'jpg', 'png', 'bmp', 'webp'):
                img = images[0]
                img = self._apply_image_options(img, options)
                self._save_image(img, output_path, output_format, options)
            else:
                # For multi-page formats like TIFF, save all pages
                if output_format == 'tiff':
                    processed_images = [self._apply_image_options(img, options) for img in images]
                    processed_images[0].save(
                        output_path,
                        format='TIFF',
                        save_all=True,
                        append_images=processed_images[1:],
                        compression='tiff_lzw'
                    )
                else:
                    # Default: save first page
                    img = self._apply_image_options(images[0], options)
                    self._save_image(img, output_path, output_format, options)
        finally:
            # Explicitly close images to free memory
            for img in images:
                try:
                    img.close()
                except Exception:
                    pass
        
        return output_path
    
    def _convert_pdf_to_text(self, input_path: str, output_path: str, options: ConversionOptions) -> Optional[str]:
        """Extract text from PDF."""
        fitz = self._get_fitz()
        if not fitz:
            raise RuntimeError("PyMuPDF (fitz) not installed")
        
        doc = fitz.open(input_path)
        text_parts = []
        
        page_range = self._parse_page_range(options.page_range)
        start = page_range[0] - 1 if page_range else 0
        end = page_range[1] if page_range else len(doc)
        
        try:
            for i in range(start, min(end, len(doc))):
                page = doc[i]
                text = page.get_text()
                if text.strip():
                    text_parts.append(text)
        finally:
            doc.close()
        
        # Check if any text was extracted
        if not text_parts or not any(t.strip() for t in text_parts):
            # Check if PDF might be scanned/image-based
            has_images = False
            try:
                doc = fitz.open(input_path)
                for i in range(start, min(end, len(doc))):
                    page = doc[i]
                    images = page.get_images()
                    if images:
                        has_images = True
                        break
                doc.close()
            except Exception:
                pass
            
            if has_images:
                raise RuntimeError(
                    "PDF appears to be scanned or image-based with no extractable text. "
                    "Text extraction is not possible without OCR. "
                    "Consider converting to images first, then using OCR."
                )
            else:
                raise RuntimeError(
                    "No text could be extracted from the PDF. "
                    "The PDF may be empty, password-protected, or contain only vector graphics."
                )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(text_parts))
        
        return output_path
    
    def _convert_pdf_to_html(self, input_path: str, output_path: str, options: ConversionOptions) -> Optional[str]:
        """Convert PDF to HTML."""
        fitz = self._get_fitz()
        if not fitz:
            raise RuntimeError("PyMuPDF (fitz) not installed")
        
        doc = fitz.open(input_path)
        html_parts = []
        
        page_range = self._parse_page_range(options.page_range)
        start = page_range[0] - 1 if page_range else 0
        end = page_range[1] if page_range else len(doc)
        
        try:
            for i in range(start, min(end, len(doc))):
                page = doc[i]
                html_parts.append(page.get_text("html"))
        finally:
            doc.close()
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Converted PDF</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 2cm; }}
        .page {{ margin-bottom: 2cm; page-break-after: always; }}
    </style>
</head>
<body>
{''.join(f'<div class="page">{h}</div>' for h in html_parts)}
</body>
</html>"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
    
    def _convert_pdf_to_docx(self, input_path: str, output_path: str, options: ConversionOptions) -> Optional[str]:
        """Convert PDF to DOCX (basic text extraction)."""
        fitz = self._get_fitz()
        docx_cls = self._get_docx()
        
        if not fitz or not docx_cls:
            raise RuntimeError("PyMuPDF and/or python-docx not installed")
        
        doc = fitz.open(input_path)
        docx_doc = docx_cls()
        
        page_range = self._parse_page_range(options.page_range)
        start = page_range[0] - 1 if page_range else 0
        end = page_range[1] if page_range else len(doc)
        
        try:
            for i in range(start, min(end, len(doc))):
                page = doc[i]
                text = page.get_text()
                if text.strip():
                    docx_doc.add_paragraph(text)
                if i < min(end, len(doc)) - 1:
                    docx_doc.add_page_break()
        finally:
            doc.close()
        
        docx_doc.save(output_path)
        return output_path
    
    def _parse_page_range(self, page_range: Optional[str]) -> Optional[tuple]:
        """Parse page range string like '1-5' or '1,3,5'."""
        if not page_range:
            return None
        
        # Simple range parsing: "1-5" -> (1, 5)
        if '-' in page_range and ',' not in page_range:
            parts = page_range.split('-')
            try:
                return (int(parts[0]), int(parts[1]))
            except ValueError:
                return None
        
        # For complex ranges, just return None (process all)
        return None