"""Core document conversion logic."""

import os
import tempfile
import shutil
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class OutputFormat(Enum):
    """Supported output formats."""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    HTML = "html"
    PNG = "png"
    JPEG = "jpeg"
    TIFF = "tiff"
    BMP = "bmp"
    WEBP = "webp"


class InputFormat(Enum):
    """Supported input formats."""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    HTML = "html"
    DJVU = "djvu"
    DJV = "djv"
    PNG = "png"
    JPEG = "jpeg"
    JPG = "jpg"
    TIFF = "tiff"
    BMP = "bmp"
    WEBP = "webp"
    GIF = "gif"


@dataclass
class ConversionOptions:
    """Options for controlling output file size and quality."""
    # Image quality (1-100 for JPEG/WebP, affects compression)
    quality: int = 85
    
    # DPI for rasterization (affects output size significantly)
    dpi: int = 150
    
    # For PDF output: compression level
    pdf_compression: str = "medium"  # low, medium, high
    
    # For image output: resize factor (0.1-2.0)
    resize_factor: float = 1.0
    
    # For DJVU: compression parameters
    djvu_quality: int = 50  # 0-100
    
    # Page range (for multi-page documents)
    page_range: Optional[str] = None  # e.g., "1-5" or "1,3,5"
    
    # Grayscale conversion (reduces size)
    grayscale: bool = False
    
    # Remove metadata
    strip_metadata: bool = True
    
    # Output directory (None = temp)
    output_dir: Optional[str] = None
    
    # Custom output filename (without extension)
    output_filename: Optional[str] = None

    def __post_init__(self):
        """Validate options."""
        self.quality = max(1, min(100, self.quality))
        self.dpi = max(72, min(600, self.dpi))
        self.resize_factor = max(0.1, min(3.0, self.resize_factor))
        self.djvu_quality = max(0, min(100, self.djvu_quality))
        if self.pdf_compression not in ("low", "medium", "high"):
            self.pdf_compression = "medium"


@dataclass
class ConversionResult:
    """Result of a conversion operation."""
    success: bool
    output_path: Optional[str] = None
    output_size: int = 0
    input_size: int = 0
    pages_processed: int = 0
    error: Optional[str] = None
    format: Optional[str] = None
    options_used: Optional[ConversionOptions] = None


class DocumentConverter:
    """Main document converter class."""
    
    SUPPORTED_INPUT_FORMATS = {fmt.value for fmt in InputFormat}
    SUPPORTED_OUTPUT_FORMATS = {fmt.value for fmt in OutputFormat}
    
    # Format compatibility matrix
    FORMAT_COMPATIBILITY = {
        InputFormat.PDF.value: [f.value for f in OutputFormat],
        InputFormat.DOCX.value: [OutputFormat.PDF.value, OutputFormat.TXT.value, OutputFormat.HTML.value, OutputFormat.PNG.value, OutputFormat.JPEG.value],
        InputFormat.TXT.value: [OutputFormat.PDF.value, OutputFormat.DOCX.value, OutputFormat.HTML.value],
        InputFormat.HTML.value: [OutputFormat.PDF.value, OutputFormat.DOCX.value, OutputFormat.TXT.value, OutputFormat.PNG.value, OutputFormat.JPEG.value],
        InputFormat.DJVU.value: [OutputFormat.PDF.value, OutputFormat.PNG.value, OutputFormat.JPEG.value, OutputFormat.TIFF.value, OutputFormat.TXT.value],
        InputFormat.DJV.value: [OutputFormat.PDF.value, OutputFormat.PNG.value, OutputFormat.JPEG.value, OutputFormat.TIFF.value, OutputFormat.TXT.value],
        InputFormat.PNG.value: [OutputFormat.PDF.value, OutputFormat.DOCX.value, OutputFormat.JPEG.value, OutputFormat.TIFF.value, OutputFormat.BMP.value, OutputFormat.WEBP.value],
        InputFormat.JPEG.value: [OutputFormat.PDF.value, OutputFormat.DOCX.value, OutputFormat.PNG.value, OutputFormat.TIFF.value, OutputFormat.BMP.value, OutputFormat.WEBP.value],
        InputFormat.JPG.value: [OutputFormat.PDF.value, OutputFormat.DOCX.value, OutputFormat.PNG.value, OutputFormat.TIFF.value, OutputFormat.BMP.value, OutputFormat.WEBP.value],
        InputFormat.TIFF.value: [OutputFormat.PDF.value, OutputFormat.PNG.value, OutputFormat.JPEG.value, OutputFormat.BMP.value, OutputFormat.WEBP.value],
        InputFormat.BMP.value: [OutputFormat.PDF.value, OutputFormat.PNG.value, OutputFormat.JPEG.value, OutputFormat.TIFF.value, OutputFormat.WEBP.value],
        InputFormat.WEBP.value: [OutputFormat.PDF.value, OutputFormat.PNG.value, OutputFormat.JPEG.value, OutputFormat.TIFF.value, OutputFormat.BMP.value],
        InputFormat.GIF.value: [OutputFormat.PDF.value, OutputFormat.PNG.value, OutputFormat.JPEG.value, OutputFormat.TIFF.value, OutputFormat.BMP.value, OutputFormat.WEBP.value],
    }

    def __init__(self):
        self._handlers = {}
        self._load_handlers()
    
    def _load_handlers(self):
        """Lazy load format handlers."""
        try:
            from .formats.pdf_handler import PDFHandler
            self._handlers[InputFormat.PDF.value] = PDFHandler()
        except ImportError:
            logger.warning("PDF handler not available")
        
        try:
            from .formats.docx_handler import DOCXHandler
            self._handlers[InputFormat.DOCX.value] = DOCXHandler()
        except ImportError:
            logger.warning("DOCX handler not available")
        
        try:
            from .formats.txt_handler import TXTHandler
            self._handlers[InputFormat.TXT.value] = TXTHandler()
        except ImportError:
            logger.warning("TXT handler not available")
        
        try:
            from .formats.html_handler import HTMLHandler
            self._handlers[InputFormat.HTML.value] = HTMLHandler()
        except ImportError:
            logger.warning("HTML handler not available")
        
        try:
            from .formats.djvu_handler import DJVUHandler
            self._handlers[InputFormat.DJVU.value] = DJVUHandler()
            self._handlers[InputFormat.DJV.value] = DJVUHandler()
        except ImportError:
            logger.warning("DJVU handler not available")
        
        try:
            from .formats.image_handler import ImageHandler
            for fmt in [InputFormat.PNG, InputFormat.JPEG, InputFormat.JPG, 
                       InputFormat.TIFF, InputFormat.BMP, InputFormat.WEBP, InputFormat.GIF]:
                self._handlers[fmt.value] = ImageHandler()
        except ImportError:
            logger.warning("Image handler not available")

    def get_supported_input_formats(self) -> List[str]:
        """Get list of supported input formats."""
        return sorted(list(self._handlers.keys()))

    def get_supported_output_formats(self, input_format: str) -> List[str]:
        """Get supported output formats for a given input format."""
        input_fmt = input_format.lower()
        if input_fmt in self.FORMAT_COMPATIBILITY:
            # Filter by available handlers
            available = []
            for fmt in self.FORMAT_COMPATIBILITY[input_fmt]:
                if self._can_output(fmt):
                    available.append(fmt)
            return available
        return []

    def _can_output(self, format: str) -> bool:
        """Check if we can output to a format."""
        # For now, assume all output formats are supported if we have the right libraries
        return True

    def can_convert(self, input_format: str, output_format: str) -> bool:
        """Check if conversion is supported."""
        input_fmt = input_format.lower()
        output_fmt = output_format.lower()
        
        if input_fmt not in self.FORMAT_COMPATIBILITY:
            return False
        return output_fmt in self.FORMAT_COMPATIBILITY[input_fmt]

    def convert(
        self,
        input_path: str,
        output_format: str,
        options: Optional[ConversionOptions] = None
    ) -> ConversionResult:
        """
        Convert a document to the specified format.
        
        Args:
            input_path: Path to input file
            output_format: Target format (pdf, docx, txt, html, png, jpeg, etc.)
            options: Conversion options for quality/size control
            
        Returns:
            ConversionResult with output path and metadata
        """
        input_path = Path(input_path)
        if not input_path.exists():
            return ConversionResult(
                success=False,
                error=f"Input file not found: {input_path}"
            )
        
        input_format = input_path.suffix.lower().lstrip('.')
        output_format = output_format.lower()
        
        if not self.can_convert(input_format, output_format):
            return ConversionResult(
                success=False,
                error=f"Conversion from {input_format} to {output_format} not supported"
            )
        
        if input_format not in self._handlers:
            return ConversionResult(
                success=False,
                error=f"No handler for input format: {input_format}"
            )
        
        options = options or ConversionOptions()
        handler = self._handlers[input_format]
        
        # Determine output path
        if options.output_dir:
            output_dir = Path(options.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            output_dir = Path(tempfile.gettempdir()) / "doc_converter"
            output_dir.mkdir(parents=True, exist_ok=True)
        
        if options.output_filename:
            output_filename = f"{options.output_filename}.{output_format}"
        else:
            output_filename = f"{input_path.stem}_converted.{output_format}"
        
        output_path = output_dir / output_filename
        
        try:
            input_size = input_path.stat().st_size
            result = handler.convert(
                input_path=str(input_path),
                output_path=str(output_path),
                output_format=output_format,
                options=options
            )
            
            if result and Path(result).exists():
                output_size = Path(result).stat().st_size
                return ConversionResult(
                    success=True,
                    output_path=str(result),
                    output_size=output_size,
                    input_size=input_size,
                    format=output_format,
                    options_used=options
                )
            else:
                return ConversionResult(
                    success=False,
                    error="Conversion produced no output file"
                )
                
        except Exception as e:
            logger.exception(f"Conversion failed: {e}")
            return ConversionResult(
                success=False,
                error=str(e)
            )

    def convert_batch(
        self,
        input_paths: List[str],
        output_format: str,
        options: Optional[ConversionOptions] = None
    ) -> List[ConversionResult]:
        """Convert multiple files."""
        results = []
        for path in input_paths:
            results.append(self.convert(path, output_format, options))
        return results

    def estimate_output_size(
        self,
        input_path: str,
        output_format: str,
        options: Optional[ConversionOptions] = None
    ) -> Dict[str, Any]:
        """Estimate output file size without converting."""
        input_path = Path(input_path)
        if not input_path.exists():
            return {"error": "File not found"}
        
        input_size = input_path.stat().st_size
        input_format = input_path.suffix.lower().lstrip('.')
        options = options or ConversionOptions()
        
        # Rough estimation based on format and options
        estimates = {
            "pdf": lambda: input_size * 0.8 * (options.dpi / 150) * (options.quality / 85),
            "docx": lambda: input_size * 1.2,
            "txt": lambda: input_size * 0.1,
            "html": lambda: input_size * 1.5,
            "png": lambda: input_size * 2.0 * (options.dpi / 150) ** 2 * (options.resize_factor ** 2),
            "jpeg": lambda: input_size * 0.3 * (options.dpi / 150) ** 2 * (options.quality / 85) * (options.resize_factor ** 2),
            "tiff": lambda: input_size * 1.5 * (options.dpi / 150) ** 2,
            "webp": lambda: input_size * 0.4 * (options.dpi / 150) ** 2 * (options.quality / 85),
        }
        
        estimator = estimates.get(output_format.lower(), lambda: input_size)
        estimated = int(estimator())
        
        return {
            "input_size": input_size,
            "estimated_output_size": estimated,
            "compression_ratio": round(estimated / input_size, 2) if input_size > 0 else 0,
            "options": {
                "quality": options.quality,
                "dpi": options.dpi,
                "resize_factor": options.resize_factor,
                "grayscale": options.grayscale,
            }
        }