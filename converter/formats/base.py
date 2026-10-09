"""Base handler for document formats."""

import io
from abc import ABC, abstractmethod
from typing import Optional
from ..core import ConversionOptions
from ..libraries import get_libraries


class BaseHandler(ABC):
    """Base class for format handlers."""
    
    def __init__(self):
        self._libs = get_libraries()
    
    def _get_pillow(self):
        return self._libs.get_pillow()
    
    def _get_fitz(self):
        return self._libs.get_fitz()
    
    @abstractmethod
    def convert(
        self,
        input_path: str,
        output_path: str,
        output_format: str,
        options: ConversionOptions
    ) -> Optional[str]:
        """
        Convert input file to output format.
        
        Args:
            input_path: Path to input file
            output_path: Desired output path
            output_format: Target format
            options: Conversion options
            
        Returns:
            Path to output file if successful, None otherwise
        """
        pass
    
    def _apply_image_options(self, image, options: ConversionOptions):
        """Apply common image options (resize, grayscale, etc.)."""
        pillow = self._get_pillow()
        if not pillow:
            raise RuntimeError("Pillow not installed")
        
        # Resize
        if options.resize_factor != 1.0:
            new_size = (
                int(image.width * options.resize_factor),
                int(image.height * options.resize_factor)
            )
            # Access Resampling from PIL.Image
            from PIL import Image as PILImage
            image = image.resize(new_size, PILImage.Resampling.LANCZOS)
        
        # Grayscale
        if options.grayscale and image.mode != 'L':
            image = image.convert('L')
        
        return image
    
    def _save_image(self, image, output_path: str, format: str, options: ConversionOptions):
        """Save image with appropriate options."""
        pillow = self._get_pillow()
        if not pillow:
            raise RuntimeError("Pillow not installed")
        
        format = format.upper()
        if format == 'JPG':
            format = 'JPEG'
        
        save_kwargs = {}
        
        if format == 'JPEG':
            save_kwargs['quality'] = options.quality
            save_kwargs['optimize'] = True
            if options.strip_metadata:
                save_kwargs['exif'] = b''
        elif format == 'PNG':
            save_kwargs['optimize'] = True
            save_kwargs['compress_level'] = 9 if options.quality > 90 else 6
        elif format == 'WEBP':
            save_kwargs['quality'] = options.quality
            save_kwargs['method'] = 6
        elif format == 'TIFF':
            save_kwargs['compression'] = 'tiff_lzw'
        
        image.save(output_path, format=format, **save_kwargs)