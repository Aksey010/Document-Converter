"""Tests for format handlers."""

import pytest
import tempfile
from pathlib import Path
import json

from PIL import Image

from converter import ConversionOptions, ConversionResult
from converter.formats.pdf_handler import PDFHandler
from converter.formats.docx_handler import DOCXHandler
from converter.formats.txt_handler import TXTHandler
from converter.formats.html_handler import HTMLHandler
from converter.formats.image_handler import ImageHandler
from converter.formats.djvu_handler import DJVUHandler
from converter.formats.base import BaseHandler


class TestPDFHandler:
    """Tests for PDFHandler."""

    def test_pdf_to_pdf_compression(self, pdf_handler, sample_text_pdf, test_dir):
        """Test PDF to PDF with compression."""
        output_path = test_dir / "compressed.pdf"
        options = ConversionOptions(pdf_compression="high")
        
        result = pdf_handler.convert(
            str(sample_text_pdf), str(output_path), 'pdf', 
            options
        )
        
        assert result == str(output_path)
        assert Path(result).exists()

    def test_pdf_to_text(self, pdf_handler, sample_text_pdf, test_dir):
        """Test PDF to text extraction."""
        output_path = test_dir / "output.txt"
        
        result = pdf_handler.convert(
            str(sample_text_pdf), str(output_path), 'txt', 
            ConversionOptions()
        )
        
        assert result == str(output_path)
        assert Path(result).exists()
        content = Path(result).read_text(encoding='utf-8')
        assert "Test PDF" in content
        assert "extraction" in content

    def test_pdf_to_text_empty(self, pdf_handler, empty_pdf, test_dir):
        """Test PDF to text with empty PDF."""
        output_path = test_dir / "empty_output.txt"
        
        with pytest.raises(RuntimeError, match="No text could be extracted|empty"):
            pdf_handler.convert(
                str(empty_pdf), str(test_dir / "output.txt"), 'txt', 
                ConversionOptions()
            )

    def test_pdf_to_text_scanned(self, pdf_handler, scanned_pdf, test_dir):
        """Test PDF to text with scanned PDF."""
        with pytest.raises(RuntimeError, match="scanned|image-based|OCR"):
            pdf_handler.convert(
                str(scanned_pdf), str(test_dir / "output.txt"), 'txt', 
                ConversionOptions()
            )

    def test_pdf_to_html(self, pdf_handler, sample_text_pdf, test_dir):
        """Test PDF to HTML conversion."""
        output_path = test_dir / "output.html"
        
        result = pdf_handler.convert(
            str(sample_text_pdf), str(output_path), 'html', 
            ConversionOptions()
        )
        
        assert result == str(output_path)
        assert Path(result).exists()
        content = Path(result).read_text(encoding='utf-8')
        assert "<html>" in content
        assert "Test PDF" in content

    def test_pdf_to_docx(self, pdf_handler, sample_text_pdf, test_dir):
        """Test PDF to DOCX conversion."""
        output_path = test_dir / "output.docx"
        
        result = pdf_handler.convert(
            str(sample_text_pdf), str(output_path), 'docx', 
            ConversionOptions()
        )
        
        assert result == str(output_path)
        assert Path(result).exists()

    def test_pdf_to_images(self, pdf_handler, sample_text_pdf, test_dir):
        """Test PDF to various image formats."""
        for fmt in ['png', 'jpeg', 'tiff', 'bmp', 'webp']:
            output_path = test_dir / f"output.{fmt}"
            result = pdf_handler.convert(
                str(sample_text_pdf), str(output_path), fmt, 
                ConversionOptions(dpi=150)
            )
            assert Path(result).exists(), f"Failed for {fmt}"

    def test_pdf_to_images_multi_page(self, pdf_handler, test_dir):
        """Test multi-page PDF to TIFF."""
        # Create multi-page PDF
        import fitz
        pdf_path = Path(tempfile.mkdtemp()) / "multipage.pdf"
        doc = fitz.open()
        for i in range(3):
            page = doc.new_page()
            page.insert_text((100, 100), f"Page {i+1}")
        doc.save(pdf_path)
        doc.close()
        
        output_path = test_dir / "multipage.tiff"
        result = pdf_handler.convert(
            str(pdf_path), str(output_path), 'tiff', 
            ConversionOptions()
        )
        assert Path(result).exists()

    def test_page_range(self, pdf_handler, sample_text_pdf, test_dir):
        """Test page range option."""
        output_path = test_dir / "page_range.txt"
        options = ConversionOptions(page_range="1-1")
        
        result = pdf_handler.convert(
            str(sample_text_pdf), str(output_path), 'txt', 
            options
        )
        assert Path(result).exists()


class TestDOCXHandler:
    """Tests for DOCXHandler."""

    def test_docx_to_pdf(self, docx_handler, sample_docx, test_dir):
        """Test DOCX to PDF conversion."""
        output_path = test_dir / "output.pdf"
        
        result = docx_handler.convert(
            str(sample_docx), str(output_path), 'pdf', 
            ConversionOptions()
        )
        
        assert result == str(output_path)
        assert Path(result).exists()

    def test_docx_to_txt(self, docx_handler, sample_docx, test_dir):
        """Test DOCX to text extraction."""
        output_path = test_dir / "output.txt"
        
        result = docx_handler.convert(
            str(sample_docx), str(output_path), 'txt', 
            ConversionOptions()
        )
        
        assert result == str(output_path)
        assert Path(result).exists()
        content = Path(result).read_text(encoding='utf-8')
        assert "Test Document" in content
        assert "test paragraph" in content.lower()

    def test_docx_to_html(self, docx_handler, sample_docx, test_dir):
        """Test DOCX to HTML conversion."""
        output_path = test_dir / "output.html"
        
        result = docx_handler.convert(
            str(sample_docx), str(output_path), 'html', 
            ConversionOptions()
        )
        
        assert result == str(output_path)
        assert Path(result).exists()
        content = Path(result).read_text(encoding='utf-8')
        assert "<html>" in content
        assert "Test Document" in content

    def test_docx_to_images(self, docx_handler, sample_docx, test_dir):
        """Test DOCX to image conversion."""
        for fmt in ['png', 'jpeg']:
            output_path = test_dir / f"output.{fmt}"
            result = docx_handler.convert(
                str(sample_docx), str(output_path), fmt, 
                ConversionOptions(dpi=150)
            )
            assert Path(result).exists(), f"Failed for {fmt}"


class TestTXTHandler:
    """Tests for TXTHandler."""

    def test_txt_to_pdf(self, txt_handler, sample_txt, test_dir):
        """Test TXT to PDF conversion."""
        output_path = test_dir / "output.pdf"
        
        result = txt_handler.convert(
            str(sample_txt), str(output_path), 'pdf', 
            ConversionOptions()
        )
        
        assert result == str(output_path)
        assert Path(result).exists()

    def test_txt_to_docx(self, txt_handler, sample_txt, test_dir):
        """Test TXT to DOCX conversion."""
        output_path = test_dir / "output.docx"
        
        result = txt_handler.convert(
            str(sample_txt), str(output_path), 'docx', 
            ConversionOptions()
        )
        
        assert result == str(output_path)
        assert Path(result).exists()

    def test_txt_to_html(self, txt_handler, sample_txt, test_dir):
        """Test TXT to HTML conversion."""
        output_path = test_dir / "output.html"
        
        result = txt_handler.convert(
            str(sample_txt), str(output_path), 'html', 
            ConversionOptions()
        )
        
        assert result == str(output_path)
        assert Path(result).exists()
        content = Path(result).read_text(encoding='utf-8')
        assert "<html>" in content
        assert "Test TXT" in content

    def test_txt_to_images(self, txt_handler, sample_txt, test_dir):
        """Test TXT to image conversion."""
        for fmt in ['png', 'jpeg']:
            output_path = test_dir / f"output.{fmt}"
            result = txt_handler.convert(
                str(sample_txt), str(output_path), fmt, 
                ConversionOptions()
            )
            assert Path(result).exists(), f"Failed for {fmt}"

    def test_empty_txt(self, txt_handler, test_dir):
        """Test empty text file."""
        empty_txt = Path(tempfile.mkdtemp()) / "empty.txt"
        empty_txt.write_text("")
        
        output_path = test_dir / "output.pdf"
        result = txt_handler.convert(
            str(empty_txt), str(output_path), 'pdf', 
            ConversionOptions()
        )
        assert Path(result).exists()


class TestHTMLHandler:
    """Tests for HTMLHandler."""

    def test_html_to_pdf(self, html_handler, sample_html, test_dir):
        """Test HTML to PDF conversion."""
        output_path = test_dir / "output.pdf"
        
        result = html_handler.convert(
            str(sample_html), str(output_path), 'pdf', 
            ConversionOptions()
        )
        
        assert result == str(output_path)
        assert Path(result).exists()

    def test_html_to_docx(self, html_handler, sample_html, test_dir):
        """Test HTML to DOCX conversion."""
        output_path = test_dir / "output.docx"
        
        result = html_handler.convert(
            str(sample_html), str(output_path), 'docx', 
            ConversionOptions()
        )
        
        assert result == str(output_path)
        assert Path(result).exists()

    def test_html_to_txt(self, html_handler, sample_html, test_dir):
        """Test HTML to text extraction."""
        output_path = test_dir / "output.txt"
        
        result = html_handler.convert(
            str(sample_html), str(output_path), 'txt', 
            ConversionOptions()
        )
        
        assert result == str(output_path)
        assert Path(result).exists()
        content = Path(result).read_text(encoding='utf-8')
        assert "Test HTML" in content

    def test_html_to_images(self, html_handler, sample_html, test_dir):
        """Test HTML to image conversion."""
        for fmt in ['png', 'jpeg']:
            output_path = test_dir / f"output.{fmt}"
            result = html_handler.convert(
                str(sample_html), str(output_path), fmt, 
                ConversionOptions(dpi=150)
            )
            assert Path(result).exists(), f"Failed for {fmt}"


class TestImageHandler:
    """Tests for ImageHandler."""

    def test_image_to_pdf(self, image_handler, sample_image, test_dir):
        """Test image to PDF conversion."""
        output_path = test_dir / "output.pdf"
        
        result = image_handler.convert(
            str(sample_image), str(output_path), 'pdf', 
            ConversionOptions()
        )
        
        assert result == str(output_path)
        assert Path(result).exists()

    def test_image_to_docx(self, image_handler, sample_image, test_dir):
        """Test image to DOCX conversion."""
        output_path = test_dir / "output.docx"
        
        result = image_handler.convert(
            str(sample_image), str(output_path), 'docx', 
            ConversionOptions()
        )
        
        assert result == str(output_path)
        assert Path(result).exists()

    def test_image_to_image(self, image_handler, sample_image, test_dir):
        """Test image to image conversion."""
        for fmt in ['png', 'jpeg', 'webp', 'tiff', 'bmp']:
            output_path = test_dir / f"output.{fmt}"
            result = image_handler.convert(
                str(sample_image), str(output_path), fmt, 
                ConversionOptions(quality=85)
            )
            assert Path(result).exists(), f"Failed for {fmt}"

    def test_gif_to_jpeg(self, image_handler, test_dir):
        """Test GIF to JPEG conversion (palette mode)."""
        gif_path = Path(tempfile.mkdtemp()) / "test.gif"
        img = Image.new('P', (100, 100), color=1)
        img.save(gif_path, 'GIF')
        
        output_path = test_dir / "output.jpeg"
        result = image_handler.convert(
            str(gif_path), str(output_path), 'jpeg', 
            ConversionOptions()
        )
        assert Path(result).exists()

    def test_image_options_grayscale(self, image_handler, sample_image, test_dir):
        """Test grayscale option."""
        output_path = test_dir / "gray.png"
        options = ConversionOptions(grayscale=True)
        
        result = image_handler.convert(
            str(sample_image), str(output_path), 'png', 
            options
        )
        assert Path(result).exists()

    def test_image_options_resize(self, image_handler, sample_image, test_dir):
        """Test resize option."""
        output_path = test_dir / "resized.png"
        options = ConversionOptions(resize_factor=0.5)
        
        result = image_handler.convert(
            str(sample_image), str(output_path), 'png', 
            options
        )
        assert Path(result).exists()

    def test_image_options_quality(self, image_handler, sample_image, test_dir):
        """Test quality option."""
        for quality in [10, 50, 95]:
            output_path = test_dir / f"q{quality}.jpg"
            options = ConversionOptions(quality=quality)
            
            result = image_handler.convert(
                str(sample_image), str(output_path), 'jpeg', 
                options
            )
            assert Path(result).exists()


class TestDJVUHandler:
    """Tests for DJVUHandler (will be skipped if ddjvu not available)."""

    @pytest.fixture(autouse=True)
    def _check_ddjvu(self):
        """Skip tests if ddjvu not available."""
        import subprocess
        try:
            subprocess.run(['ddjvu', '--version'], capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            pytest.skip("ddjvu not available")

    def test_djvu_to_pdf(self, djvu_handler, test_dir):
        """Test DJVU to PDF conversion."""
        pytest.skip("Requires DJVU test file")

    def test_djvu_to_images(self, djvu_handler, test_dir):
        """Test DJVU to image conversion."""
        pytest.skip("Requires DJVU test file")


class TestBaseHandler:
    """Tests for BaseHandler base class."""

    def test_apply_image_options_resize(self, image_handler, sample_image):
        """Test _apply_image_options resize."""
        options = ConversionOptions(resize_factor=0.5)
        img = image_handler._get_pillow().open(sample_image)
        result = image_handler._apply_image_options(img, options)
        
        assert result.width == img.width // 2
        assert result.height == img.height // 2

    def test_apply_image_options_grayscale(self, image_handler, sample_image):
        """Test _apply_image_options grayscale."""
        options = ConversionOptions(grayscale=True)
        img = image_handler._get_pillow().open(sample_image)
        result = image_handler._apply_image_options(img, options)
        
        assert result.mode == 'L'

    def test_save_image_options(self, image_handler, sample_image, test_dir):
        """Test _save_image with various options."""
        img = image_handler._get_pillow().open(sample_image)
        
        # Test JPEG options
        output_path = test_dir / "test.jpg"
        image_handler._save_image(
            image_handler._get_pillow().open(sample_image),
            str(test_dir / "test.jpg"), 'jpeg', 
            ConversionOptions(quality=90, strip_metadata=True)
        )
        assert Path(test_dir / "test.jpg").exists()

        # Test PNG options
        image_handler._save_image(
            image_handler._get_pillow().open(sample_image),
            str(test_dir / "test.png"), 'png', 
            ConversionOptions(quality=90)
        )
        assert Path(test_dir / "test.png").exists()

        # Test WEBP options
        image_handler._save_image(
            image_handler._get_pillow().open(sample_image),
            str(test_dir / "test.webp"), 'webp', 
            ConversionOptions(quality=80)
        )
        assert Path(test_dir / "test.webp").exists()


class TestHandlerAvailability:
    """Test handler availability checks."""

    def test_pdf_handler_available(self, pdf_handler):
        assert pdf_handler._get_fitz() is not None

    def test_docx_handler_available(self, docx_handler):
        assert docx_handler._get_docx() is not None

    def test_image_handler_available(self, image_handler):
        assert image_handler._get_pillow() is not None

    def test_library_manager(self, library_manager):
        status = library_manager.get_status()
        assert 'fitz' in status
        assert 'pillow' in status
        assert 'docx' in status
        assert status['fitz'] is True
        assert status['pillow'] is True
        assert status['docx'] is True


# Import tempfile at module level
import tempfile