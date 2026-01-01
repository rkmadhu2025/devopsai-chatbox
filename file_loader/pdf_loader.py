"""
PDF Loader - Extract text and metadata from PDF files.
Supports multiple PDF libraries with fallback options.
"""
import io
import logging
from typing import Optional, Dict, Any, Tuple, List

logger = logging.getLogger(__name__)

# Try to import PDF libraries
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    try:
        from PyPDF2 import PdfReader
        PYPDF_AVAILABLE = True
    except ImportError:
        PYPDF_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


class PDFLoader:
    """
    PDF text and metadata extractor.
    Uses PyMuPDF (fitz) as primary, with pypdf and pdfplumber as fallbacks.
    """

    def __init__(self, prefer_library: Optional[str] = None):
        """
        Initialize PDF loader.

        Args:
            prefer_library: Preferred library ('pymupdf', 'pypdf', 'pdfplumber')
        """
        self.available_libraries = []
        if PYMUPDF_AVAILABLE:
            self.available_libraries.append('pymupdf')
        if PYPDF_AVAILABLE:
            self.available_libraries.append('pypdf')
        if PDFPLUMBER_AVAILABLE:
            self.available_libraries.append('pdfplumber')

        if not self.available_libraries:
            logger.warning("No PDF libraries available. Install: pip install pymupdf pypdf pdfplumber")

        self.prefer_library = prefer_library

    def extract_text(
        self,
        file_content: bytes,
        extract_images: bool = False
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Extract text from PDF content.

        Args:
            file_content: PDF file bytes
            extract_images: Whether to attempt image extraction (OCR)

        Returns:
            Tuple of (extracted_text, metadata)
        """
        metadata = {
            "library_used": None,
            "page_count": 0,
            "has_images": False,
            "extraction_errors": []
        }

        if not self.available_libraries:
            return None, {"error": "No PDF library available"}

        # Determine library order
        lib_order = self.available_libraries.copy()
        if self.prefer_library and self.prefer_library in lib_order:
            lib_order.remove(self.prefer_library)
            lib_order.insert(0, self.prefer_library)

        # Try each library
        for lib in lib_order:
            try:
                if lib == 'pymupdf':
                    text, meta = self._extract_with_pymupdf(file_content, extract_images)
                elif lib == 'pypdf':
                    text, meta = self._extract_with_pypdf(file_content)
                elif lib == 'pdfplumber':
                    text, meta = self._extract_with_pdfplumber(file_content)
                else:
                    continue

                if text:
                    metadata.update(meta)
                    metadata["library_used"] = lib
                    return text, metadata

            except Exception as e:
                logger.warning(f"PDF extraction with {lib} failed: {e}")
                metadata["extraction_errors"].append(f"{lib}: {str(e)}")

        return None, metadata

    def _extract_with_pymupdf(
        self,
        file_content: bytes,
        extract_images: bool = False
    ) -> Tuple[str, Dict[str, Any]]:
        """Extract using PyMuPDF (fitz)."""
        doc = fitz.open(stream=file_content, filetype="pdf")

        metadata = {
            "page_count": len(doc),
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
            "subject": doc.metadata.get("subject", ""),
            "creator": doc.metadata.get("creator", ""),
            "creation_date": doc.metadata.get("creationDate", ""),
            "has_images": False,
            "word_count": 0
        }

        text_parts = []
        for page_num, page in enumerate(doc):
            # Extract text
            page_text = page.get_text("text")
            if page_text.strip():
                text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}")

            # Check for images
            image_list = page.get_images(full=True)
            if image_list:
                metadata["has_images"] = True
                if extract_images:
                    # Could add OCR processing here
                    pass

        doc.close()

        full_text = "\n\n".join(text_parts)
        metadata["word_count"] = len(full_text.split())
        metadata["char_count"] = len(full_text)

        return full_text, metadata

    def _extract_with_pypdf(self, file_content: bytes) -> Tuple[str, Dict[str, Any]]:
        """Extract using pypdf/PyPDF2."""
        reader = PdfReader(io.BytesIO(file_content))

        metadata = {
            "page_count": len(reader.pages),
            "title": "",
            "author": "",
            "has_images": False,
            "word_count": 0
        }

        # Extract metadata
        if reader.metadata:
            metadata["title"] = reader.metadata.get("/Title", "") or ""
            metadata["author"] = reader.metadata.get("/Author", "") or ""

        text_parts = []
        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}")

            # Check for images
            if "/XObject" in page.get("/Resources", {}):
                metadata["has_images"] = True

        full_text = "\n\n".join(text_parts)
        metadata["word_count"] = len(full_text.split())
        metadata["char_count"] = len(full_text)

        return full_text, metadata

    def _extract_with_pdfplumber(self, file_content: bytes) -> Tuple[str, Dict[str, Any]]:
        """Extract using pdfplumber."""
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            metadata = {
                "page_count": len(pdf.pages),
                "title": pdf.metadata.get("Title", "") if pdf.metadata else "",
                "author": pdf.metadata.get("Author", "") if pdf.metadata else "",
                "has_images": False,
                "has_tables": False,
                "word_count": 0
            }

            text_parts = []
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    text_parts.append(f"--- Page {page_num + 1} ---\n{page_text}")

                # Check for images and tables
                if page.images:
                    metadata["has_images"] = True
                if page.extract_tables():
                    metadata["has_tables"] = True

            full_text = "\n\n".join(text_parts)
            metadata["word_count"] = len(full_text.split())
            metadata["char_count"] = len(full_text)

            return full_text, metadata

    def extract_tables(self, file_content: bytes) -> List[List[List[str]]]:
        """
        Extract tables from PDF.

        Returns:
            List of tables, each table is a list of rows
        """
        if not PDFPLUMBER_AVAILABLE:
            logger.warning("pdfplumber required for table extraction")
            return []

        tables = []
        try:
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                for page in pdf.pages:
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)
        except Exception as e:
            logger.error(f"Table extraction failed: {e}")

        return tables

    def get_page_count(self, file_content: bytes) -> int:
        """Get page count without full extraction."""
        try:
            if PYMUPDF_AVAILABLE:
                doc = fitz.open(stream=file_content, filetype="pdf")
                count = len(doc)
                doc.close()
                return count
            elif PYPDF_AVAILABLE:
                reader = PdfReader(io.BytesIO(file_content))
                return len(reader.pages)
        except Exception as e:
            logger.error(f"Could not get page count: {e}")
        return 0

    def is_available(self) -> bool:
        """Check if any PDF library is available."""
        return len(self.available_libraries) > 0

    def get_available_libraries(self) -> List[str]:
        """Get list of available PDF libraries."""
        return self.available_libraries.copy()
