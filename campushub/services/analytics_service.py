"""
Peer Review, Attendance & Analytics Engine Service (Functional Module 3).
Computes participation metrics, attendance percentages, peer ratings, and analytics reports.
"""

from typing import Optional, List, Dict, Any
from campushub.database.db_manager import DatabaseManager, get_db
from campushub.models.review import SessionReview
from campushub.utils.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    PermissionDeniedError,
    DuplicateEntityError,
)
from campushub.utils.validators import validate_rating
from campushub.utils.logger import setup_logger

logger = setup_logger("analytics_service")


class AnalyticsService:
    """Computes academic metrics, peer review statistics, and performance analytics."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or get_db()

    def submit_review(
        self,
        session_id: int,
        reviewer_id: int,
        rating: int,
        comments: str = "",
        reviewee_id: Optional[int] = None,
    ) -> SessionReview:
        """Submits peer feedback or tutor evaluation for a completed/attended session."""
        rating = validate_rating(rating)

        # 1. Verify session exists
        session = self.db.execute_query_one(
            "SELECT * FROM study_sessions WHERE id = ?", (session_id,)
        )
        if not session:
            raise ResourceNotFoundError(f"Session {session_id} not found.")

        # Default reviewee to session host if not specified
        if not reviewee_id:
            reviewee_id = session["host_id"]

        if reviewer_id == reviewee_id:
            raise ValidationError("You cannot review or rate yourself.")

        # 2. Check if reviewer already submitted review for this session
        existing = self.db.execute_query_one(
            "SELECT id FROM session_reviews WHERE session_id = ? AND reviewer_id = ?",
            (session_id, reviewer_id),
        )
        if existing:
            raise DuplicateEntityError("You have already submitted a review for this session.")

        review_id = self.db.execute_write(
            """
            INSERT INTO session_reviews (session_id, reviewer_id, reviewee_id, rating, comments)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, reviewer_id, reviewee_id, rating, comments.strip()),
        )

        logger.info(f"Review {review_id} submitted by user {reviewer_id} for session {session_id} (Rating: {rating}).")
        return self.get_review_by_id(review_id)

    def get_review_by_id(self, review_id: int) -> SessionReview:
        """Retrieves a single review record."""
        query = """
            SELECT r.*, u.full_name as reviewer_name, s.title as session_title
            FROM session_reviews r
            JOIN users u ON r.reviewer_id = u.id
            JOIN study_sessions s ON r.session_id = s.id
            WHERE r.id = ?
        """
        row = self.db.execute_query_one(query, (review_id,))
        if not row:
            raise ResourceNotFoundError(f"Review {review_id} not found.")
        return SessionReview.from_row(row)

    def get_user_rating_summary(self, user_id: int) -> Dict[str, Any]:
        """Calculates average rating, total reviews, and star breakdown for a user/tutor."""
        query = """
            SELECT rating, COUNT(*) as cnt
            FROM session_reviews
            WHERE reviewee_id = ?
            GROUP BY rating
        """
        rows = self.db.execute_query_all(query, (user_id,))
        breakdown = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        total_count = 0
        total_score = 0

        for r in rows:
            stars = r["rating"]
            count = r["cnt"]
            breakdown[stars] = count
            total_count += count
            total_score += stars * count

        avg_rating = round(total_score / total_count, 2) if total_count > 0 else 0.0

        return {
            "user_id": user_id,
            "total_reviews": total_count,
            "average_rating": avg_rating,
            "rating_breakdown": breakdown,
        }

    def get_group_analytics(self, group_id: int) -> Dict[str, Any]:
        """Generates comprehensive participation and attendance analytics for a group."""
        group = self.db.execute_query_one("SELECT * FROM study_groups WHERE id = ?", (group_id,))
        if not group:
            raise ResourceNotFoundError(f"Group {group_id} not found.")

        # Total active members
        members_count = self.db.execute_query_one(
            "SELECT COUNT(*) as c FROM group_members WHERE group_id = ? AND status = 'ACTIVE'",
            (group_id,),
        )["c"]

        # Sessions stats
        sessions_query = """
            SELECT 
                COUNT(*) as total_sessions,
                SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) as completed_sessions,
                SUM(CASE WHEN status = 'SCHEDULED' THEN 1 ELSE 0 END) as scheduled_sessions,
                SUM(CASE WHEN status = 'CANCELLED' THEN 1 ELSE 0 END) as cancelled_sessions
            FROM study_sessions
            WHERE group_id = ?
        """
        session_stats = self.db.execute_query_one(sessions_query, (group_id,))
        total_sessions = session_stats["total_sessions"] or 0
        completed_sessions = session_stats["completed_sessions"] or 0

        # Attendance stats
        attendance_query = """
            SELECT 
                COUNT(sa.id) as total_rsvps,
                SUM(CASE WHEN sa.status = 'ATTENDED' THEN 1 ELSE 0 END) as total_attended
            FROM session_attendance sa
            JOIN study_sessions s ON sa.session_id = s.id
            WHERE s.group_id = ?
        """
        att_stats = self.db.execute_query_one(attendance_query, (group_id,))
        total_rsvps = att_stats["total_rsvps"] or 0
        total_attended = att_stats["total_attended"] or 0

        attendance_rate = (
            round((total_attended / total_rsvps) * 100, 1) if total_rsvps > 0 else 0.0
        )

        # Resources stats
        res_stats = self.db.execute_query_one(
            "SELECT COUNT(*) as total_resources, COALESCE(SUM(download_count), 0) as total_downloads FROM study_resources WHERE group_id = ?",
            (group_id,),
        )

        # Average group session rating
        avg_rating_row = self.db.execute_query_one(
            """
            SELECT AVG(sr.rating) as avg_rating, COUNT(sr.id) as review_count
            FROM session_reviews sr
            JOIN study_sessions s ON sr.session_id = s.id
            WHERE s.group_id = ?
            """,
            (group_id,),
        )
        avg_rating = round(avg_rating_row["avg_rating"], 2) if avg_rating_row["avg_rating"] else 0.0

        return {
            "group_id": group_id,
            "group_name": group["name"],
            "course_code": group["course_code"],
            "total_members": members_count,
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "scheduled_sessions": session_stats["scheduled_sessions"] or 0,
            "cancelled_sessions": session_stats["cancelled_sessions"] or 0,
            "total_rsvps": total_rsvps,
            "total_attended": total_attended,
            "attendance_rate_percent": attendance_rate,
            "total_resources": res_stats["total_resources"] or 0,
            "total_resource_downloads": res_stats["total_downloads"] or 0,
            "average_satisfaction_rating": avg_rating,
            "total_reviews": avg_rating_row["review_count"] or 0,
        }

    def get_student_academic_summary(self, user_id: int) -> Dict[str, Any]:
        """Summarizes an individual student's learning engagement."""
        user = self.db.execute_query_one("SELECT * FROM users WHERE id = ?", (user_id,))
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found.")

        # Groups joined
        groups_count = self.db.execute_query_one(
            "SELECT COUNT(*) as c FROM group_members WHERE user_id = ? AND status = 'ACTIVE'",
            (user_id,),
        )["c"]

        # Attendance stats
        att_row = self.db.execute_query_one(
            """
            SELECT 
                COUNT(*) as rsvps,
                SUM(CASE WHEN status = 'ATTENDED' THEN 1 ELSE 0 END) as attended
            FROM session_attendance
            WHERE user_id = ?
            """,
            (user_id,),
        )
        rsvps = att_row["rsvps"] or 0
        attended = att_row["attended"] or 0
        att_rate = round((attended / rsvps) * 100, 1) if rsvps > 0 else 0.0

        # Resources uploaded
        resources_uploaded = self.db.execute_query_one(
            "SELECT COUNT(*) as c FROM study_resources WHERE uploader_id = ?", (user_id,)
        )["c"]

        # Sessions hosted
        sessions_hosted = self.db.execute_query_one(
            "SELECT COUNT(*) as c FROM study_sessions WHERE host_id = ?", (user_id,)
        )["c"]

        return {
            "user_id": user_id,
            "full_name": user["full_name"],
            "role": user["role"],
            "department": user["department"],
            "groups_joined": groups_count,
            "sessions_hosted": sessions_hosted,
            "sessions_rsvpd": rsvps,
            "sessions_attended": attended,
            "attendance_rate_percent": att_rate,
            "resources_shared": resources_uploaded,
        }

    def generate_text_report(self, group_id: int) -> str:
        """Generates a formatted ASCII summary report for academic review."""
        data = self.get_group_analytics(group_id)
        border = "=" * 60
        sub_border = "-" * 60

        report = f"""
{border}
         CAMPUSHUB ACADEMIC STUDY GROUP ANALYTICS REPORT
{border}
Group Name       : {data['group_name']}
Course Code      : {data['course_code']}
Active Members   : {data['total_members']}
{sub_border}
SESSION PERFORMANCE METRICS:
  * Total Sessions Created : {data['total_sessions']}
  * Completed Sessions     : {data['completed_sessions']}
  * Currently Scheduled    : {data['scheduled_sessions']}
  * Cancelled Sessions     : {data['cancelled_sessions']}
{sub_border}
ATTENDANCE & ENGAGEMENT:
  * Total Member RSVPs     : {data['total_rsvps']}
  * Verified Attendances   : {data['total_attended']}
  * Attendance Rate        : {data['attendance_rate_percent']}%
{sub_border}
RESOURCE SHARING & COLLABORATION:
  * Total Materials Uploaded : {data['total_resources']}
  * Material Access Count    : {data['total_resource_downloads']}
{sub_border}
QUALITY & PEER EVALUATION:
  * Average Satisfaction   : {data['average_satisfaction_rating']} / 5.0
  * Reviews Evaluated      : {data['total_reviews']}
{border}
Generated by CampusHub Analytics Engine
"""
        return report.strip()
