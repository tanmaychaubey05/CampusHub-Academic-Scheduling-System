"""
Database connection and session manager for CampusHub.
Handles SQLite operations, connection lifecycle, and schema initialization.
"""

import sqlite3
import os
from pathlib import Path
from contextlib import contextmanager
from typing import Generator, Any, List, Optional, Tuple, Dict
from campushub.utils.logger import setup_logger

logger = setup_logger("db_manager")

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "campushub.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


class DatabaseManager:
    """Manages SQLite connections and executes parameterized queries."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            self.db_path = str(DEFAULT_DB_PATH)
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self._mem_conn = None
        else:
            self.db_path = db_path
            if self.db_path != ":memory:":
                os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
                self._mem_conn = None
            else:
                self._mem_conn = sqlite3.connect(":memory:")
                self._mem_conn.row_factory = sqlite3.Row
                self._mem_conn.execute("PRAGMA foreign_keys = ON;")

        self._initialize_schema()

    def get_connection(self) -> sqlite3.Connection:
        """Returns a configured SQLite connection."""
        if self._mem_conn is not None:
            return self._mem_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        return conn

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Cursor, None, None]:
        """Context manager providing atomic transaction execution."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction rolled back due to error: {e}")
            raise
        finally:
            if self._mem_conn is None:
                conn.close()

    def _initialize_schema(self) -> None:
        """Executes the DDL schema script if tables do not exist."""
        if not os.path.exists(SCHEMA_PATH):
            raise FileNotFoundError(f"Schema file not found at: {SCHEMA_PATH}")

        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_script = f.read()

        conn = self.get_connection()
        try:
            conn.executescript(schema_script)
            conn.commit()
            logger.info("Database schema initialized successfully.")
        finally:
            if self._mem_conn is None:
                conn.close()

    def execute_write(self, query: str, params: Tuple[Any, ...] = ()) -> int:
        """Executes an INSERT/UPDATE/DELETE query and returns the last row ID or rows affected."""
        with self.transaction() as cur:
            cur.execute(query, params)
            return cur.lastrowid

    def execute_query_all(self, query: str, params: Tuple[Any, ...] = ()) -> List[Dict[str, Any]]:
        """Executes a SELECT query and returns all matching rows as dictionaries."""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(query, params)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        finally:
            if self._mem_conn is None:
                conn.close()

    def execute_query_one(self, query: str, params: Tuple[Any, ...] = ()) -> Optional[Dict[str, Any]]:
        """Executes a SELECT query and returns the first row as a dictionary, or None."""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(query, params)
            row = cur.fetchone()
            return dict(row) if row else None
        finally:
            if self._mem_conn is None:
                conn.close()


# Global Singleton instance for application runtime
_global_db: Optional[DatabaseManager] = None


def get_db(db_path: Optional[str] = None) -> DatabaseManager:
    """Retrieve or initialize the active DatabaseManager instance."""
    global _global_db
    if db_path is not None:
        return DatabaseManager(db_path)
    if _global_db is None:
        _global_db = DatabaseManager()
    return _global_db
