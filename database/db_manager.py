"""
Database Manager for PostgreSQL operations.
Handles connection pooling, transactions, and common database operations.
"""
import os
import json
import logging
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from datetime import datetime

try:
    import psycopg2
    from psycopg2 import pool, sql, extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages PostgreSQL database connections and operations.
    Supports both synchronous (psycopg2) and asynchronous (asyncpg) operations.
    """

    # Default connection settings
    DEFAULT_CONFIG = {
        "host": "postgresql-leadmin-service.postgresql-leadmin.svc.cluster.local",
        "port": 5432,
        "database": "chatbot_data",
        "user": "root",
        "password": "Fin@spot!leadmin",
        "min_connections": 1,
        "max_connections": 10
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the database manager.

        Args:
            config: Database configuration dictionary. If None, uses defaults or env vars.
        """
        self.config = self._load_config(config)
        self._sync_pool = None
        self._async_pool = None
        self._initialized = False

    def _load_config(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Load configuration from various sources."""
        final_config = self.DEFAULT_CONFIG.copy()

        # Override with config file if exists
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    if "postgresql" in file_config:
                        final_config.update(file_config["postgresql"])
            except Exception as e:
                logger.warning(f"Could not load config file: {e}")

        # Override with environment variables
        env_mappings = {
            "DB_HOST": "host",
            "DB_PORT": "port",
            "DB_NAME": "database",
            "DB_USER": "user",
            "DB_PASSWORD": "password",
            "DATABASE_URL": None  # Special handling
        }

        for env_var, config_key in env_mappings.items():
            value = os.environ.get(env_var)
            if value:
                if config_key:
                    if env_var == "DB_PORT":
                        value = int(value)
                    final_config[config_key] = value
                elif env_var == "DATABASE_URL":
                    # Parse DATABASE_URL format
                    parsed = self._parse_database_url(value)
                    if parsed:
                        final_config.update(parsed)

        # Override with passed config
        if config:
            final_config.update(config)

        return final_config

    def _parse_database_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Parse DATABASE_URL format: postgresql://user:pass@host:port/dbname"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return {
                "host": parsed.hostname,
                "port": parsed.port or 5432,
                "database": parsed.path.lstrip('/'),
                "user": parsed.username,
                "password": parsed.password
            }
        except Exception as e:
            logger.error(f"Failed to parse DATABASE_URL: {e}")
            return None

    def get_connection_string(self) -> str:
        """Get PostgreSQL connection string."""
        return (
            f"postgresql://{self.config['user']}:{self.config['password']}"
            f"@{self.config['host']}:{self.config['port']}/{self.config['database']}"
        )

    def initialize_sync_pool(self) -> bool:
        """Initialize synchronous connection pool using psycopg2."""
        if not PSYCOPG2_AVAILABLE:
            logger.error("psycopg2 is not installed. Run: pip install psycopg2-binary")
            return False

        try:
            self._sync_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=self.config.get("min_connections", 1),
                maxconn=self.config.get("max_connections", 10),
                host=self.config["host"],
                port=self.config["port"],
                database=self.config["database"],
                user=self.config["user"],
                password=self.config["password"]
            )
            self._initialized = True
            logger.info("Database connection pool initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            return False

    async def initialize_async_pool(self) -> bool:
        """Initialize asynchronous connection pool using asyncpg."""
        if not ASYNCPG_AVAILABLE:
            logger.error("asyncpg is not installed. Run: pip install asyncpg")
            return False

        try:
            self._async_pool = await asyncpg.create_pool(
                host=self.config["host"],
                port=self.config["port"],
                database=self.config["database"],
                user=self.config["user"],
                password=self.config["password"],
                min_size=self.config.get("min_connections", 1),
                max_size=self.config.get("max_connections", 10)
            )
            self._initialized = True
            logger.info("Async database connection pool initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize async connection pool: {e}")
            return False

    @contextmanager
    def get_connection(self):
        """Get a connection from the synchronous pool."""
        if not self._sync_pool:
            if not self.initialize_sync_pool():
                raise RuntimeError("Failed to initialize database pool")

        conn = None
        try:
            conn = self._sync_pool.getconn()
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                self._sync_pool.putconn(conn)

    async def get_async_connection(self):
        """Get a connection from the asynchronous pool."""
        if not self._async_pool:
            if not await self.initialize_async_pool():
                raise RuntimeError("Failed to initialize async database pool")
        return await self._async_pool.acquire()

    async def release_async_connection(self, conn):
        """Release an async connection back to the pool."""
        await self._async_pool.release(conn)

    def execute(self, query: str, params: tuple = None) -> int:
        """
        Execute a query that doesn't return results (INSERT, UPDATE, DELETE).

        Returns:
            Number of affected rows.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.rowcount

    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Execute a query with multiple parameter sets."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.executemany(query, params_list)
                return cur.rowcount

    def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
        """Execute a query and fetch one result as a dictionary."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute(query, params)
                result = cur.fetchone()
                return dict(result) if result else None

    def fetch_all(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a query and fetch all results as dictionaries."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute(query, params)
                results = cur.fetchall()
                return [dict(row) for row in results]

    def insert_returning(self, query: str, params: tuple = None) -> Optional[Any]:
        """Execute an INSERT query with RETURNING clause."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                result = cur.fetchone()
                return result[0] if result else None

    async def async_execute(self, query: str, *args) -> str:
        """Execute a query asynchronously."""
        conn = await self.get_async_connection()
        try:
            result = await conn.execute(query, *args)
            return result
        finally:
            await self.release_async_connection(conn)

    async def async_fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Fetch one row asynchronously."""
        conn = await self.get_async_connection()
        try:
            row = await conn.fetchrow(query, *args)
            return dict(row) if row else None
        finally:
            await self.release_async_connection(conn)

    async def async_fetch_all(self, query: str, *args) -> List[Dict[str, Any]]:
        """Fetch all rows asynchronously."""
        conn = await self.get_async_connection()
        try:
            rows = await conn.fetch(query, *args)
            return [dict(row) for row in rows]
        finally:
            await self.release_async_connection(conn)

    def create_tables(self) -> bool:
        """Create all required tables if they don't exist."""
        tables_sql = """
        -- Chat History Table
        CREATE TABLE IF NOT EXISTS chat_history (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL,
            message TEXT NOT NULL,
            agent_id VARCHAR(100),
            metadata JSONB DEFAULT '{}',
            tokens_used INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        -- Create index on session_id for faster lookups
        CREATE INDEX IF NOT EXISTS idx_chat_history_session_id ON chat_history(session_id);
        CREATE INDEX IF NOT EXISTS idx_chat_history_created_at ON chat_history(created_at);

        -- Host History Table
        CREATE TABLE IF NOT EXISTS host_history (
            id SERIAL PRIMARY KEY,
            hostname VARCHAR(255) NOT NULL,
            ip_address VARCHAR(45),
            action VARCHAR(100) NOT NULL,
            status VARCHAR(50) NOT NULL,
            details JSONB DEFAULT '{}',
            user_id VARCHAR(100),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        -- Create indexes for host_history
        CREATE INDEX IF NOT EXISTS idx_host_history_hostname ON host_history(hostname);
        CREATE INDEX IF NOT EXISTS idx_host_history_created_at ON host_history(created_at);
        CREATE INDEX IF NOT EXISTS idx_host_history_status ON host_history(status);

        -- File Loads Table
        CREATE TABLE IF NOT EXISTS file_loads (
            id SERIAL PRIMARY KEY,
            filename VARCHAR(500) NOT NULL,
            original_filename VARCHAR(500),
            file_path TEXT NOT NULL,
            file_type VARCHAR(50) NOT NULL,
            mime_type VARCHAR(100),
            file_size BIGINT NOT NULL,
            file_hash VARCHAR(64),
            processing_status VARCHAR(50) DEFAULT 'pending',
            extracted_text TEXT,
            metadata JSONB DEFAULT '{}',
            session_id VARCHAR(255),
            uploaded_by VARCHAR(100),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP WITH TIME ZONE,
            error_message TEXT
        );

        -- Create indexes for file_loads
        CREATE INDEX IF NOT EXISTS idx_file_loads_session_id ON file_loads(session_id);
        CREATE INDEX IF NOT EXISTS idx_file_loads_file_type ON file_loads(file_type);
        CREATE INDEX IF NOT EXISTS idx_file_loads_status ON file_loads(processing_status);
        CREATE INDEX IF NOT EXISTS idx_file_loads_created_at ON file_loads(created_at);

        -- Session Metadata Table (for tracking active sessions)
        CREATE TABLE IF NOT EXISTS sessions (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(255) UNIQUE NOT NULL,
            user_id VARCHAR(100),
            user_agent TEXT,
            ip_address VARCHAR(45),
            is_active BOOLEAN DEFAULT TRUE,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP WITH TIME ZONE
        );

        -- Create index on sessions
        CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id);
        CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(is_active);
        """

        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(tables_sql)
            logger.info("Database tables created/verified successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            return False

    def health_check(self) -> Dict[str, Any]:
        """Check database connectivity and return health status."""
        result = {
            "status": "unhealthy",
            "database": self.config["database"],
            "host": self.config["host"],
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            row = self.fetch_one("SELECT version() as version, NOW() as server_time")
            if row:
                result["status"] = "healthy"
                result["version"] = row.get("version", "unknown")
                result["server_time"] = str(row.get("server_time", ""))
        except Exception as e:
            result["error"] = str(e)

        return result

    def close(self):
        """Close all database connections."""
        if self._sync_pool:
            self._sync_pool.closeall()
            self._sync_pool = None
            logger.info("Synchronous connection pool closed")

    async def close_async(self):
        """Close async connection pool."""
        if self._async_pool:
            await self._async_pool.close()
            self._async_pool = None
            logger.info("Asynchronous connection pool closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


# Global instance for shared usage
_db_manager: Optional[DatabaseManager] = None


def get_db_manager(config: Optional[Dict[str, Any]] = None) -> DatabaseManager:
    """Get or create a global DatabaseManager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(config)
    return _db_manager
