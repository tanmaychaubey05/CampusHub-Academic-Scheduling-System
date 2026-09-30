"""
Unit tests for AnalyticsService (Module 3).
"""

import unittest
from campushub.database.db_manager import DatabaseManager
from campushub.services.auth_service import AuthService
from campushub.services.group_service import GroupService
from campushub.services.scheduler_service import SchedulerService
from campushub.services.analytics_service import AnalyticsService
from campushub.utils.exceptions import ValidationError, DuplicateEntityError


class TestAnalyticsService(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager(":memory:")
        self.auth_svc = AuthService(self.db)
        self.group_svc = GroupService(self.db)
        self.sched_svc = SchedulerService(self.db)
        self.anal_svc = AnalyticsService(self.db)

        self.tutor = self.auth_svc.register(
            "tutor_mark", "mark@univ.edu", "pass123Word", "Mark Vance", "TUTOR"
        )
        self.student = self.auth_svc.register(
            "student_lisa", "lisa@univ.edu", "pass123Word", "Lisa Ray", "STUDENT"
        )

        self.group = self.group_svc.create_group(
            self.tutor.id, "Computer Networks Circle", "CSE3004"
        )
        self.group_svc.join_group(self.group.id, self.student.id)

        self.session = self.sched_svc.schedule_session(
            group_id=self.group.id,
            host_id=self.tutor.id,
            title="Subnetting & CIDR",
            description="IPv4 Subnet mask calculation",
            location_or_link="Room 302",
            start_time_str="2026-10-20 15:00",
            end_time_str="2026-10-20 16:30",
        )

    def test_submit_peer_review_and_rating(self):
        rev = self.anal_svc.submit_review(
            session_id=self.session.id,
            reviewer_id=self.student.id,
            rating=5,
            comments="Very clear explanation of VLSM subnetting!",
            reviewee_id=self.tutor.id,
        )
        self.assertIsNotNone(rev.id)
        self.assertEqual(rev.rating, 5)

        # Duplicate review prevention
        with self.assertRaises(DuplicateEntityError):
            self.anal_svc.submit_review(
                session_id=self.session.id,
                reviewer_id=self.student.id,
                rating=4,
                comments="Trying to review again",
            )

    def test_self_review_prohibition(self):
        # Host cannot rate self
        with self.assertRaises(ValidationError):
            self.anal_svc.submit_review(
                session_id=self.session.id,
                reviewer_id=self.tutor.id,
                rating=5,
                comments="Rating myself 5 stars",
                reviewee_id=self.tutor.id,
            )

    def test_group_analytics_metrics(self):
        # Student marks attendance
        self.sched_svc.rsvp_session(self.session.id, self.student.id)
        self.sched_svc.mark_attendance(self.session.id, self.student.id)

        # Submit review
        self.anal_svc.submit_review(
            session_id=self.session.id,
            reviewer_id=self.student.id,
            rating=4,
            comments="Good session",
            reviewee_id=self.tutor.id,
        )

        analytics = self.anal_svc.get_group_analytics(self.group.id)
        self.assertEqual(analytics["total_sessions"], 1)
        self.assertEqual(analytics["total_members"], 2)
        self.assertGreaterEqual(analytics["attendance_rate_percent"], 50.0)
        self.assertEqual(analytics["average_satisfaction_rating"], 4.0)

    def test_academic_summary_generation(self):
        summary = self.anal_svc.get_student_academic_summary(self.student.id)
        self.assertEqual(summary["user_id"], self.student.id)
        self.assertEqual(summary["groups_joined"], 1)


if __name__ == "__main__":
    unittest.main()
