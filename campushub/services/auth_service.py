"""
Authentication and User Management Service.
Implements secure password hashing with salt, user registration, and authentication.
"""

import hashlib
import os
import secrets
from typing import Optional, Dict, Any, List
from campushub.database.db_manager import DatabaseManager, get_db
from campushub.models.user import User, UserRole
from campushub.utils.exceptions import (
    AuthenticationError,
    ValidationError,
    DuplicateEntityError,
    ResourceNotFoundError,
)
from campushub.utils.validators import validate_email, validate_password, validate_not_blank
from campushub.utils.logger import setup_logger

logger = setup_logger("auth_service")


class AuthService:
    """Manages credentials, sessions, and user records."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or get_db()

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        """Computes salted SHA-256 hash using PBKDF2."""
        return hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
        ).hex()

    def register(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str,
        role: str = UserRole.STUDENT.value,
        department: str = "Computer Science",
    ) -> User:
        """Registers a new user after strict input validation."""
        username = validate_not_blank(username, "Username").lower()
        full_name = validate_not_blank(full_name, "Full Name")
        email = validate_email(email)
        password = validate_password(password)
        department = validate_not_blank(department, "Department")

        if role not in [r.value for r in UserRole]:
            raise ValidationError(f"Invalid role '{role}'. Allowed: {[r.value for r in UserRole]}")

        # Check existing username or email
        existing_user = self.db.execute_query_one(
            "SELECT id FROM users WHERE username = ? OR email = ?", (username, email)
        )
        if existing_user:
            raise DuplicateEntityError("Username or email already registered.")

        salt = secrets.token_hex(16)
        pwd_hash = self._hash_password(password, salt)

        user_id = self.db.execute_write(
            """
            INSERT INTO users (username, email, password_hash, salt, full_name, role, department)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (username, email, pwd_hash, salt, full_name, role, department),
        )

        logger.info(f"Registered user '{username}' with ID {user_id} and role '{role}'.")
        return self.get_user_by_id(user_id)

    def login(self, username_or_email: str, password: str) -> User:
        """Authenticates user and returns User model if valid."""
        identifier = validate_not_blank(username_or_email, "Username/Email").strip().lower()
        if not password:
            raise AuthenticationError("Password cannot be blank.")

        row = self.db.execute_query_one(
            "SELECT * FROM users WHERE LOWER(username) = ? OR LOWER(email) = ?",
            (identifier, identifier),
        )
        if not row:
            logger.warning(f"Failed login attempt for identifier: {identifier}")
            raise AuthenticationError("Invalid username or password.")

        expected_hash = self._hash_password(password, row["salt"])
        if not secrets.compare_digest(row["password_hash"], expected_hash):
            logger.warning(f"Failed login attempt (incorrect password) for: {identifier}")
            raise AuthenticationError("Invalid username or password.")

        logger.info(f"User '{row['username']}' logged in successfully.")
        return User.from_row(row)

    def get_user_by_id(self, user_id: int) -> User:
        """Retrieves user by primary key ID."""
        row = self.db.execute_query_one("SELECT * FROM users WHERE id = ?", (user_id,))
        if not row:
            raise ResourceNotFoundError(f"User with ID {user_id} not found.")
        return User.from_row(row)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Retrieves user by username."""
        row = self.db.execute_query_one(
            "SELECT * FROM users WHERE LOWER(username) = ?", (username.strip().lower(),)
        )
        return User.from_row(row) if row else None

    def list_all_users(self) -> List[User]:
        """Lists all registered users (for admin/directory)."""
        rows = self.db.execute_query_all("SELECT * FROM users ORDER BY id ASC")
        return [User.from_row(r) for r in rows]
