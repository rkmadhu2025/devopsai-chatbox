"""
Image Loader - Process images and extract text via OCR.
Supports various image formats with optional OCR capabilities.
"""
import io
import os
import base64
import logging
from typing import Optional, Dict, Any, Tuple, List

logger = logging.getLogger(__name__)

# Try to import image processing libraries
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False


class ImageLoader:
    """
    Image processor with OCR capabilities.
    Extracts text from images using multiple OCR backends.
    """

    # Supported image formats
    SUPPORTED_FORMATS = {
        'JPEG', 'JPG', 'PNG', 'GIF', 'BMP', 'TIFF', 'TIF', 'WEBP'
    }

    def __init__(
        self,
        ocr_backend: str = "auto",
        languages: List[str] = None
    ):
        """
        Initialize image loader.

        Args:
            ocr_backend: OCR backend to use ('tesseract', 'easyocr', 'auto')
            languages: List of languages for OCR (e.g., ['en', 'ch_sim'])
        """
        self.languages = languages or ['en']
        self.ocr_backend = self._select_ocr_backend(ocr_backend)
        self._easyocr_reader = None

    def _select_ocr_backend(self, preferred: str) -> Optional[str]:
        """Select available OCR backend."""
        if preferred == "tesseract" and TESSERACT_AVAILABLE:
            return "tesseract"
        elif preferred == "easyocr" and EASYOCR_AVAILABLE:
            return "easyocr"
        elif preferred == "auto":
            if TESSERACT_AVAILABLE:
                return "tesseract"
            elif EASYOCR_AVAILABLE:
                return "easyocr"
        return None

    @property
    def easyocr_reader(self):
        """Lazy load EasyOCR reader."""
        if self._easyocr_reader is None and EASYOCR_AVAILABLE:
            self._easyocr_reader = easyocr.Reader(self.languages, gpu=False)
        return self._easyocr_reader

    def extract_text(
        self,
        file_content: bytes,
        filename: str
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Extract text from image using OCR.

        Args:
            file_content: Image file bytes
            filename: Original filename

        Returns:
            Tuple of (extracted_text, metadata)
        """
        metadata = {
            "format": None,
            "width": None,
            "height": None,
            "mode": None,
            "ocr_backend": self.ocr_backend,
            "ocr_available": self.ocr_backend is not None,
            "has_text": False
        }

        if not PIL_AVAILABLE:
            return None, {"error": "PIL/Pillow not installed. Run: pip install Pillow"}

        try:
            # Open and analyze image
            image = Image.open(io.BytesIO(file_content))

            metadata["format"] = image.format
            metadata["width"] = image.width
            metadata["height"] = image.height
            metadata["mode"] = image.mode
            metadata["size_bytes"] = len(file_content)

            # Check if format is supported
            if image.format and image.format.upper() not in self.SUPPORTED_FORMATS:
                return None, {"error": f"Unsupported format: {image.format}"}

            # Extract EXIF data if available
            exif_data = self._extract_exif(image)
            if exif_data:
                metadata["exif"] = exif_data

            # Perform OCR if available
            extracted_text = None
            if self.ocr_backend:
                extracted_text, ocr_meta = self._perform_ocr(image)
                metadata.update(ocr_meta)
                if extracted_text:
                    metadata["has_text"] = True
                    metadata["word_count"] = len(extracted_text.split())
                    metadata["char_count"] = len(extracted_text)

            # If no OCR, provide image description
            if not extracted_text:
                extracted_text = self._generate_description(image, filename, metadata)

            return extracted_text, metadata

        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            return None, {"error": str(e)}

    def _extract_exif(self, image: Image.Image) -> Optional[Dict[str, Any]]:
        """Extract EXIF metadata from image."""
        try:
            exif = image._getexif()
            if not exif:
                return None

            from PIL.ExifTags import TAGS

            exif_data = {}
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                if isinstance(value, bytes):
                    value = value.decode('utf-8', errors='ignore')
                # Only include safe, serializable values
                if isinstance(value, (str, int, float)):
                    exif_data[tag] = value

            return exif_data if exif_data else None
        except Exception:
            return None

    def _perform_ocr(self, image: Image.Image) -> Tuple[Optional[str], Dict[str, Any]]:
        """Perform OCR on image."""
        metadata = {"ocr_confidence": None}

        if self.ocr_backend == "tesseract":
            return self._ocr_tesseract(image, metadata)
        elif self.ocr_backend == "easyocr":
            return self._ocr_easyocr(image, metadata)

        return None, metadata

    def _ocr_tesseract(
        self,
        image: Image.Image,
        metadata: Dict[str, Any]
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """Perform OCR using Tesseract."""
        try:
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')

            # Perform OCR
            text = pytesseract.image_to_string(image)

            # Get detailed data for confidence
            try:
                data = pytesseract.image_to_data(
                    image, output_type=pytesseract.Output.DICT
                )
                confidences = [
                    int(c) for c in data['conf'] if c != '-1' and str(c).isdigit()
                ]
                if confidences:
                    metadata["ocr_confidence"] = sum(confidences) / len(confidences)
            except Exception:
                pass

            return text.strip() if text else None, metadata

        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")
            metadata["ocr_error"] = str(e)
            return None, metadata

    def _ocr_easyocr(
        self,
        image: Image.Image,
        metadata: Dict[str, Any]
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """Perform OCR using EasyOCR."""
        try:
            # Convert PIL image to numpy array
            import numpy as np
            img_array = np.array(image)

            # Convert RGB to BGR for EasyOCR
            if len(img_array.shape) == 3 and img_array.shape[2] == 3:
                img_array = img_array[:, :, ::-1]

            # Perform OCR
            results = self.easyocr_reader.readtext(img_array)

            if results:
                # Extract text and calculate average confidence
                texts = []
                confidences = []
                for (bbox, text, conf) in results:
                    texts.append(text)
                    confidences.append(conf)

                metadata["ocr_confidence"] = sum(confidences) / len(confidences) * 100
                return ' '.join(texts), metadata

            return None, metadata

        except Exception as e:
            logger.error(f"EasyOCR failed: {e}")
            metadata["ocr_error"] = str(e)
            return None, metadata

    def _generate_description(
        self,
        image: Image.Image,
        filename: str,
        metadata: Dict[str, Any]
    ) -> str:
        """Generate a text description of the image when OCR is unavailable."""
        desc_parts = [f"[Image: {filename}]"]
        desc_parts.append(f"Format: {metadata.get('format', 'Unknown')}")
        desc_parts.append(f"Dimensions: {metadata.get('width')}x{metadata.get('height')}")
        desc_parts.append(f"Color mode: {metadata.get('mode', 'Unknown')}")

        if metadata.get('exif'):
            desc_parts.append("Contains EXIF metadata")

        if not metadata.get('ocr_available'):
            desc_parts.append("Note: OCR not available. Install pytesseract or easyocr for text extraction.")

        return '\n'.join(desc_parts)

    def preprocess_for_ocr(self, image: Image.Image) -> Image.Image:
        """Preprocess image to improve OCR accuracy."""
        if not OPENCV_AVAILABLE:
            return image

        import numpy as np

        # Convert to numpy array
        img_array = np.array(image)

        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # Apply thresholding
        _, thresh = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh)

        return Image.fromarray(denoised)

    def resize_for_processing(
        self,
        image: Image.Image,
        max_dimension: int = 4000
    ) -> Image.Image:
        """Resize image if too large for processing."""
        if max(image.width, image.height) <= max_dimension:
            return image

        ratio = max_dimension / max(image.width, image.height)
        new_size = (int(image.width * ratio), int(image.height * ratio))

        return image.resize(new_size, Image.Resampling.LANCZOS)

    def get_image_base64(
        self,
        file_content: bytes,
        max_size: int = 1024
    ) -> Optional[str]:
        """
        Convert image to base64 for embedding in responses.

        Args:
            file_content: Image bytes
            max_size: Maximum dimension for resizing

        Returns:
            Base64 encoded string
        """
        if not PIL_AVAILABLE:
            return None

        try:
            image = Image.open(io.BytesIO(file_content))

            # Resize if needed
            if max(image.width, image.height) > max_size:
                image = self.resize_for_processing(image, max_size)

            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'RGBA':
                    background.paste(image, mask=image.split()[3])
                else:
                    background.paste(image)
                image = background

            # Save to buffer
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)

            return base64.b64encode(buffer.read()).decode('utf-8')

        except Exception as e:
            logger.error(f"Failed to convert image to base64: {e}")
            return None

    def extract_dominant_colors(
        self,
        file_content: bytes,
        num_colors: int = 5
    ) -> List[Tuple[int, int, int]]:
        """Extract dominant colors from image."""
        if not PIL_AVAILABLE:
            return []

        try:
            image = Image.open(io.BytesIO(file_content))

            # Resize for faster processing
            image = image.resize((100, 100))

            # Convert to RGB
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Get color counts
            colors = image.getcolors(10000)
            if not colors:
                return []

            # Sort by count and return top colors
            sorted_colors = sorted(colors, key=lambda x: x[0], reverse=True)
            return [color[1] for color in sorted_colors[:num_colors]]

        except Exception as e:
            logger.error(f"Failed to extract colors: {e}")
            return []

    def is_available(self) -> bool:
        """Check if image processing is available."""
        return PIL_AVAILABLE

    def is_ocr_available(self) -> bool:
        """Check if OCR is available."""
        return self.ocr_backend is not None

    def get_supported_formats(self) -> List[str]:
        """Get list of supported image formats."""
        return list(self.SUPPORTED_FORMATS)
