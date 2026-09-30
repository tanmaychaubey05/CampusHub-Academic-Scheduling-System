"""
Unit tests for AuthService and Password Security.
"""

import unittest
from campushub.database.db_manager import DatabaseManager
from campushub.services.auth_service import AuthService
from campushub.utils.exceptions import (
    AuthenticationError,
    ValidationError,
    DuplicateEntityError,
)
from campushub.models.user import UserRole


class TestAuthService(unittest.TestCase):
    def setUp(self):
        # Use in-memory SQLite database for isolated test execution
        self.db = DatabaseManager(":memory:")
        self.auth_svc = AuthService(self.db)

    def test_successful_registration_and_login(self):
        user = self.auth_svc.register(
            username="student1",
            email="student1@univ.edu",
            password="securePassword1",
            full_name="Alice Smith",
            role=UserRole.STUDENT.value,
            department="Computer Science",
        )
        self.assertIsNotNone(user.id)
        self.assertEqual(user.username, "student1")
        self.assertEqual(user.role, UserRole.STUDENT.value)

        # Login
        logged_in = self.auth_svc.login("student1", "securePassword1")
        self.assertEqual(logged_in.id, user.id)

    def test_duplicate_username_rejection(self):
        self.auth_svc.register(
            username="testdup",
            email="dup1@univ.edu",
            password="passWord123",
            full_name="Duplicate User",
        )
        with self.assertRaises(DuplicateEntityError):
            self.auth_svc.register(
                username="testdup",
                email="dup2@univ.edu",
                password="passWord123",
                full_name="Duplicate User 2",
            )

    def test_weak_password_validation(self):
        with self.assertRaises(ValidationError):
            self.auth_svc.register(
                username="weakpass",
                email="weak@univ.edu",
                password="123",  # Too short
                full_name="Weak Password User",
            )

    def test_invalid_email_format(self):
        with self.assertRaises(ValidationError):
            self.auth_svc.register(
                username="bademail",
                email="not-an-email",
                password="validPass1",
                full_name="Bad Email User",
            )

    def test_invalid_login_credentials(self):
        self.auth_svc.register(
            username="loginfail",
            email="fail@univ.edu",
            password="correctPass1",
            full_name="Login Fail User",
        )
        with self.assertRaises(AuthenticationError):
            self.auth_svc.login("loginfail", "wrongPassword99")


if __name__ == "__main__":
    unittest.main()
