"""
File Repository - Handles all file-related database operations.
"""
import json
import logging
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime

from .db_manager import DatabaseManager, get_db_manager

logger = logging.getLogger(__name__)


class FileRepository:
    """Repository for managing file records in the database."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize file repository.

        Args:
            db_manager: DatabaseManager instance. If None, uses global instance.
        """
        self.db = db_manager or get_db_manager()

    def save_file_record(
        self,
        filename: str,
        original_filename: str,
        file_path: str,
        file_type: str,
        file_size: int,
        mime_type: Optional[str] = None,
        file_hash: Optional[str] = None,
        session_id: Optional[str] = None,
        uploaded_by: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """
        Save a file record to the database.

        Args:
            filename: Stored filename
            original_filename: Original uploaded filename
            file_path: Full path to the stored file
            file_type: Type of file (pdf, text, image, etc.)
            file_size: File size in bytes
            mime_type: MIME type of the file
            file_hash: SHA256 hash of the file
            session_id: Associated session ID
            uploaded_by: User who uploaded the file
            metadata: Additional metadata

        Returns:
            Inserted record ID or None on failure
        """
        query = """
            INSERT INTO file_loads
                (filename, original_filename, file_path, file_type, mime_type,
                 file_size, file_hash, session_id, uploaded_by, metadata,
                 processing_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        try:
            file_id = self.db.insert_returning(
                query,
                (
                    filename,
                    original_filename,
                    file_path,
                    file_type,
                    mime_type,
                    file_size,
                    file_hash,
                    session_id,
                    uploaded_by,
                    json.dumps(metadata or {}),
                    "pending"
                )
            )
            logger.info(f"Saved file record {file_id} for {original_filename}")
            return file_id
        except Exception as e:
            logger.error(f"Failed to save file record: {e}")
            return None

    def update_processing_status(
        self,
        file_id: int,
        status: str,
        extracted_text: Optional[str] = None,
        error_message: Optional[str] = None,
        metadata_update: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update the processing status of a file.

        Args:
            file_id: File record ID
            status: New status (pending, processing, completed, failed)
            extracted_text: Text extracted from the file
            error_message: Error message if processing failed
            metadata_update: Additional metadata to merge

        Returns:
            True if successful, False otherwise
        """
        if metadata_update:
            query = """
                UPDATE file_loads
                SET processing_status = %s,
                    extracted_text = %s,
                    error_message = %s,
                    metadata = metadata || %s,
                    processed_at = CASE WHEN %s IN ('completed', 'failed')
                                       THEN CURRENT_TIMESTAMP
                                       ELSE processed_at END
                WHERE id = %s
            """
            params = (
                status,
                extracted_text,
                error_message,
                json.dumps(metadata_update),
                status,
                file_id
            )
        else:
            query = """
                UPDATE file_loads
                SET processing_status = %s,
                    extracted_text = %s,
                    error_message = %s,
                    processed_at = CASE WHEN %s IN ('completed', 'failed')
                                       THEN CURRENT_TIMESTAMP
                                       ELSE processed_at END
                WHERE id = %s
            """
            params = (status, extracted_text, error_message, status, file_id)

        try:
            affected = self.db.execute(query, params)
            return affected > 0
        except Exception as e:
            logger.error(f"Failed to update processing status: {e}")
            return False

    def get_file_by_id(self, file_id: int) -> Optional[Dict[str, Any]]:
        """Get file record by ID."""
        query = """
            SELECT id, filename, original_filename, file_path, file_type,
                   mime_type, file_size, file_hash, processing_status,
                   extracted_text, metadata, session_id, uploaded_by,
                   created_at, processed_at, error_message
            FROM file_loads
            WHERE id = %s
        """
        try:
            result = self.db.fetch_one(query, (file_id,))
            if result and isinstance(result.get("metadata"), str):
                result["metadata"] = json.loads(result["metadata"])
            return result
        except Exception as e:
            logger.error(f"Failed to get file by ID: {e}")
            return None

    def get_file_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Get file record by hash (for deduplication)."""
        query = """
            SELECT id, filename, original_filename, file_path, file_type,
                   processing_status, extracted_text, metadata
            FROM file_loads
            WHERE file_hash = %s
            ORDER BY created_at DESC
            LIMIT 1
        """
        try:
            result = self.db.fetch_one(query, (file_hash,))
            if result and isinstance(result.get("metadata"), str):
                result["metadata"] = json.loads(result["metadata"])
            return result
        except Exception as e:
            logger.error(f"Failed to get file by hash: {e}")
            return None

    def get_session_files(
        self,
        session_id: str,
        file_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all files for a session.

        Args:
            session_id: Session identifier
            file_type: Optional filter by file type
            status: Optional filter by processing status

        Returns:
            List of file records
        """
        conditions = ["session_id = %s"]
        params = [session_id]

        if file_type:
            conditions.append("file_type = %s")
            params.append(file_type)

        if status:
            conditions.append("processing_status = %s")
            params.append(status)

        query = f"""
            SELECT id, filename, original_filename, file_path, file_type,
                   mime_type, file_size, processing_status, created_at
            FROM file_loads
            WHERE {' AND '.join(conditions)}
            ORDER BY created_at DESC
        """
        try:
            return self.db.fetch_all(query, tuple(params))
        except Exception as e:
            logger.error(f"Failed to get session files: {e}")
            return []

    def get_extracted_text(self, file_id: int) -> Optional[str]:
        """Get extracted text for a file."""
        query = """
            SELECT extracted_text FROM file_loads
            WHERE id = %s AND processing_status = 'completed'
        """
        try:
            result = self.db.fetch_one(query, (file_id,))
            return result.get("extracted_text") if result else None
        except Exception as e:
            logger.error(f"Failed to get extracted text: {e}")
            return None

    def get_pending_files(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get files pending processing."""
        query = """
            SELECT id, filename, file_path, file_type, mime_type, file_size
            FROM file_loads
            WHERE processing_status = 'pending'
            ORDER BY created_at ASC
            LIMIT %s
        """
        try:
            return self.db.fetch_all(query, (limit,))
        except Exception as e:
            logger.error(f"Failed to get pending files: {e}")
            return []

    def search_files(
        self,
        search_text: str,
        file_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search files by extracted text content.

        Args:
            search_text: Text to search for
            file_type: Optional filter by file type
            limit: Maximum results

        Returns:
            List of matching files
        """
        if file_type:
            query = """
                SELECT id, filename, original_filename, file_type, file_size,
                       processing_status, created_at,
                       ts_headline('english', extracted_text, plainto_tsquery(%s),
                                   'MaxWords=50, MinWords=20') as excerpt
                FROM file_loads
                WHERE file_type = %s
                  AND extracted_text ILIKE %s
                ORDER BY created_at DESC
                LIMIT %s
            """
            params = (search_text, file_type, f"%{search_text}%", limit)
        else:
            query = """
                SELECT id, filename, original_filename, file_type, file_size,
                       processing_status, created_at,
                       SUBSTRING(extracted_text FROM 1 FOR 200) as excerpt
                FROM file_loads
                WHERE extracted_text ILIKE %s
                ORDER BY created_at DESC
                LIMIT %s
            """
            params = (f"%{search_text}%", limit)

        try:
            return self.db.fetch_all(query, params)
        except Exception as e:
            logger.error(f"Failed to search files: {e}")
            return []

    def get_file_stats(self) -> Dict[str, Any]:
        """Get overall file statistics."""
        query = """
            SELECT
                COUNT(*) as total_files,
                COUNT(CASE WHEN processing_status = 'completed' THEN 1 END) as processed,
                COUNT(CASE WHEN processing_status = 'pending' THEN 1 END) as pending,
                COUNT(CASE WHEN processing_status = 'failed' THEN 1 END) as failed,
                SUM(file_size) as total_size,
                COUNT(DISTINCT file_type) as unique_types,
                COUNT(DISTINCT session_id) as sessions_with_files
            FROM file_loads
        """
        try:
            result = self.db.fetch_one(query)
            if result:
                result["total_size_mb"] = round((result.get("total_size") or 0) / (1024 * 1024), 2)
            return result or {}
        except Exception as e:
            logger.error(f"Failed to get file stats: {e}")
            return {}

    def get_stats_by_type(self) -> List[Dict[str, Any]]:
        """Get statistics grouped by file type."""
        query = """
            SELECT
                file_type,
                COUNT(*) as count,
                SUM(file_size) as total_size,
                AVG(file_size) as avg_size
            FROM file_loads
            GROUP BY file_type
            ORDER BY count DESC
        """
        try:
            return self.db.fetch_all(query)
        except Exception as e:
            logger.error(f"Failed to get stats by type: {e}")
            return []

    def delete_file_record(self, file_id: int) -> bool:
        """Delete a file record."""
        query = "DELETE FROM file_loads WHERE id = %s"
        try:
            affected = self.db.execute(query, (file_id,))
            return affected > 0
        except Exception as e:
            logger.error(f"Failed to delete file record: {e}")
            return False

    def cleanup_old_files(self, days: int = 30) -> int:
        """Delete file records older than specified days."""
        query = """
            DELETE FROM file_loads
            WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '%s days'
        """
        try:
            deleted = self.db.execute(query, (days,))
            logger.info(f"Cleaned up {deleted} old file records")
            return deleted
        except Exception as e:
            logger.error(f"Failed to cleanup old files: {e}")
            return 0
