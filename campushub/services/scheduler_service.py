"""
Session Scheduling Service (Functional Module 2).
Handles time-slot booking, algorithmic conflict detection, RSVP, and attendance.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from campushub.database.db_manager import DatabaseManager, get_db
from campushub.models.session import StudySession, AttendanceRecord, SessionStatus, AttendanceStatus
from campushub.models.study_group import MembershipStatus
from campushub.utils.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    PermissionDeniedError,
    SchedulingConflictError,
    DuplicateEntityError,
)
from campushub.utils.validators import (
    validate_not_blank,
    validate_datetime_str,
    validate_time_window,
)
from campushub.utils.logger import setup_logger

logger = setup_logger("scheduler_service")


class SchedulerService:
    """Manages study sessions, conflict detection algorithms, and attendance tracking."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or get_db()

    def schedule_session(
        self,
        group_id: int,
        host_id: int,
        title: str,
        description: str,
        location_or_link: str,
        start_time_str: str,
        end_time_str: str,
    ) -> StudySession:
        """
        Schedules a study session with algorithmic overlap detection.
        Ensures neither host nor group has conflicting active sessions.
        """
        title = validate_not_blank(title, "Session Title")
        location_or_link = validate_not_blank(location_or_link, "Location or Link")

        start_dt = validate_datetime_str(start_time_str, "Start Time")
        end_dt = validate_datetime_str(end_time_str, "End Time")
        validate_time_window(start_dt, end_dt)

        start_iso = start_dt.strftime("%Y-%m-%d %H:%M")
        end_iso = end_dt.strftime("%Y-%m-%d %H:%M")

        # 1. Verify host is active member of group
        membership = self.db.execute_query_one(
            "SELECT status FROM group_members WHERE group_id = ? AND user_id = ?",
            (group_id, host_id),
        )
        if not membership or membership["status"] != MembershipStatus.ACTIVE.value:
            raise PermissionDeniedError("Host must be an active member of the study group.")

        # 2. Algorithmic Overlap Detection for Host
        host_conflicts = self.check_conflicts_for_host(host_id, start_iso, end_iso)
        if host_conflicts:
            c = host_conflicts[0]
            raise SchedulingConflictError(
                f"Host is already booked for '{c['title']}' from {c['start_time']} to {c['end_time']}."
            )

        # 3. Algorithmic Overlap Detection for Group
        group_conflicts = self.check_conflicts_for_group(group_id, start_iso, end_iso)
        if group_conflicts:
            c = group_conflicts[0]
            raise SchedulingConflictError(
                f"Group already has session '{c['title']}' scheduled from {c['start_time']} to {c['end_time']}."
            )

        # 4. Insert Session and auto-RSVP host
        with self.db.transaction() as cur:
            cur.execute(
                """
                INSERT INTO study_sessions (group_id, title, description, host_id, location_or_link, start_time, end_time, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'SCHEDULED')
                """,
                (group_id, title, description.strip(), host_id, location_or_link, start_iso, end_iso),
            )
            session_id = cur.lastrowid

            # Auto RSVP host
            cur.execute(
                """
                INSERT INTO session_attendance (session_id, user_id, status)
                VALUES (?, ?, 'RSVP')
                """,
                (session_id, host_id),
            )

        logger.info(f"Session {session_id} ('{title}') scheduled by host {host_id} for group {group_id}.")
        return self.get_session_by_id(session_id)

    def check_conflicts_for_host(
        self, host_id: int, start_time: str, end_time: str, exclude_session_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Interval overlap algorithm:
        Two intervals [A, B] and [C, D] overlap if and only if (A < D) AND (B > C).
        """
        query = """
            SELECT id, title, start_time, end_time, group_id
            FROM study_sessions
            WHERE host_id = ?
              AND status = 'SCHEDULED'
              AND (start_time < ? AND end_time > ?)
        """
        params: List[Any] = [host_id, end_time, start_time]
        if exclude_session_id:
            query += " AND id != ?"
            params.append(exclude_session_id)

        return self.db.execute_query_all(query, tuple(params))

    def check_conflicts_for_group(
        self, group_id: int, start_time: str, end_time: str, exclude_session_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Check if group has overlapping scheduled sessions."""
        query = """
            SELECT id, title, start_time, end_time
            FROM study_sessions
            WHERE group_id = ?
              AND status = 'SCHEDULED'
              AND (start_time < ? AND end_time > ?)
        """
        params: List[Any] = [group_id, end_time, start_time]
        if exclude_session_id:
            query += " AND id != ?"
            params.append(exclude_session_id)

        return self.db.execute_query_all(query, tuple(params))

    def get_session_by_id(self, session_id: int) -> StudySession:
        """Retrieves session details by ID."""
        query = """
            SELECT s.*, g.name as group_name, u.full_name as host_name,
                   (SELECT COUNT(*) FROM session_attendance sa WHERE sa.session_id = s.id) as attendee_count
            FROM study_sessions s
            JOIN study_groups g ON s.group_id = g.id
            JOIN users u ON s.host_id = u.id
            WHERE s.id = ?
        """
        row = self.db.execute_query_one(query, (session_id,))
        if not row:
            raise ResourceNotFoundError(f"Study session {session_id} not found.")
        return StudySession.from_row(row)

    def list_sessions_for_group(self, group_id: int) -> List[StudySession]:
        """Lists all sessions for a specific study group."""
        query = """
            SELECT s.*, g.name as group_name, u.full_name as host_name,
                   (SELECT COUNT(*) FROM session_attendance sa WHERE sa.session_id = s.id) as attendee_count
            FROM study_sessions s
            JOIN study_groups g ON s.group_id = g.id
            JOIN users u ON s.host_id = u.id
            WHERE s.group_id = ?
            ORDER BY s.start_time ASC
        """
        rows = self.db.execute_query_all(query, (group_id,))
        return [StudySession.from_row(r) for r in rows]

    def list_upcoming_sessions_for_user(self, user_id: int) -> List[StudySession]:
        """Lists all upcoming scheduled sessions for groups the user is a member of."""
        query = """
            SELECT s.*, g.name as group_name, u.full_name as host_name,
                   (SELECT COUNT(*) FROM session_attendance sa WHERE sa.session_id = s.id) as attendee_count
            FROM study_sessions s
            JOIN study_groups g ON s.group_id = g.id
            JOIN group_members gm ON g.id = gm.group_id
            JOIN users u ON s.host_id = u.id
            WHERE gm.user_id = ? AND gm.status = 'ACTIVE'
              AND s.status = 'SCHEDULED'
            ORDER BY s.start_time ASC
        """
        rows = self.db.execute_query_all(query, (user_id,))
        return [StudySession.from_row(r) for r in rows]

    def rsvp_session(self, session_id: int, user_id: int) -> AttendanceRecord:
        """Records an RSVP response for a session."""
        session = self.get_session_by_id(session_id)
        if session.status != SessionStatus.SCHEDULED.value:
            raise ValidationError(f"Cannot RSVP to a session that is {session.status.lower()}.")

        existing = self.db.execute_query_one(
            "SELECT * FROM session_attendance WHERE session_id = ? AND user_id = ?",
            (session_id, user_id),
        )
        if existing:
            return AttendanceRecord.from_row(existing)

        self.db.execute_write(
            """
            INSERT INTO session_attendance (session_id, user_id, status)
            VALUES (?, ?, 'RSVP')
            """,
            (session_id, user_id),
        )
        logger.info(f"User {user_id} RSVP'd to session {session_id}.")
        row = self.db.execute_query_one(
            "SELECT sa.*, u.username, u.full_name FROM session_attendance sa JOIN users u ON sa.user_id = u.id WHERE sa.session_id = ? AND sa.user_id = ?",
            (session_id, user_id),
        )
        return AttendanceRecord.from_row(row)

    def mark_attendance(self, session_id: int, user_id: int) -> AttendanceRecord:
        """Marks a user as having attended the session (check-in)."""
        session = self.get_session_by_id(session_id)
        existing = self.db.execute_query_one(
            "SELECT * FROM session_attendance WHERE session_id = ? AND user_id = ?",
            (session_id, user_id),
        )
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if existing:
            self.db.execute_write(
                """
                UPDATE session_attendance
                SET status = 'ATTENDED', check_in_time = ?
                WHERE id = ?
                """,
                (now_str, existing["id"]),
            )
        else:
            self.db.execute_write(
                """
                INSERT INTO session_attendance (session_id, user_id, status, check_in_time)
                VALUES (?, ?, 'ATTENDED', ?)
                """,
                (session_id, user_id, now_str),
            )

        logger.info(f"User {user_id} checked into session {session_id}.")
        row = self.db.execute_query_one(
            "SELECT sa.*, u.username, u.full_name FROM session_attendance sa JOIN users u ON sa.user_id = u.id WHERE sa.session_id = ? AND sa.user_id = ?",
            (session_id, user_id),
        )
        return AttendanceRecord.from_row(row)

    def complete_session(self, session_id: int, actor_id: int) -> None:
        """Marks a session as completed."""
        session = self.get_session_by_id(session_id)
        if session.host_id != actor_id:
            raise PermissionDeniedError("Only the session host can complete this session.")
        self.db.execute_write(
            "UPDATE study_sessions SET status = 'COMPLETED' WHERE id = ?", (session_id,)
        )
        logger.info(f"Session {session_id} marked as COMPLETED by host {actor_id}.")

    def cancel_session(self, session_id: int, actor_id: int) -> None:
        """Cancels a scheduled session."""
        session = self.get_session_by_id(session_id)
        if session.host_id != actor_id:
            raise PermissionDeniedError("Only the session host can cancel this session.")
        self.db.execute_write(
            "UPDATE study_sessions SET status = 'CANCELLED' WHERE id = ?", (session_id,)
        )
        logger.info(f"Session {session_id} CANCELLED by host {actor_id}.")

    def get_attendance_list(self, session_id: int) -> List[AttendanceRecord]:
        """Lists all RSVPs and attendees for a session."""
        query = """
            SELECT sa.*, u.username, u.full_name
            FROM session_attendance sa
            JOIN users u ON sa.user_id = u.id
            WHERE sa.session_id = ?
            ORDER BY sa.status DESC, u.full_name ASC
        """
        rows = self.db.execute_query_all(query, (session_id,))
        return [AttendanceRecord.from_row(r) for r in rows]
