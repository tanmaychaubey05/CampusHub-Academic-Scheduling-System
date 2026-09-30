"""
Academic Resource Repository Service.
Handles resource uploading, metadata indexing, tagging, and search.
"""

from typing import Optional, List, Dict, Any
from campushub.database.db_manager import DatabaseManager, get_db
from campushub.models.resource import StudyResource, ResourceType
from campushub.models.study_group import MembershipStatus
from campushub.utils.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    PermissionDeniedError,
)
from campushub.utils.validators import validate_not_blank
from campushub.utils.logger import setup_logger

logger = setup_logger("resource_service")


class ResourceService:
    """Manages study materials, categorization, and search index."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or get_db()

    def upload_resource(
        self,
        group_id: int,
        uploader_id: int,
        title: str,
        resource_type: str,
        file_or_url: str,
        description: str = "",
        tags: str = "",
    ) -> StudyResource:
        """Indexes a new study resource in a study group."""
        title = validate_not_blank(title, "Resource Title")
        file_or_url = validate_not_blank(file_or_url, "File Path / URL")

        valid_types = [t.value for t in ResourceType]
        if resource_type.upper() not in valid_types:
            raise ValidationError(f"Invalid resource type. Allowed: {valid_types}")

        # Check uploader is active member of group
        membership = self.db.execute_query_one(
            "SELECT status FROM group_members WHERE group_id = ? AND user_id = ?",
            (group_id, uploader_id),
        )
        if not membership or membership["status"] != MembershipStatus.ACTIVE.value:
            raise PermissionDeniedError("Only active group members can upload resources.")

        res_id = self.db.execute_write(
            """
            INSERT INTO study_resources (group_id, uploader_id, title, resource_type, file_or_url, description, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                group_id,
                uploader_id,
                title,
                resource_type.upper(),
                file_or_url.strip(),
                description.strip(),
                tags.strip().lower(),
            ),
        )

        logger.info(f"Resource {res_id} ('{title}') uploaded by user {uploader_id} to group {group_id}.")
        return self.get_resource_by_id(res_id)

    def get_resource_by_id(self, resource_id: int) -> StudyResource:
        """Retrieves resource by ID."""
        query = """
            SELECT r.*, u.full_name as uploader_name, g.name as group_name
            FROM study_resources r
            JOIN users u ON r.uploader_id = u.id
            JOIN study_groups g ON r.group_id = g.id
            WHERE r.id = ?
        """
        row = self.db.execute_query_one(query, (resource_id,))
        if not row:
            raise ResourceNotFoundError(f"Resource {resource_id} not found.")
        return StudyResource.from_row(row)

    def search_resources(
        self,
        group_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        tag: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> List[StudyResource]:
        """Searches resources with multi-criteria filtering."""
        query = """
            SELECT r.*, u.full_name as uploader_name, g.name as group_name
            FROM study_resources r
            JOIN users u ON r.uploader_id = u.id
            JOIN study_groups g ON r.group_id = g.id
            WHERE 1=1
        """
        params: List[Any] = []

        if group_id:
            query += " AND r.group_id = ?"
            params.append(group_id)
        if resource_type:
            query += " AND r.resource_type = ?"
            params.append(resource_type.upper())
        if tag:
            query += " AND LOWER(r.tags) LIKE ?"
            params.append(f"%{tag.strip().lower()}%")
        if search_query:
            query += " AND (LOWER(r.title) LIKE ? OR LOWER(r.description) LIKE ?)"
            term = f"%{search_query.strip().lower()}%"
            params.extend([term, term])

        query += " ORDER BY r.download_count DESC, r.created_at DESC"
        rows = self.db.execute_query_all(query, tuple(params))
        return [StudyResource.from_row(r) for r in rows]

    def record_download(self, resource_id: int) -> int:
        """Increments download/access counter for resource."""
        self.get_resource_by_id(resource_id)  # Validate exists
        self.db.execute_write(
            "UPDATE study_resources SET download_count = download_count + 1 WHERE id = ?",
            (resource_id,),
        )
        updated = self.db.execute_query_one(
            "SELECT download_count FROM study_resources WHERE id = ?", (resource_id,)
        )
        return updated["download_count"]
