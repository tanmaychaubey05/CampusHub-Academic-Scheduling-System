"""
Unit tests for GroupService (Module 1).
"""

import unittest
from campushub.database.db_manager import DatabaseManager
from campushub.services.auth_service import AuthService
from campushub.services.group_service import GroupService
from campushub.utils.exceptions import ValidationError, DuplicateEntityError


class TestGroupService(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager(":memory:")
        self.auth_svc = AuthService(self.db)
        self.group_svc = GroupService(self.db)

        self.leader = self.auth_svc.register(
            "leader1", "leader@univ.edu", "pass123Word", "Group Leader", "STUDENT"
        )
        self.student = self.auth_svc.register(
            "student2", "student2@univ.edu", "pass123Word", "Bob Smith", "STUDENT"
        )

    def test_create_group_and_leader_assignment(self):
        grp = self.group_svc.create_group(
            creator_id=self.leader.id,
            name="Data Structures Circle",
            course_code="CSE2001",
            description="Linked lists and trees",
            max_members=15,
        )
        self.assertIsNotNone(grp.id)
        self.assertEqual(grp.creator_id, self.leader.id)
        self.assertEqual(grp.member_count, 1)

        members = self.group_svc.get_group_members(grp.id)
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0].role_in_group, "LEADER")

    def test_join_public_group(self):
        grp = self.group_svc.create_group(
            creator_id=self.leader.id,
            name="Web Tech Study Group",
            course_code="CSE3002",
            is_private=False,
        )
        mem = self.group_svc.join_group(grp.id, self.student.id)
        self.assertEqual(mem.status, "ACTIVE")

        # Duplicate join attempt
        with self.assertRaises(DuplicateEntityError):
            self.group_svc.join_group(grp.id, self.student.id)

    def test_join_private_group_and_approval(self):
        grp = self.group_svc.create_group(
            creator_id=self.leader.id,
            name="Advanced ML Research",
            course_code="CSE4001",
            is_private=True,
        )
        mem = self.group_svc.join_group(grp.id, self.student.id)
        self.assertEqual(mem.status, "PENDING")

        # Leader approves
        self.group_svc.approve_membership(grp.id, self.student.id, self.leader.id)
        updated_mem = self.group_svc.get_membership(grp.id, self.student.id)
        self.assertEqual(updated_mem.status, "ACTIVE")

    def test_capacity_constraint_enforcement(self):
        grp = self.group_svc.create_group(
            creator_id=self.leader.id,
            name="Small Seminar",
            course_code="CSE1001",
            max_members=2,  # Leader + 1 member
        )
        self.group_svc.join_group(grp.id, self.student.id)

        user3 = self.auth_svc.register(
            "student3", "student3@univ.edu", "pass123Word", "Charlie", "STUDENT"
        )
        with self.assertRaises(ValidationError):
            self.group_svc.join_group(grp.id, user3.id)


if __name__ == "__main__":
    unittest.main()
