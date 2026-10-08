"""Image format handler."""

import os
import io
from typing import Optional
from .base import BaseHandler
from ..core import ConversionOptions
from ..libraries import get_libraries


class ImageHandler(BaseHandler):
    """Handler for image files (PNG, JPEG, TIFF, BMP, WEBP, GIF)."""
    
    def __init__(self):
        self._libs = get_libraries()
    
    def _get_pillow(self):
        return self._libs.get_pillow()
    
    def _get_fitz(self):
        return self._libs.get_fitz()
    
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
        """Convert image to target format."""
        pillow = self._get_pillow()
        if not pillow:
            raise RuntimeError("Pillow not installed")
        
        output_format = output_format.lower()
        
        # Open input image
        try:
            img = pillow.open(input_path)
        except Exception as e:
            raise RuntimeError(f"Failed to open image: {e}")
        
        # Handle multi-page images (TIFF, GIF)
        if hasattr(img, 'n_frames') and img.n_frames > 1:
            return self._convert_multipage_image(img, input_path, output_path, output_format, options)
        
        # Apply options
        img = self._apply_image_options(img, options)
        
        if output_format in ('png', 'jpeg', 'jpg', 'tiff', 'bmp', 'webp'):
            return self._convert_image_to_image(img, output_path, output_format, options)
        elif output_format == 'pdf':
            return self._convert_image_to_pdf(img, output_path, options)
        elif output_format == 'docx':
            return self._convert_image_to_docx(img, output_path, options)
        elif output_format == 'txt':
            return self._convert_image_to_text(img, output_path, options)
        
        return None
    
    def _convert_multipage_image(
        self,
        img,
        input_path: str,
        output_path: str,
        output_format: str,
        options: ConversionOptions
    ) -> Optional[str]:
        """Handle multi-page images (TIFF, GIF)."""
        fitz = self._get_fitz()
        
        if output_format == 'pdf':
            return self._multipage_to_pdf(img, output_path, options)
        elif output_format == 'tiff':
            # Save all frames as multi-page TIFF
            frames = []
            for i in range(img.n_frames):
                img.seek(i)
                frame = img.copy()
                frame = self._apply_image_options(frame, options)
                frames.append(frame)
            
            try:
                frames[0].save(
                    output_path,
                    format='TIFF',
                    save_all=True,
                    append_images=frames[1:],
                    compression='tiff_lzw'
                )
            finally:
                for frame in frames:
                    try:
                        frame.close()
                    except Exception:
                        pass
            return output_path
        elif output_format in ('png', 'jpeg', 'jpg', 'bmp', 'webp'):
            # Save first frame only
            img.seek(0)
            frame = img.copy()
            frame = self._apply_image_options(frame, options)
            self._save_image(frame, output_path, output_format, options)
            return output_path
        
        return None
    
    def _multipage_to_pdf(self, img, output_path: str, options: ConversionOptions) -> Optional[str]:
        """Convert multi-page image to PDF."""
        fitz = self._get_fitz()
        if not fitz:
            raise RuntimeError("PyMuPDF (fitz) required for multi-page PDF")
        
        pdf_doc = fitz.open()
        
        try:
            for i in range(img.n_frames):
                img.seek(i)
                frame = img.copy()
                frame = self._apply_image_options(frame, options)
                
                page = pdf_doc.new_page(width=frame.width, height=frame.height)
                # Save frame to bytes buffer with explicit format
                buf = io.BytesIO()
                frame.save(buf, format='PNG')
                page.insert_image(page.rect, stream=buf.getvalue())
                frame.close()
        finally:
            pdf_doc.save(output_path, garbage=3, deflate=True)
            pdf_doc.close()
        
        return output_path
    
    def _convert_image_to_image(
        self,
        img,
        output_path: str,
        output_format: str,
        options: ConversionOptions
    ) -> Optional[str]:
        """Convert image to another image format."""
        # Handle palette mode (e.g., GIF) for JPEG output
        if output_format in ('jpeg', 'jpg') and img.mode == 'P':
            img = img.convert('RGB')
        self._save_image(img, output_path, output_format, options)
        return output_path
    
    def _convert_image_to_pdf(self, img, output_path: str, options: ConversionOptions) -> Optional[str]:
        """Convert single image to PDF."""
        fitz = self._get_fitz()
        if not fitz:
            raise RuntimeError("PyMuPDF (fitz) required for PDF output")
        
        pdf_doc = fitz.open()
        page = pdf_doc.new_page(width=img.width, height=img.height)
        # Save image to bytes buffer with explicit format
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        page.insert_image(page.rect, stream=buf.getvalue())
        pdf_doc.save(output_path, garbage=3, deflate=True)
        pdf_doc.close()
        return output_path
    
    def _convert_image_to_docx(self, img, output_path: str, options: ConversionOptions) -> Optional[str]:
        """Convert image to DOCX."""
        docx_cls = self._get_docx()
        if not docx_cls:
            raise RuntimeError("python-docx required for DOCX output")
        
        doc = docx_cls()
        # Save image to temp file first
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name
            img.save(tmp_path, format='PNG')
        
        try:
            inches = self._get_docx_shared()
            if inches:
                doc.add_picture(tmp_path, width=inches(6))
            else:
                doc.add_picture(tmp_path)
            doc.save(output_path)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        
        return output_path
    
    def _convert_image_to_text(self, img, output_path: str, options: ConversionOptions) -> Optional[str]:
        """Extract text from image using OCR."""
        pytesseract = self._libs.get_pytesseract()
        try:
            if pytesseract:
                text = pytesseract.image_to_string(img, lang='rus+eng')
            else:
                text = "[OCR requires pytesseract and tesseract-ocr installed]"
        except Exception as e:
            text = f"[OCR error: {e}]"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        return output_path