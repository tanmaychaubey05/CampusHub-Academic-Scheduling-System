"""
Study Group and Membership Domain Models.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any


class GroupRole(str, Enum):
    LEADER = "LEADER"
    MEMBER = "MEMBER"
    MODERATOR = "MODERATOR"


class MembershipStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PENDING = "PENDING"
    REJECTED = "REJECTED"


@dataclass
class StudyGroup:
    id: int
    name: str
    course_code: str
    description: str
    creator_id: int
    max_members: int = 20
    is_private: bool = False
    created_at: Optional[str] = None
    creator_name: Optional[str] = None
    member_count: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "course_code": self.course_code,
            "description": self.description,
            "creator_id": self.creator_id,
            "creator_name": self.creator_name,
            "max_members": self.max_members,
            "is_private": bool(self.is_private),
            "member_count": self.member_count or 0,
            "created_at": self.created_at,
        }

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "StudyGroup":
        return cls(
            id=row["id"],
            name=row["name"],
            course_code=row["course_code"],
            description=row.get("description", ""),
            creator_id=row["creator_id"],
            max_members=row.get("max_members", 20),
            is_private=bool(row.get("is_private", 0)),
            created_at=str(row.get("created_at")),
            creator_name=row.get("creator_name"),
            member_count=row.get("member_count"),
        )


@dataclass
class GroupMember:
    id: int
    group_id: int
    user_id: int
    role_in_group: str
    status: str
    joined_at: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "group_id": self.group_id,
            "user_id": self.user_id,
            "role_in_group": self.role_in_group,
            "status": self.status,
            "joined_at": self.joined_at,
            "username": self.username,
            "full_name": self.full_name,
        }

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "GroupMember":
        return cls(
            id=row["id"],
            group_id=row["group_id"],
            user_id=row["user_id"],
            role_in_group=row["role_in_group"],
            status=row["status"],
            joined_at=str(row.get("joined_at")),
            username=row.get("username"),
            full_name=row.get("full_name"),
        )
