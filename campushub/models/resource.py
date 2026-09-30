"""
Study Resource Domain Model.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List


class ResourceType(str, Enum):
    NOTES = "NOTES"
    PAST_PAPER = "PAST_PAPER"
    CODE = "CODE"
    SLIDES = "SLIDES"
    REFERENCE = "REFERENCE"


@dataclass
class StudyResource:
    id: int
    group_id: int
    uploader_id: int
    title: str
    resource_type: str
    file_or_url: str
    description: str
    tags: str
    download_count: int = 0
    created_at: Optional[str] = None
    uploader_name: Optional[str] = None
    group_name: Optional[str] = None

    @property
    def tag_list(self) -> List[str]:
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "group_id": self.group_id,
            "group_name": self.group_name,
            "uploader_id": self.uploader_id,
            "uploader_name": self.uploader_name,
            "title": self.title,
            "resource_type": self.resource_type,
            "file_or_url": self.file_or_url,
            "description": self.description,
            "tags": self.tags,
            "tag_list": self.tag_list,
            "download_count": self.download_count,
            "created_at": self.created_at,
        }

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "StudyResource":
        return cls(
            id=row["id"],
            group_id=row["group_id"],
            uploader_id=row["uploader_id"],
            title=row["title"],
            resource_type=row["resource_type"],
            file_or_url=row["file_or_url"],
            description=row.get("description", ""),
            tags=row.get("tags", ""),
            download_count=row.get("download_count", 0),
            created_at=str(row.get("created_at")),
            uploader_name=row.get("uploader_name"),
            group_name=row.get("group_name"),
        )
