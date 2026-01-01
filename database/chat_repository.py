"""
Chat Repository - Handles all chat history database operations.
"""
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from .db_manager import DatabaseManager, get_db_manager

logger = logging.getLogger(__name__)


class ChatRepository:
    """Repository for managing chat history in the database."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize chat repository.

        Args:
            db_manager: DatabaseManager instance. If None, uses global instance.
        """
        self.db = db_manager or get_db_manager()

    def save_message(
        self,
        session_id: str,
        role: str,
        message: str,
        agent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tokens_used: int = 0
    ) -> Optional[int]:
        """
        Save a chat message to the database.

        Args:
            session_id: Unique session identifier
            role: Message role (user, assistant, system)
            message: Message content
            agent_id: Optional agent that handled the message
            metadata: Optional metadata dictionary
            tokens_used: Number of tokens used

        Returns:
            Inserted message ID or None on failure
        """
        query = """
            INSERT INTO chat_history
                (session_id, role, message, agent_id, metadata, tokens_used)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        try:
            message_id = self.db.insert_returning(
                query,
                (
                    session_id,
                    role,
                    message,
                    agent_id,
                    json.dumps(metadata or {}),
                    tokens_used
                )
            )
            logger.debug(f"Saved message {message_id} for session {session_id}")
            return message_id
        except Exception as e:
            logger.error(f"Failed to save message: {e}")
            return None

    def save_conversation(
        self,
        session_id: str,
        messages: List[Dict[str, Any]],
        agent_id: Optional[str] = None
    ) -> int:
        """
        Save multiple messages at once.

        Args:
            session_id: Session identifier
            messages: List of message dictionaries with 'role' and 'content'
            agent_id: Optional agent ID for all messages

        Returns:
            Number of messages saved
        """
        saved_count = 0
        for msg in messages:
            result = self.save_message(
                session_id=session_id,
                role=msg.get("role", "user"),
                message=msg.get("content", ""),
                agent_id=agent_id,
                metadata=msg.get("metadata"),
                tokens_used=msg.get("tokens", 0)
            )
            if result:
                saved_count += 1
        return saved_count

    def get_session_history(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get chat history for a session.

        Args:
            session_id: Session identifier
            limit: Maximum number of messages to return
            offset: Number of messages to skip

        Returns:
            List of message dictionaries
        """
        query = """
            SELECT id, session_id, role, message, agent_id, metadata,
                   tokens_used, created_at
            FROM chat_history
            WHERE session_id = %s
            ORDER BY created_at ASC
            LIMIT %s OFFSET %s
        """
        try:
            results = self.db.fetch_all(query, (session_id, limit, offset))
            # Parse metadata JSON
            for row in results:
                if isinstance(row.get("metadata"), str):
                    row["metadata"] = json.loads(row["metadata"])
                if row.get("created_at"):
                    row["created_at"] = row["created_at"].isoformat()
            return results
        except Exception as e:
            logger.error(f"Failed to get session history: {e}")
            return []

    def get_recent_messages(
        self,
        session_id: str,
        count: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get the most recent messages for a session.

        Args:
            session_id: Session identifier
            count: Number of recent messages to return

        Returns:
            List of message dictionaries (newest first)
        """
        query = """
            SELECT id, role, message, agent_id, metadata, tokens_used, created_at
            FROM chat_history
            WHERE session_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """
        try:
            results = self.db.fetch_all(query, (session_id, count))
            # Reverse to get chronological order
            results.reverse()
            for row in results:
                if isinstance(row.get("metadata"), str):
                    row["metadata"] = json.loads(row["metadata"])
                if row.get("created_at"):
                    row["created_at"] = row["created_at"].isoformat()
            return results
        except Exception as e:
            logger.error(f"Failed to get recent messages: {e}")
            return []

    def get_conversation_for_context(
        self,
        session_id: str,
        max_messages: int = 20
    ) -> List[Dict[str, str]]:
        """
        Get conversation history formatted for AI context.

        Args:
            session_id: Session identifier
            max_messages: Maximum messages to include in context

        Returns:
            List of {"role": ..., "content": ...} dictionaries
        """
        messages = self.get_recent_messages(session_id, max_messages)
        return [
            {"role": msg["role"], "content": msg["message"]}
            for msg in messages
        ]

    def search_messages(
        self,
        query_text: str,
        session_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search messages by content.

        Args:
            query_text: Text to search for
            session_id: Optional session to limit search to
            limit: Maximum results to return

        Returns:
            List of matching messages
        """
        if session_id:
            query = """
                SELECT id, session_id, role, message, agent_id, created_at
                FROM chat_history
                WHERE session_id = %s AND message ILIKE %s
                ORDER BY created_at DESC
                LIMIT %s
            """
            params = (session_id, f"%{query_text}%", limit)
        else:
            query = """
                SELECT id, session_id, role, message, agent_id, created_at
                FROM chat_history
                WHERE message ILIKE %s
                ORDER BY created_at DESC
                LIMIT %s
            """
            params = (f"%{query_text}%", limit)

        try:
            return self.db.fetch_all(query, params)
        except Exception as e:
            logger.error(f"Failed to search messages: {e}")
            return []

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get statistics for a session.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary with session statistics
        """
        query = """
            SELECT
                COUNT(*) as total_messages,
                COUNT(CASE WHEN role = 'user' THEN 1 END) as user_messages,
                COUNT(CASE WHEN role = 'assistant' THEN 1 END) as assistant_messages,
                SUM(tokens_used) as total_tokens,
                MIN(created_at) as first_message,
                MAX(created_at) as last_message,
                COUNT(DISTINCT agent_id) as agents_used
            FROM chat_history
            WHERE session_id = %s
        """
        try:
            result = self.db.fetch_one(query, (session_id,))
            if result:
                if result.get("first_message"):
                    result["first_message"] = result["first_message"].isoformat()
                if result.get("last_message"):
                    result["last_message"] = result["last_message"].isoformat()
            return result or {}
        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            return {}

    def get_all_sessions(
        self,
        limit: int = 100,
        active_within_hours: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get list of all sessions with their latest activity.

        Args:
            limit: Maximum sessions to return
            active_within_hours: Only return sessions active within this many hours

        Returns:
            List of session summaries
        """
        if active_within_hours:
            cutoff = datetime.utcnow() - timedelta(hours=active_within_hours)
            query = """
                SELECT
                    session_id,
                    COUNT(*) as message_count,
                    MIN(created_at) as started_at,
                    MAX(created_at) as last_activity,
                    SUM(tokens_used) as total_tokens
                FROM chat_history
                WHERE created_at > %s
                GROUP BY session_id
                ORDER BY last_activity DESC
                LIMIT %s
            """
            params = (cutoff, limit)
        else:
            query = """
                SELECT
                    session_id,
                    COUNT(*) as message_count,
                    MIN(created_at) as started_at,
                    MAX(created_at) as last_activity,
                    SUM(tokens_used) as total_tokens
                FROM chat_history
                GROUP BY session_id
                ORDER BY last_activity DESC
                LIMIT %s
            """
            params = (limit,)

        try:
            results = self.db.fetch_all(query, params)
            for row in results:
                if row.get("started_at"):
                    row["started_at"] = row["started_at"].isoformat()
                if row.get("last_activity"):
                    row["last_activity"] = row["last_activity"].isoformat()
            return results
        except Exception as e:
            logger.error(f"Failed to get sessions: {e}")
            return []

    def delete_session(self, session_id: str) -> int:
        """
        Delete all messages for a session.

        Args:
            session_id: Session identifier

        Returns:
            Number of deleted messages
        """
        query = "DELETE FROM chat_history WHERE session_id = %s"
        try:
            return self.db.execute(query, (session_id,))
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return 0

    def cleanup_old_sessions(self, days: int = 30) -> int:
        """
        Delete chat history older than specified days.

        Args:
            days: Delete messages older than this many days

        Returns:
            Number of deleted messages
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = "DELETE FROM chat_history WHERE created_at < %s"
        try:
            deleted = self.db.execute(query, (cutoff,))
            logger.info(f"Cleaned up {deleted} old messages")
            return deleted
        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {e}")
            return 0


# Async version for real-time operations
class AsyncChatRepository:
    """Async repository for high-performance chat operations."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or get_db_manager()

    async def save_message(
        self,
        session_id: str,
        role: str,
        message: str,
        agent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tokens_used: int = 0
    ) -> Optional[int]:
        """Save a chat message asynchronously."""
        query = """
            INSERT INTO chat_history
                (session_id, role, message, agent_id, metadata, tokens_used)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id
        """
        try:
            result = await self.db.async_fetch_one(
                query,
                session_id,
                role,
                message,
                agent_id,
                json.dumps(metadata or {}),
                tokens_used
            )
            return result.get("id") if result else None
        except Exception as e:
            logger.error(f"Failed to save message async: {e}")
            return None

    async def get_session_history(
        self,
        session_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get chat history asynchronously."""
        query = """
            SELECT id, session_id, role, message, agent_id, metadata,
                   tokens_used, created_at
            FROM chat_history
            WHERE session_id = $1
            ORDER BY created_at ASC
            LIMIT $2
        """
        try:
            results = await self.db.async_fetch_all(query, session_id, limit)
            for row in results:
                if isinstance(row.get("metadata"), str):
                    row["metadata"] = json.loads(row["metadata"])
            return results
        except Exception as e:
            logger.error(f"Failed to get session history async: {e}")
            return []

    async def get_conversation_for_context(
        self,
        session_id: str,
        max_messages: int = 20
    ) -> List[Dict[str, str]]:
        """Get conversation formatted for AI context asynchronously."""
        query = """
            SELECT role, message
            FROM chat_history
            WHERE session_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """
        try:
            results = await self.db.async_fetch_all(query, session_id, max_messages)
            results.reverse()
            return [{"role": r["role"], "content": r["message"]} for r in results]
        except Exception as e:
            logger.error(f"Failed to get context async: {e}")
            return []
