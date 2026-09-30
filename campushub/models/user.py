"""
User and Role Domain Models.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any


class UserRole(str, Enum):
    STUDENT = "STUDENT"
    TUTOR = "TUTOR"
    ADMIN = "ADMIN"


@dataclass
class User:
    id: int
    username: str
    email: str
    password_hash: str
    salt: str
    full_name: str
    role: str
    department: str
    created_at: Optional[str] = None

    def is_student(self) -> bool:
        return self.role == UserRole.STUDENT.value

    def is_tutor(self) -> bool:
        return self.role == UserRole.TUTOR.value

    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN.value

    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Serializes user model to dictionary."""
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "department": self.department,
            "created_at": self.created_at,
        }
        if include_sensitive:
            data["password_hash"] = self.password_hash
            data["salt"] = self.salt
        return data

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "User":
        return cls(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            password_hash=row["password_hash"],
            salt=row["salt"],
            full_name=row["full_name"],
            role=row["role"],
            department=row["department"],
            created_at=str(row.get("created_at")),
        )
