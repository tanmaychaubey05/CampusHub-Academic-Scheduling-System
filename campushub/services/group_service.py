"""
Study Group Management Service (Functional Module 1).
Handles group creation, membership workflows, approval queues, and discovery.
"""

from typing import Optional, List, Dict, Any
from campushub.database.db_manager import DatabaseManager, get_db
from campushub.models.study_group import StudyGroup, GroupMember, GroupRole, MembershipStatus
from campushub.models.user import UserRole
from campushub.utils.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    PermissionDeniedError,
    DuplicateEntityError,
)
from campushub.utils.validators import validate_not_blank
from campushub.utils.logger import setup_logger

logger = setup_logger("group_service")


class GroupService:
    """Manages study group lifecycles, memberships, and role assignments."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or get_db()

    def create_group(
        self,
        creator_id: int,
        name: str,
        course_code: str,
        description: str = "",
        max_members: int = 20,
        is_private: bool = False,
    ) -> StudyGroup:
        """Creates a new study group and adds the creator as LEADER."""
        name = validate_not_blank(name, "Group Name")
        course_code = validate_not_blank(course_code, "Course Code").upper()

        if max_members < 2 or max_members > 100:
            raise ValidationError("Max members must be between 2 and 100.")

        with self.db.transaction() as cur:
            cur.execute(
                """
                INSERT INTO study_groups (name, course_code, description, creator_id, max_members, is_private)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (name, course_code, description.strip(), creator_id, max_members, int(is_private)),
            )
            group_id = cur.lastrowid

            # Add creator as LEADER
            cur.execute(
                """
                INSERT INTO group_members (group_id, user_id, role_in_group, status)
                VALUES (?, ?, ?, ?)
                """,
                (group_id, creator_id, GroupRole.LEADER.value, MembershipStatus.ACTIVE.value),
            )

        logger.info(f"Group '{name}' ({course_code}) created by user {creator_id} with ID {group_id}.")
        return self.get_group_by_id(group_id)

    def get_group_by_id(self, group_id: int) -> StudyGroup:
        """Retrieves group details by ID including member count."""
        query = """
            SELECT g.*, u.full_name as creator_name,
                   (SELECT COUNT(*) FROM group_members gm WHERE gm.group_id = g.id AND gm.status = 'ACTIVE') as member_count
            FROM study_groups g
            JOIN users u ON g.creator_id = u.id
            WHERE g.id = ?
        """
        row = self.db.execute_query_one(query, (group_id,))
        if not row:
            raise ResourceNotFoundError(f"Study group {group_id} not found.")
        return StudyGroup.from_row(row)

    def list_groups(
        self, course_code: Optional[str] = None, search_query: Optional[str] = None
    ) -> List[StudyGroup]:
        """Lists active study groups with optional filtering."""
        query = """
            SELECT g.*, u.full_name as creator_name,
                   (SELECT COUNT(*) FROM group_members gm WHERE gm.group_id = g.id AND gm.status = 'ACTIVE') as member_count
            FROM study_groups g
            JOIN users u ON g.creator_id = u.id
            WHERE 1=1
        """
        params: List[Any] = []
        if course_code:
            query += " AND UPPER(g.course_code) = ?"
            params.append(course_code.strip().upper())
        if search_query:
            query += " AND (LOWER(g.name) LIKE ? OR LOWER(g.description) LIKE ?)"
            term = f"%{search_query.strip().lower()}%"
            params.extend([term, term])

        query += " ORDER BY g.created_at DESC"
        rows = self.db.execute_query_all(query, tuple(params))
        return [StudyGroup.from_row(r) for r in rows]

    def join_group(self, group_id: int, user_id: int) -> GroupMember:
        """
        Submits request or directly joins group.
        If group is private, status is PENDING; otherwise ACTIVE.
        """
        group = self.get_group_by_id(group_id)

        # Check existing membership
        existing = self.db.execute_query_one(
            "SELECT * FROM group_members WHERE group_id = ? AND user_id = ?",
            (group_id, user_id),
        )
        if existing:
            status = existing["status"]
            if status == MembershipStatus.ACTIVE.value:
                raise DuplicateEntityError("You are already an active member of this group.")
            elif status == MembershipStatus.PENDING.value:
                raise DuplicateEntityError("Your join request is already pending leader approval.")
            else:
                # Re-apply if previously rejected
                initial_status = MembershipStatus.PENDING.value if group.is_private else MembershipStatus.ACTIVE.value
                self.db.execute_write(
                    "UPDATE group_members SET status = ?, joined_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (initial_status, existing["id"]),
                )
                return self.get_membership(group_id, user_id)

        # Check capacity
        active_count = self.db.execute_query_one(
            "SELECT COUNT(*) as cnt FROM group_members WHERE group_id = ? AND status = 'ACTIVE'",
            (group_id,),
        )["cnt"]
        if active_count >= group.max_members:
            raise ValidationError(f"Study group is full (max capacity: {group.max_members}).")

        initial_status = MembershipStatus.PENDING.value if group.is_private else MembershipStatus.ACTIVE.value
        mem_id = self.db.execute_write(
            """
            INSERT INTO group_members (group_id, user_id, role_in_group, status)
            VALUES (?, ?, ?, ?)
            """,
            (group_id, user_id, GroupRole.MEMBER.value, initial_status),
        )

        logger.info(f"User {user_id} joined group {group_id} with status '{initial_status}'.")
        return self.get_membership(group_id, user_id)

    def approve_membership(self, group_id: int, member_user_id: int, actor_id: int) -> None:
        """Approves a pending membership request. Only group leader or admin can approve."""
        self._verify_leader_or_admin(group_id, actor_id)
        res = self.db.execute_write(
            """
            UPDATE group_members SET status = 'ACTIVE'
            WHERE group_id = ? AND user_id = ? AND status = 'PENDING'
            """,
            (group_id, member_user_id),
        )
        logger.info(f"Leader {actor_id} approved user {member_user_id} for group {group_id}.")

    def reject_membership(self, group_id: int, member_user_id: int, actor_id: int) -> None:
        """Rejects a pending membership request."""
        self._verify_leader_or_admin(group_id, actor_id)
        self.db.execute_write(
            """
            UPDATE group_members SET status = 'REJECTED'
            WHERE group_id = ? AND user_id = ? AND status = 'PENDING'
            """,
            (group_id, member_user_id),
        )
        logger.info(f"Leader {actor_id} rejected user {member_user_id} for group {group_id}.")

    def leave_group(self, group_id: int, user_id: int) -> None:
        """Removes a user from a study group."""
        mem = self.get_membership(group_id, user_id)
        if mem.role_in_group == GroupRole.LEADER.value:
            raise ValidationError("Group leaders cannot leave without transferring leadership first.")
        self.db.execute_write(
            "DELETE FROM group_members WHERE group_id = ? AND user_id = ?",
            (group_id, user_id),
        )
        logger.info(f"User {user_id} left group {group_id}.")

    def get_group_members(self, group_id: int, include_pending: bool = False) -> List[GroupMember]:
        """Lists members belonging to a group."""
        status_filter = "('ACTIVE', 'PENDING')" if include_pending else "('ACTIVE')"
        query = f"""
            SELECT gm.*, u.username, u.full_name
            FROM group_members gm
            JOIN users u ON gm.user_id = u.id
            WHERE gm.group_id = ? AND gm.status IN {status_filter}
            ORDER BY CASE gm.role_in_group WHEN 'LEADER' THEN 1 WHEN 'MODERATOR' THEN 2 ELSE 3 END
        """
        rows = self.db.execute_query_all(query, (group_id,))
        return [GroupMember.from_row(r) for r in rows]

    def get_user_groups(self, user_id: int) -> List[StudyGroup]:
        """Lists all groups in which the user is an active member."""
        query = """
            SELECT g.*, u.full_name as creator_name,
                   (SELECT COUNT(*) FROM group_members gm2 WHERE gm2.group_id = g.id AND gm2.status = 'ACTIVE') as member_count
            FROM study_groups g
            JOIN group_members gm ON g.id = gm.group_id
            JOIN users u ON g.creator_id = u.id
            WHERE gm.user_id = ? AND gm.status = 'ACTIVE'
            ORDER BY g.name ASC
        """
        rows = self.db.execute_query_all(query, (user_id,))
        return [StudyGroup.from_row(r) for r in rows]

    def get_membership(self, group_id: int, user_id: int) -> GroupMember:
        """Retrieves membership record for a specific user in a group."""
        query = """
            SELECT gm.*, u.username, u.full_name
            FROM group_members gm
            JOIN users u ON gm.user_id = u.id
            WHERE gm.group_id = ? AND gm.user_id = ?
        """
        row = self.db.execute_query_one(query, (group_id, user_id))
        if not row:
            raise ResourceNotFoundError(f"User {user_id} is not a member of group {group_id}.")
        return GroupMember.from_row(row)

    def _verify_leader_or_admin(self, group_id: int, actor_id: int) -> None:
        """Enforces that actor is either the group leader, moderator, or system admin."""
        user = self.db.execute_query_one("SELECT role FROM users WHERE id = ?", (actor_id,))
        if user and user["role"] == UserRole.ADMIN.value:
            return

        mem = self.db.execute_query_one(
            "SELECT role_in_group FROM group_members WHERE group_id = ? AND user_id = ? AND status = 'ACTIVE'",
            (group_id, actor_id),
        )
        if not mem or mem["role_in_group"] not in (GroupRole.LEADER.value, GroupRole.MODERATOR.value):
            raise PermissionDeniedError("Action requires Group Leader or Moderator privileges.")
