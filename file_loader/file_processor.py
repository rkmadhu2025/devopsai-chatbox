"""
File Processor - Main orchestrator for file loading and processing.
Handles PDF, text, image files and coordinates with the database.
"""
import os
import hashlib
import logging
import uuid
import mimetypes
from typing import Optional, Dict, Any, List, Tuple, BinaryIO
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# File type mappings
MIME_TYPE_MAP = {
    # PDF
    'application/pdf': 'pdf',
    # Text files
    'text/plain': 'text',
    'text/markdown': 'text',
    'text/csv': 'text',
    'text/html': 'text',
    'text/xml': 'text',
    'application/json': 'text',
    'application/xml': 'text',
    'text/x-python': 'text',
    'text/x-java': 'text',
    'application/javascript': 'text',
    'text/css': 'text',
    'text/yaml': 'text',
    # Images
    'image/jpeg': 'image',
    'image/png': 'image',
    'image/gif': 'image',
    'image/webp': 'image',
    'image/bmp': 'image',
    'image/tiff': 'image',
    'image/svg+xml': 'image',
}

# Extension to type mapping
EXTENSION_MAP = {
    '.pdf': 'pdf',
    '.txt': 'text',
    '.md': 'text',
    '.csv': 'text',
    '.json': 'text',
    '.xml': 'text',
    '.html': 'text',
    '.htm': 'text',
    '.py': 'text',
    '.js': 'text',
    '.ts': 'text',
    '.java': 'text',
    '.cpp': 'text',
    '.c': 'text',
    '.h': 'text',
    '.css': 'text',
    '.yaml': 'text',
    '.yml': 'text',
    '.log': 'text',
    '.ini': 'text',
    '.conf': 'text',
    '.sh': 'text',
    '.bat': 'text',
    '.sql': 'text',
    '.jpg': 'image',
    '.jpeg': 'image',
    '.png': 'image',
    '.gif': 'image',
    '.webp': 'image',
    '.bmp': 'image',
    '.tiff': 'image',
    '.tif': 'image',
    '.svg': 'image',
}


class FileProcessor:
    """
    Main file processor that handles all file types.
    Coordinates between specific loaders and the database.
    """

    def __init__(
        self,
        upload_dir: Optional[str] = None,
        db_manager=None,
        max_file_size: int = 50 * 1024 * 1024  # 50MB default
    ):
        """
        Initialize the file processor.

        Args:
            upload_dir: Directory to store uploaded files
            db_manager: DatabaseManager instance for persistence
            max_file_size: Maximum allowed file size in bytes
        """
        self.upload_dir = upload_dir or self._get_default_upload_dir()
        self.max_file_size = max_file_size
        self.db_manager = db_manager

        # Ensure upload directory exists
        os.makedirs(self.upload_dir, exist_ok=True)

        # Initialize specific loaders lazily
        self._pdf_loader = None
        self._text_loader = None
        self._image_loader = None

        # Initialize file repository if db available
        self._file_repo = None
        if db_manager:
            from database import FileRepository
            self._file_repo = FileRepository(db_manager)

    def _get_default_upload_dir(self) -> str:
        """Get default upload directory."""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        return os.path.join(base_dir, "uploads")

    @property
    def pdf_loader(self):
        """Lazy load PDF loader."""
        if self._pdf_loader is None:
            from .pdf_loader import PDFLoader
            self._pdf_loader = PDFLoader()
        return self._pdf_loader

    @property
    def text_loader(self):
        """Lazy load text loader."""
        if self._text_loader is None:
            from .text_loader import TextLoader
            self._text_loader = TextLoader()
        return self._text_loader

    @property
    def image_loader(self):
        """Lazy load image loader."""
        if self._image_loader is None:
            from .image_loader import ImageLoader
            self._image_loader = ImageLoader()
        return self._image_loader

    def get_file_type(
        self,
        filename: str,
        mime_type: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Determine file type from filename and/or MIME type.

        Args:
            filename: Name of the file
            mime_type: Optional MIME type

        Returns:
            Tuple of (file_type, mime_type)
        """
        # Try MIME type first
        if mime_type and mime_type in MIME_TYPE_MAP:
            return MIME_TYPE_MAP[mime_type], mime_type

        # Try extension
        ext = os.path.splitext(filename.lower())[1]
        if ext in EXTENSION_MAP:
            file_type = EXTENSION_MAP[ext]
            guessed_mime = mimetypes.guess_type(filename)[0] or f"application/{ext[1:]}"
            return file_type, guessed_mime

        # Guess MIME type
        guessed_mime, _ = mimetypes.guess_type(filename)
        if guessed_mime and guessed_mime in MIME_TYPE_MAP:
            return MIME_TYPE_MAP[guessed_mime], guessed_mime

        # Default to unknown
        return "unknown", guessed_mime or "application/octet-stream"

    def calculate_hash(self, file_content: bytes) -> str:
        """Calculate SHA256 hash of file content."""
        return hashlib.sha256(file_content).hexdigest()

    def generate_filename(self, original_filename: str) -> str:
        """Generate a unique filename for storage."""
        ext = os.path.splitext(original_filename)[1]
        unique_id = uuid.uuid4().hex[:12]
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}_{unique_id}{ext}"

    async def process_file(
        self,
        file_content: bytes,
        original_filename: str,
        mime_type: Optional[str] = None,
        session_id: Optional[str] = None,
        uploaded_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process an uploaded file.

        Args:
            file_content: Raw file bytes
            original_filename: Original filename
            mime_type: Optional MIME type
            session_id: Associated session ID
            uploaded_by: User identifier
            metadata: Additional metadata

        Returns:
            Processing result dictionary
        """
        result = {
            "success": False,
            "original_filename": original_filename,
            "file_id": None,
            "file_type": None,
            "extracted_text": None,
            "metadata": {},
            "error": None
        }

        try:
            # Validate file size
            file_size = len(file_content)
            if file_size > self.max_file_size:
                result["error"] = f"File size ({file_size} bytes) exceeds maximum ({self.max_file_size} bytes)"
                return result

            # Determine file type
            file_type, detected_mime = self.get_file_type(original_filename, mime_type)
            result["file_type"] = file_type
            result["metadata"]["mime_type"] = detected_mime
            result["metadata"]["file_size"] = file_size

            # Calculate hash for deduplication
            file_hash = self.calculate_hash(file_content)
            result["metadata"]["file_hash"] = file_hash

            # Check for duplicates if database available
            if self._file_repo:
                existing = self._file_repo.get_file_by_hash(file_hash)
                if existing and existing.get("processing_status") == "completed":
                    logger.info(f"Found duplicate file: {file_hash}")
                    result["success"] = True
                    result["file_id"] = existing["id"]
                    result["extracted_text"] = existing.get("extracted_text")
                    result["metadata"]["is_duplicate"] = True
                    return result

            # Generate unique filename and save
            new_filename = self.generate_filename(original_filename)
            file_path = os.path.join(self.upload_dir, new_filename)

            with open(file_path, 'wb') as f:
                f.write(file_content)

            result["metadata"]["stored_path"] = file_path
            result["metadata"]["stored_filename"] = new_filename

            # Save to database if available
            file_id = None
            if self._file_repo:
                file_id = self._file_repo.save_file_record(
                    filename=new_filename,
                    original_filename=original_filename,
                    file_path=file_path,
                    file_type=file_type,
                    file_size=file_size,
                    mime_type=detected_mime,
                    file_hash=file_hash,
                    session_id=session_id,
                    uploaded_by=uploaded_by,
                    metadata=metadata
                )
                result["file_id"] = file_id

            # Process based on file type
            extracted_text = None
            processing_metadata = {}

            if file_type == "pdf":
                extracted_text, processing_metadata = await self._process_pdf(file_content)
            elif file_type == "text":
                extracted_text, processing_metadata = await self._process_text(file_content, original_filename)
            elif file_type == "image":
                extracted_text, processing_metadata = await self._process_image(file_content, original_filename)
            else:
                result["error"] = f"Unsupported file type: {file_type}"
                if file_id:
                    self._file_repo.update_processing_status(
                        file_id, "failed", error_message=result["error"]
                    )
                return result

            result["extracted_text"] = extracted_text
            result["metadata"].update(processing_metadata)

            # Update database with extracted text
            if file_id and self._file_repo:
                self._file_repo.update_processing_status(
                    file_id,
                    "completed",
                    extracted_text=extracted_text,
                    metadata_update=processing_metadata
                )

            result["success"] = True
            logger.info(f"Successfully processed file: {original_filename} -> {new_filename}")

        except Exception as e:
            logger.error(f"Failed to process file {original_filename}: {e}")
            result["error"] = str(e)
            if result.get("file_id") and self._file_repo:
                self._file_repo.update_processing_status(
                    result["file_id"], "failed", error_message=str(e)
                )

        return result

    async def _process_pdf(self, file_content: bytes) -> Tuple[Optional[str], Dict[str, Any]]:
        """Process PDF file and extract text."""
        try:
            text, metadata = self.pdf_loader.extract_text(file_content)
            return text, metadata
        except Exception as e:
            logger.error(f"PDF processing error: {e}")
            return None, {"error": str(e)}

    async def _process_text(
        self,
        file_content: bytes,
        filename: str
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """Process text file."""
        try:
            text, metadata = self.text_loader.extract_text(file_content, filename)
            return text, metadata
        except Exception as e:
            logger.error(f"Text processing error: {e}")
            return None, {"error": str(e)}

    async def _process_image(
        self,
        file_content: bytes,
        filename: str
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """Process image file and extract text via OCR if available."""
        try:
            text, metadata = self.image_loader.extract_text(file_content, filename)
            return text, metadata
        except Exception as e:
            logger.error(f"Image processing error: {e}")
            return None, {"error": str(e)}

    def process_file_sync(
        self,
        file_content: bytes,
        original_filename: str,
        mime_type: Optional[str] = None,
        session_id: Optional[str] = None,
        uploaded_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Synchronous version of process_file for non-async contexts."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            self.process_file(
                file_content, original_filename, mime_type,
                session_id, uploaded_by, metadata
            )
        )

    def get_file_content(self, file_id: int) -> Optional[Dict[str, Any]]:
        """
        Get file content and metadata by ID.

        Returns:
            Dictionary with file info and extracted text
        """
        if not self._file_repo:
            logger.error("Database not configured")
            return None

        file_record = self._file_repo.get_file_by_id(file_id)
        if not file_record:
            return None

        result = {
            "id": file_record["id"],
            "filename": file_record["original_filename"],
            "file_type": file_record["file_type"],
            "extracted_text": file_record.get("extracted_text"),
            "status": file_record["processing_status"],
            "metadata": file_record.get("metadata", {})
        }

        return result

    def get_session_files(
        self,
        session_id: str,
        file_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all files for a session."""
        if not self._file_repo:
            return []
        return self._file_repo.get_session_files(session_id, file_type)

    def search_files(
        self,
        query: str,
        file_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search files by content."""
        if not self._file_repo:
            return []
        return self._file_repo.search_files(query, file_type, limit)

    def get_context_for_chat(
        self,
        session_id: str,
        max_files: int = 5,
        max_chars_per_file: int = 5000
    ) -> str:
        """
        Get file context formatted for chat.

        Args:
            session_id: Session identifier
            max_files: Maximum number of files to include
            max_chars_per_file: Maximum characters per file

        Returns:
            Formatted context string
        """
        if not self._file_repo:
            return ""

        files = self._file_repo.get_session_files(session_id, status="completed")[:max_files]

        if not files:
            return ""

        context_parts = ["## Uploaded Files Context\n"]

        for file_record in files:
            file_data = self._file_repo.get_file_by_id(file_record["id"])
            if file_data and file_data.get("extracted_text"):
                text = file_data["extracted_text"][:max_chars_per_file]
                if len(file_data["extracted_text"]) > max_chars_per_file:
                    text += "\n... [truncated]"

                context_parts.append(f"### File: {file_record['original_filename']}")
                context_parts.append(f"Type: {file_record['file_type']}")
                context_parts.append(f"```\n{text}\n```\n")

        return "\n".join(context_parts)

    def delete_file(self, file_id: int, delete_physical: bool = True) -> bool:
        """Delete a file record and optionally the physical file."""
        if not self._file_repo:
            return False

        file_record = self._file_repo.get_file_by_id(file_id)
        if not file_record:
            return False

        # Delete physical file if requested
        if delete_physical and file_record.get("file_path"):
            try:
                if os.path.exists(file_record["file_path"]):
                    os.remove(file_record["file_path"])
            except Exception as e:
                logger.warning(f"Could not delete physical file: {e}")

        # Delete database record
        return self._file_repo.delete_file_record(file_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get file processing statistics."""
        if not self._file_repo:
            return {"error": "Database not configured"}
        return self._file_repo.get_file_stats()
