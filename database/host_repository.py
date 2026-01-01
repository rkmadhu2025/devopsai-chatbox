"""
Host Repository - Handles host activity history database operations.
Tracks host actions, status changes, and activity logs.
"""
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from .db_manager import DatabaseManager, get_db_manager

logger = logging.getLogger(__name__)


class HostRepository:
    """Repository for managing host activity history in the database."""

    # Common action types
    ACTION_TYPES = {
        "DEPLOY": "deploy",
        "RESTART": "restart",
        "STOP": "stop",
        "START": "start",
        "SCALE": "scale",
        "UPDATE": "update",
        "ROLLBACK": "rollback",
        "HEALTH_CHECK": "health_check",
        "CONFIG_CHANGE": "config_change",
        "INCIDENT": "incident",
        "MAINTENANCE": "maintenance",
        "ALERT": "alert",
        "BACKUP": "backup",
        "RESTORE": "restore",
    }

    # Status values
    STATUS_VALUES = {
        "PENDING": "pending",
        "IN_PROGRESS": "in_progress",
        "SUCCESS": "success",
        "FAILED": "failed",
        "CANCELLED": "cancelled",
        "TIMEOUT": "timeout",
    }

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize host repository.

        Args:
            db_manager: DatabaseManager instance. If None, uses global instance.
        """
        self.db = db_manager or get_db_manager()

    def log_action(
        self,
        hostname: str,
        action: str,
        status: str,
        ip_address: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """
        Log a host action to the database.

        Args:
            hostname: Name of the host
            action: Action performed (deploy, restart, etc.)
            status: Status of the action (success, failed, etc.)
            ip_address: IP address of the host
            user_id: User who performed the action
            details: Additional details as dictionary

        Returns:
            Inserted record ID or None on failure
        """
        query = """
            INSERT INTO host_history
                (hostname, ip_address, action, status, details, user_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        try:
            record_id = self.db.insert_returning(
                query,
                (
                    hostname,
                    ip_address,
                    action,
                    status,
                    json.dumps(details or {}),
                    user_id
                )
            )
            logger.debug(f"Logged action {action} for host {hostname}: {status}")
            return record_id
        except Exception as e:
            logger.error(f"Failed to log host action: {e}")
            return None

    def log_deployment(
        self,
        hostname: str,
        version: str,
        status: str,
        ip_address: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """
        Log a deployment action.

        Args:
            hostname: Host being deployed to
            version: Version being deployed
            status: Deployment status
            ip_address: Host IP
            user_id: User performing deployment
            details: Additional deployment details
        """
        full_details = details or {}
        full_details["version"] = version
        full_details["deployment_type"] = "application"

        return self.log_action(
            hostname=hostname,
            action=self.ACTION_TYPES["DEPLOY"],
            status=status,
            ip_address=ip_address,
            user_id=user_id,
            details=full_details
        )

    def log_incident(
        self,
        hostname: str,
        incident_type: str,
        severity: str,
        description: str,
        ip_address: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """
        Log an incident for a host.

        Args:
            hostname: Affected host
            incident_type: Type of incident (outage, degradation, etc.)
            severity: Severity level (critical, high, medium, low)
            description: Incident description
            ip_address: Host IP
            user_id: User reporting
            details: Additional incident details
        """
        full_details = details or {}
        full_details["incident_type"] = incident_type
        full_details["severity"] = severity
        full_details["description"] = description

        return self.log_action(
            hostname=hostname,
            action=self.ACTION_TYPES["INCIDENT"],
            status="reported",
            ip_address=ip_address,
            user_id=user_id,
            details=full_details
        )

    def log_health_check(
        self,
        hostname: str,
        is_healthy: bool,
        response_time_ms: Optional[float] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """
        Log a health check result.

        Args:
            hostname: Host checked
            is_healthy: Whether host is healthy
            response_time_ms: Response time in milliseconds
            ip_address: Host IP
            details: Additional check details
        """
        full_details = details or {}
        full_details["is_healthy"] = is_healthy
        if response_time_ms is not None:
            full_details["response_time_ms"] = response_time_ms

        return self.log_action(
            hostname=hostname,
            action=self.ACTION_TYPES["HEALTH_CHECK"],
            status="success" if is_healthy else "failed",
            ip_address=ip_address,
            details=full_details
        )

    def get_host_history(
        self,
        hostname: str,
        limit: int = 100,
        offset: int = 0,
        action: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get activity history for a specific host.

        Args:
            hostname: Host to get history for
            limit: Maximum records to return
            offset: Number of records to skip
            action: Filter by action type
            status: Filter by status

        Returns:
            List of history records
        """
        conditions = ["hostname = %s"]
        params = [hostname]

        if action:
            conditions.append("action = %s")
            params.append(action)

        if status:
            conditions.append("status = %s")
            params.append(status)

        params.extend([limit, offset])

        query = f"""
            SELECT id, hostname, ip_address, action, status, details,
                   user_id, created_at
            FROM host_history
            WHERE {' AND '.join(conditions)}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        try:
            results = self.db.fetch_all(query, tuple(params))
            for row in results:
                if isinstance(row.get("details"), str):
                    row["details"] = json.loads(row["details"])
                if row.get("created_at"):
                    row["created_at"] = row["created_at"].isoformat()
            return results
        except Exception as e:
            logger.error(f"Failed to get host history: {e}")
            return []

    def get_recent_activity(
        self,
        hours: int = 24,
        limit: int = 100,
        action: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent activity across all hosts.

        Args:
            hours: Look back this many hours
            limit: Maximum records to return
            action: Filter by action type

        Returns:
            List of recent activity records
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        if action:
            query = """
                SELECT id, hostname, ip_address, action, status, details,
                       user_id, created_at
                FROM host_history
                WHERE created_at > %s AND action = %s
                ORDER BY created_at DESC
                LIMIT %s
            """
            params = (cutoff, action, limit)
        else:
            query = """
                SELECT id, hostname, ip_address, action, status, details,
                       user_id, created_at
                FROM host_history
                WHERE created_at > %s
                ORDER BY created_at DESC
                LIMIT %s
            """
            params = (cutoff, limit)

        try:
            results = self.db.fetch_all(query, params)
            for row in results:
                if isinstance(row.get("details"), str):
                    row["details"] = json.loads(row["details"])
                if row.get("created_at"):
                    row["created_at"] = row["created_at"].isoformat()
            return results
        except Exception as e:
            logger.error(f"Failed to get recent activity: {e}")
            return []

    def get_failed_actions(
        self,
        hours: int = 24,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get recent failed actions."""
        return self.get_recent_activity_by_status("failed", hours, limit)

    def get_recent_activity_by_status(
        self,
        status: str,
        hours: int = 24,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get recent activity filtered by status."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        query = """
            SELECT id, hostname, ip_address, action, status, details,
                   user_id, created_at
            FROM host_history
            WHERE created_at > %s AND status = %s
            ORDER BY created_at DESC
            LIMIT %s
        """
        try:
            results = self.db.fetch_all(query, (cutoff, status, limit))
            for row in results:
                if isinstance(row.get("details"), str):
                    row["details"] = json.loads(row["details"])
                if row.get("created_at"):
                    row["created_at"] = row["created_at"].isoformat()
            return results
        except Exception as e:
            logger.error(f"Failed to get activity by status: {e}")
            return []

    def get_host_stats(self, hostname: str) -> Dict[str, Any]:
        """
        Get statistics for a specific host.

        Args:
            hostname: Host to get stats for

        Returns:
            Dictionary with host statistics
        """
        query = """
            SELECT
                COUNT(*) as total_actions,
                COUNT(CASE WHEN status = 'success' THEN 1 END) as successful,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                COUNT(DISTINCT action) as unique_actions,
                MIN(created_at) as first_seen,
                MAX(created_at) as last_seen,
                COUNT(CASE WHEN action = 'deploy' THEN 1 END) as deployments,
                COUNT(CASE WHEN action = 'incident' THEN 1 END) as incidents
            FROM host_history
            WHERE hostname = %s
        """
        try:
            result = self.db.fetch_one(query, (hostname,))
            if result:
                if result.get("first_seen"):
                    result["first_seen"] = result["first_seen"].isoformat()
                if result.get("last_seen"):
                    result["last_seen"] = result["last_seen"].isoformat()
                # Calculate success rate
                total = result.get("total_actions", 0)
                if total > 0:
                    result["success_rate"] = round(
                        (result.get("successful", 0) / total) * 100, 2
                    )
                else:
                    result["success_rate"] = 0.0
            return result or {}
        except Exception as e:
            logger.error(f"Failed to get host stats: {e}")
            return {}

    def get_all_hosts(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get list of all unique hosts with their latest status.

        Returns:
            List of hosts with their latest activity
        """
        query = """
            SELECT DISTINCT ON (hostname)
                hostname,
                ip_address,
                action as last_action,
                status as last_status,
                created_at as last_activity
            FROM host_history
            ORDER BY hostname, created_at DESC
            LIMIT %s
        """
        try:
            results = self.db.fetch_all(query, (limit,))
            for row in results:
                if row.get("last_activity"):
                    row["last_activity"] = row["last_activity"].isoformat()
            return results
        except Exception as e:
            logger.error(f"Failed to get all hosts: {e}")
            return []

    def get_activity_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get summary of activity in the specified time period.

        Returns:
            Dictionary with activity summary
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        query = """
            SELECT
                COUNT(*) as total_actions,
                COUNT(DISTINCT hostname) as unique_hosts,
                COUNT(CASE WHEN status = 'success' THEN 1 END) as successful,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                COUNT(CASE WHEN action = 'deploy' THEN 1 END) as deployments,
                COUNT(CASE WHEN action = 'incident' THEN 1 END) as incidents,
                COUNT(CASE WHEN action = 'health_check' THEN 1 END) as health_checks
            FROM host_history
            WHERE created_at > %s
        """
        try:
            result = self.db.fetch_one(query, (cutoff,))
            if result:
                result["time_period_hours"] = hours
            return result or {}
        except Exception as e:
            logger.error(f"Failed to get activity summary: {e}")
            return {}

    def get_actions_by_type(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get action counts grouped by type."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        query = """
            SELECT
                action,
                COUNT(*) as count,
                COUNT(CASE WHEN status = 'success' THEN 1 END) as successful,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed
            FROM host_history
            WHERE created_at > %s
            GROUP BY action
            ORDER BY count DESC
        """
        try:
            return self.db.fetch_all(query, (cutoff,))
        except Exception as e:
            logger.error(f"Failed to get actions by type: {e}")
            return []

    def search_history(
        self,
        search_term: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search host history by hostname or details.

        Args:
            search_term: Text to search for
            limit: Maximum results

        Returns:
            List of matching records
        """
        query = """
            SELECT id, hostname, ip_address, action, status, details,
                   user_id, created_at
            FROM host_history
            WHERE hostname ILIKE %s
               OR details::text ILIKE %s
            ORDER BY created_at DESC
            LIMIT %s
        """
        pattern = f"%{search_term}%"
        try:
            results = self.db.fetch_all(query, (pattern, pattern, limit))
            for row in results:
                if isinstance(row.get("details"), str):
                    row["details"] = json.loads(row["details"])
                if row.get("created_at"):
                    row["created_at"] = row["created_at"].isoformat()
            return results
        except Exception as e:
            logger.error(f"Failed to search history: {e}")
            return []

    def delete_host_history(self, hostname: str) -> int:
        """Delete all history for a specific host."""
        query = "DELETE FROM host_history WHERE hostname = %s"
        try:
            return self.db.execute(query, (hostname,))
        except Exception as e:
            logger.error(f"Failed to delete host history: {e}")
            return 0

    def cleanup_old_history(self, days: int = 90) -> int:
        """Delete history older than specified days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = "DELETE FROM host_history WHERE created_at < %s"
        try:
            deleted = self.db.execute(query, (cutoff,))
            logger.info(f"Cleaned up {deleted} old host history records")
            return deleted
        except Exception as e:
            logger.error(f"Failed to cleanup old history: {e}")
            return 0
