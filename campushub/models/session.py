"""
Study Session and Attendance Domain Models.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any


class SessionStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class AttendanceStatus(str, Enum):
    RSVP = "RSVP"
    ATTENDED = "ATTENDED"
    ABSENT = "ABSENT"


@dataclass
class StudySession:
    id: int
    group_id: int
    title: str
    description: str
    host_id: int
    location_or_link: str
    start_time: str
    end_time: str
    status: str = SessionStatus.SCHEDULED.value
    created_at: Optional[str] = None
    group_name: Optional[str] = None
    host_name: Optional[str] = None
    attendee_count: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "group_id": self.group_id,
            "group_name": self.group_name,
            "title": self.title,
            "description": self.description,
            "host_id": self.host_id,
            "host_name": self.host_name,
            "location_or_link": self.location_or_link,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": self.status,
            "attendee_count": self.attendee_count or 0,
            "created_at": self.created_at,
        }

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "StudySession":
        return cls(
            id=row["id"],
            group_id=row["group_id"],
            title=row["title"],
            description=row.get("description", ""),
            host_id=row["host_id"],
            location_or_link=row["location_or_link"],
            start_time=row["start_time"],
            end_time=row["end_time"],
            status=row.get("status", SessionStatus.SCHEDULED.value),
            created_at=str(row.get("created_at")),
            group_name=row.get("group_name"),
            host_name=row.get("host_name"),
            attendee_count=row.get("attendee_count"),
        )


@dataclass
class AttendanceRecord:
    id: int
    session_id: int
    user_id: int
    status: str
    check_in_time: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "status": self.status,
            "check_in_time": self.check_in_time,
            "username": self.username,
            "full_name": self.full_name,
        }

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "AttendanceRecord":
        return cls(
            id=row["id"],
            session_id=row["session_id"],
            user_id=row["user_id"],
            status=row["status"],
            check_in_time=str(row.get("check_in_time")) if row.get("check_in_time") else None,
            username=row.get("username"),
            full_name=row.get("full_name"),
        )
