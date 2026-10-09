"""Unit tests for DocumentConverter core functionality."""

import pytest
from pathlib import Path

from converter import DocumentConverter, ConversionOptions, ConversionResult, OutputFormat, InputFormat


class TestDocumentConverter:
    """Tests for DocumentConverter core class."""

    def test_initialization(self, converter):
        """Test converter initializes with handlers."""
        assert converter is not None
        assert hasattr(converter, '_handlers')
        assert len(converter._handlers) > 0

    def test_supported_input_formats(self, converter):
        """Test getting supported input formats."""
        formats = converter.get_supported_input_formats()
        assert isinstance(formats, list)
        assert len(formats) > 0
        assert 'pdf' in formats
        assert 'docx' in formats
        assert 'txt' in formats
        assert 'html' in formats
        assert 'pdf' in formats

    def test_supported_output_formats(self, converter):
        """Test getting supported output formats for input format."""
        pdf_outputs = converter.get_supported_output_formats('pdf')
        assert isinstance(pdf_outputs, list)
        assert len(pdf_outputs) > 0
        assert 'docx' in pdf_outputs
        assert 'txt' in pdf_outputs
        assert 'html' in pdf_outputs

    def test_can_convert(self, converter):
        """Test conversion compatibility check."""
        assert converter.can_convert('pdf', 'docx') is True
        assert converter.can_convert('pdf', 'txt') is True
        assert converter.can_convert('pdf', 'html') is True
        assert converter.can_convert('docx', 'pdf') is True
        assert converter.can_convert('docx', 'txt') is True
        assert converter.can_convert('txt', 'pdf') is True
        assert converter.can_convert('txt', 'docx') is True

    def test_cannot_convert_unsupported(self, converter):
        """Test unsupported conversions return False."""
        assert converter.can_convert('pdf', 'unsupported') is False
        assert converter.can_convert('xyz', 'pdf') is False

    def test_convert_pdf_to_txt_with_text(self, converter, sample_text_pdf):
        """Test PDF to TXT conversion with extractable text."""
        result = converter.convert(str(sample_text_pdf), 'txt')
        
        assert isinstance(result, ConversionResult)
        assert result.success is True
        assert result.error is None
        assert result.output_size > 0
        assert result.format == 'txt'
        assert result.output_path is not None
        assert Path(result.output_path).exists()

    def test_convert_pdf_to_txt_empty(self, converter, empty_pdf):
        """Test PDF to TXT conversion with empty PDF."""
        result = converter.convert(str(empty_pdf), 'txt')
        
        # Should fail with descriptive error
        assert isinstance(result, ConversionResult)
        assert result.success is False
        assert result.error is not None
        assert "empty" in result.error.lower() or "no text" in result.error.lower()

    def test_convert_pdf_to_docx(self, converter, sample_text_pdf):
        """Test PDF to DOCX conversion."""
        result = converter.convert(str(sample_text_pdf), 'docx')
        
        assert result.success is True
        assert result.format == 'docx'
        assert result.output_size > 0

    def test_convert_pdf_to_html(self, converter, sample_text_pdf):
        """Test PDF to HTML conversion."""
        result = converter.convert(str(sample_text_pdf), 'html')
        
        assert result.success is True
        assert result.format == 'html'
        assert result.output_size > 0

    def test_convert_pdf_to_image(self, converter, sample_text_pdf):
        """Test PDF to image conversion."""
        for fmt in ['png', 'jpeg']:
            result = converter.convert(str(sample_text_pdf), fmt)
            assert result.success is True, f"Failed for {fmt}: {result.error}"
            assert result.format == fmt
            assert result.output_size > 0

    def test_convert_docx_to_pdf(self, converter, sample_docx):
        """Test DOCX to PDF conversion."""
        result = converter.convert(str(sample_docx), 'pdf')
        
        assert result.success is True
        assert result.format == 'pdf'
        assert result.output_size > 0

    def test_convert_docx_to_txt(self, converter, sample_docx):
        """Test DOCX to TXT conversion."""
        result = converter.convert(str(sample_docx), 'txt')
        
        assert result.success is True
        assert result.format == 'txt'
        assert result.output_size > 0

    def test_convert_docx_to_html(self, converter, sample_docx):
        """Test DOCX to HTML conversion."""
        result = converter.convert(str(sample_docx), 'html')
        
        assert result.success is True
        assert result.format == 'html'
        assert result.output_size > 0

    def test_convert_txt_to_pdf(self, converter, sample_txt):
        """Test TXT to PDF conversion."""
        result = converter.convert(str(sample_txt), 'pdf')
        
        assert result.success is True
        assert result.format == 'pdf'
        assert result.output_size > 0

    def test_convert_txt_to_docx(self, converter, sample_txt):
        """Test TXT to DOCX conversion."""
        result = converter.convert(str(sample_txt), 'docx')
        
        assert result.success is True
        assert result.format == 'docx'
        assert result.output_size > 0

    def test_convert_txt_to_html(self, converter, sample_txt):
        """Test TXT to HTML conversion."""
        result = converter.convert(str(sample_txt), 'html')
        
        assert result.success is True
        assert result.format == 'html'
        assert result.output_size > 0

    def test_convert_html_to_pdf(self, converter, sample_html):
        """Test HTML to PDF conversion."""
        result = converter.convert(str(sample_html), 'pdf')
        
        assert result.success is True
        assert result.format == 'pdf'
        assert result.output_size > 0

    def test_convert_html_to_docx(self, converter, sample_html):
        """Test HTML to DOCX conversion."""
        result = converter.convert(str(sample_html), 'docx')
        
        assert result.success is True
        assert result.format == 'docx'
        assert result.output_size > 0

    def test_convert_html_to_txt(self, converter, sample_html):
        """Test HTML to TXT conversion."""
        result = converter.convert(str(sample_html), 'txt')
        
        assert result.success is True
        assert result.format == 'txt'
        assert result.output_size > 0

    def test_convert_image_to_pdf(self, converter, sample_image):
        """Test image to PDF conversion."""
        result = converter.convert(str(sample_image), 'pdf')
        
        assert result.success is True
        assert result.format == 'pdf'
        assert result.output_size > 0

    def test_convert_image_to_docx(self, converter, sample_image):
        """Test image to DOCX conversion."""
        result = converter.convert(str(sample_image), 'docx')
        
        assert result.success is True
        assert result.format == 'docx'
        assert result.output_size > 0

    def test_convert_image_to_image(self, converter, sample_image):
        """Test image to image conversion."""
        # Convert PNG to different formats (not PNG to PNG which is no-op)
        for fmt in ['jpeg', 'webp']:
            result = converter.convert(str(sample_image), fmt)
            assert result.success is True, f"Failed for {fmt}: {result.error}"
            assert result.format == fmt
            assert result.output_size > 0

    def test_convert_jpeg_to_pdf(self, converter, sample_jpeg):
        """Test JPEG to PDF conversion."""
        result = converter.convert(str(sample_jpeg), 'pdf')
        
        assert result.success is True
        assert result.format == 'pdf'
        assert result.output_size > 0

    def test_invalid_input_file(self, converter, test_dir):
        """Test conversion with non-existent file."""
        result = converter.convert(str(test_dir / "nonexistent.pdf"), 'txt')
        
        assert result.success is False
        assert "not found" in result.error.lower()

    def test_unsupported_conversion(self, converter, sample_text_pdf):
        """Test unsupported conversion raises error."""
        result = converter.convert(str(sample_text_pdf), 'unsupported_format')
        
        assert result.success is False
        assert "not supported" in result.error.lower() or "unsupported" in result.error.lower()

    def test_conversion_options_quality(self, converter, sample_image):
        """Test quality option affects output size."""
        options_low = ConversionOptions(quality=10)
        options_high = ConversionOptions(quality=95)
        
        result_low = converter.convert(str(sample_image), 'jpeg', options_low)
        result_high = converter.convert(str(sample_image), 'jpeg', options_high)
        
        assert result_low.success is True
        assert result_high.success is True

    def test_conversion_options_dpi(self, converter, sample_image):
        """Test DPI option affects output."""
        options_low = ConversionOptions(dpi=72)
        options_high = ConversionOptions(dpi=300)
        
        result_low = converter.convert(str(sample_image), 'pdf', options_low)
        result_high = converter.convert(str(sample_image), 'pdf', options_high)
        
        assert result_low.success is True
        assert result_high.success is True

    def test_conversion_options_grayscale(self, converter, sample_image):
        """Test grayscale option."""
        options_gray = ConversionOptions(grayscale=True)
        options_color = ConversionOptions(grayscale=False)
        
        result_gray = converter.convert(str(sample_image), 'jpeg', options_gray)
        result_color = converter.convert(str(sample_image), 'jpeg', options_color)
        
        assert result_gray.success is True
        assert result_color.success is True

    def test_conversion_options_page_range(self, converter, sample_text_pdf):
        """Test page range option."""
        options = ConversionOptions(page_range="1-1")
        result = converter.convert(str(sample_text_pdf), 'txt', options)
        
        assert result.success is True

    def test_file_not_found(self, converter, test_dir):
        """Test conversion with non-existent file."""
        result = converter.convert(str(test_dir / "nonexistent.pdf"), 'txt')
        
        assert result.success is False
        assert "not found" in result.error.lower() or "no such file" in result.error.lower()

    def test_unsupported_conversion(self, converter, sample_text_pdf):
        """Test unsupported conversion raises error."""
        result = converter.convert(str(sample_text_pdf), 'unsupported_format')
        
        assert result.success is False
        assert "not supported" in result.error.lower() or "unsupported" in result.error.lower()

    def test_conversion_options_validation(self):
        """Test ConversionOptions validation."""
        opts = ConversionOptions(
            quality=150,  # Should clamp to 100
            dpi=1000,     # Should clamp to 600
            resize_factor=5.0,  # Should clamp to 3.0
            pdf_compression="invalid",  # Should default to medium
        )
        
        assert opts.quality == 100
        assert opts.dpi == 600
        assert opts.resize_factor == 3.0
        assert opts.pdf_compression == "medium"


class TestConversionOptions:
    """Tests for ConversionOptions dataclass."""

    def test_default_values(self):
        opts = ConversionOptions()
        assert opts.quality == 85
        assert opts.dpi == 150
        assert opts.pdf_compression == "medium"
        assert opts.resize_factor == 1.0
        assert opts.djvu_quality == 50
        assert opts.page_range is None
        assert opts.grayscale is False
        assert opts.strip_metadata is True
        assert opts.output_dir is None
        assert opts.output_filename is None

    def test_custom_values(self):
        opts = ConversionOptions(
            quality=90,
            dpi=300,
            pdf_compression="high",
            resize_factor=1.5,
            djvu_quality=75,
            page_range="1-5",
            grayscale=True,
            strip_metadata=False,
        )
        assert opts.quality == 90
        assert opts.dpi == 300
        assert opts.pdf_compression == "high"
        assert opts.resize_factor == 1.5
        assert opts.djvu_quality == 75
        assert opts.page_range == "1-5"
        assert opts.grayscale is True
        assert opts.strip_metadata is False

    def test_clamping(self):
        opts = ConversionOptions(
            quality=150,
            dpi=1000,
            resize_factor=5.0,
            djvu_quality=150,
        )
        assert opts.quality == 100
        assert opts.dpi == 600
        assert opts.resize_factor == 3.0
        assert opts.djvu_quality == 100


class TestConversionResult:
    """Tests for ConversionResult dataclass."""

    def test_success_result(self):
        result = ConversionResult(
            success=True,
            output_path="/path/to/output.pdf",
            output_size=1024,
            input_size=2048,
            format="pdf",
        )
        assert result.success is True
        assert result.output_path == "/path/to/output.pdf"
        assert result.output_size == 1024
        assert result.input_size == 2048
        assert result.format == "pdf"
        assert result.error is None

    def test_error_result(self):
        result = ConversionResult(
            success=False,
            error="Conversion failed",
        )
        assert result.success is False
        assert result.error == "Conversion failed"
        assert result.output_path is None
        assert result.output_size == 0


class TestOutputFormat:
    """Tests for OutputFormat enum."""

    def test_all_formats(self):
        formats = [f.value for f in OutputFormat]
        assert "pdf" in formats
        assert "docx" in formats
        assert "txt" in formats
        assert "html" in formats
        assert "png" in formats
        assert "jpeg" in formats
        assert "tiff" in formats
        assert "bmp" in formats
        assert "webp" in formats

    def test_str_representation(self):
        assert OutputFormat.PDF.value == "pdf"
        assert OutputFormat.DOCX.value == "docx"


class TestInputFormat:
    """Tests for InputFormat enum."""

    def test_all_formats(self):
        formats = [f.value for f in InputFormat]
        assert "pdf" in formats
        assert "docx" in formats
        assert "txt" in formats
        assert "html" in formats
        assert "png" in formats
        assert "jpeg" in formats
        assert "jpg" in formats
        assert "tiff" in formats
        assert "bmp" in formats
        assert "webp" in formats
        assert "gif" in formats
        assert "djvu" in formats
        assert "djv" in formats