"""
Unit tests for SchedulerService (Module 2).
Focuses on algorithmic interval collision detection, RSVP, and attendance.
"""

import unittest
from campushub.database.db_manager import DatabaseManager
from campushub.services.auth_service import AuthService
from campushub.services.group_service import GroupService
from campushub.services.scheduler_service import SchedulerService
from campushub.utils.exceptions import SchedulingConflictError, ValidationError


class TestSchedulerService(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager(":memory:")
        self.auth_svc = AuthService(self.db)
        self.group_svc = GroupService(self.db)
        self.sched_svc = SchedulerService(self.db)

        self.tutor = self.auth_svc.register(
            "tutor_jane", "jane@univ.edu", "pass123Word", "Jane Doe", "TUTOR"
        )
        self.student = self.auth_svc.register(
            "student_bob", "bob@univ.edu", "pass123Word", "Bob Smith", "STUDENT"
        )

        self.group1 = self.group_svc.create_group(
            self.tutor.id, "Discrete Math Group", "MAT2001"
        )
        self.group2 = self.group_svc.create_group(
            self.tutor.id, "Linear Algebra Group", "MAT2002"
        )

        self.group_svc.join_group(self.group1.id, self.student.id)

    def test_schedule_session_success(self):
        sess = self.sched_svc.schedule_session(
            group_id=self.group1.id,
            host_id=self.tutor.id,
            title="Graph Theory Basics",
            description="Eulerian and Hamiltonian circuits",
            location_or_link="Room SJT-101",
            start_time_str="2026-10-10 10:00",
            end_time_str="2026-10-10 11:30",
        )
        self.assertIsNotNone(sess.id)
        self.assertEqual(sess.title, "Graph Theory Basics")
        self.assertEqual(sess.attendee_count, 1)  # Host auto-RSVP

    def test_host_conflict_detection_algorithm(self):
        """
        Verify that if Tutor Jane has a session 10:00-11:30 in Group 1,
        she cannot schedule an overlapping session in Group 2 (e.g. 11:00-12:00).
        """
        self.sched_svc.schedule_session(
            group_id=self.group1.id,
            host_id=self.tutor.id,
            title="Session 1",
            description="",
            location_or_link="Room 101",
            start_time_str="2026-10-10 10:00",
            end_time_str="2026-10-10 11:30",
        )

        # Overlapping slot: 11:00 to 12:00
        with self.assertRaises(SchedulingConflictError):
            self.sched_svc.schedule_session(
                group_id=self.group2.id,
                host_id=self.tutor.id,
                title="Session 2 (Clashing)",
                description="",
                location_or_link="Room 102",
                start_time_str="2026-10-10 11:00",
                end_time_str="2026-10-10 12:00",
            )

    def test_group_conflict_detection(self):
        """Verify that a group cannot have two sessions scheduled at the same time."""
        # Tutor schedules session 1 in Group 1
        self.sched_svc.schedule_session(
            group_id=self.group1.id,
            host_id=self.tutor.id,
            title="Group Session A",
            description="",
            location_or_link="Room 101",
            start_time_str="2026-10-12 14:00",
            end_time_str="2026-10-12 15:00",
        )

        # Student tries to schedule another session in Group 1 for the same slot
        with self.assertRaises(SchedulingConflictError):
            self.sched_svc.schedule_session(
                group_id=self.group1.id,
                host_id=self.student.id,
                title="Group Session B (Clashing)",
                description="",
                location_or_link="Room 102",
                start_time_str="2026-10-12 14:15",
                end_time_str="2026-10-12 14:45",
            )

    def test_invalid_time_windows(self):
        # End time before start time
        with self.assertRaises(ValidationError):
            self.sched_svc.schedule_session(
                group_id=self.group1.id,
                host_id=self.tutor.id,
                title="Invalid Time",
                description="",
                location_or_link="Room 101",
                start_time_str="2026-10-10 14:00",
                end_time_str="2026-10-10 13:00",
            )

        # Duration under 15 minutes
        with self.assertRaises(ValidationError):
            self.sched_svc.schedule_session(
                group_id=self.group1.id,
                host_id=self.tutor.id,
                title="Too short",
                description="",
                location_or_link="Room 101",
                start_time_str="2026-10-10 14:00",
                end_time_str="2026-10-10 14:05",
            )

    def test_rsvp_and_attendance_checkin(self):
        sess = self.sched_svc.schedule_session(
            group_id=self.group1.id,
            host_id=self.tutor.id,
            title="Recurrence Relations",
            description="",
            location_or_link="Online",
            start_time_str="2026-10-15 09:00",
            end_time_str="2026-10-15 10:00",
        )

        # RSVP
        rec = self.sched_svc.rsvp_session(sess.id, self.student.id)
        self.assertEqual(rec.status, "RSVP")

        # Check in attendance
        att = self.sched_svc.mark_attendance(sess.id, self.student.id)
        self.assertEqual(att.status, "ATTENDED")
        self.assertIsNotNone(att.check_in_time)


if __name__ == "__main__":
    unittest.main()
