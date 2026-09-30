"""
Peer Review and Rating Domain Model.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class SessionReview:
    id: int
    session_id: int
    reviewer_id: int
    rating: int
    comments: str
    reviewee_id: Optional[int] = None
    created_at: Optional[str] = None
    reviewer_name: Optional[str] = None
    session_title: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "session_title": self.session_title,
            "reviewer_id": self.reviewer_id,
            "reviewer_name": self.reviewer_name,
            "reviewee_id": self.reviewee_id,
            "rating": self.rating,
            "comments": self.comments,
            "created_at": self.created_at,
        }

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "SessionReview":
        return cls(
            id=row["id"],
            session_id=row["session_id"],
            reviewer_id=row["reviewer_id"],
            rating=row["rating"],
            comments=row.get("comments", ""),
            reviewee_id=row.get("reviewee_id"),
            created_at=str(row.get("created_at")),
            reviewer_name=row.get("reviewer_name"),
            session_title=row.get("session_title"),
        )
