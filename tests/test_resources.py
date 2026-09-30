"""
Unit tests for ResourceService.
"""

import unittest
from campushub.database.db_manager import DatabaseManager
from campushub.services.auth_service import AuthService
from campushub.services.group_service import GroupService
from campushub.services.resource_service import ResourceService
from campushub.models.resource import ResourceType


class TestResourceService(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager(":memory:")
        self.auth_svc = AuthService(self.db)
        self.group_svc = GroupService(self.db)
        self.res_svc = ResourceService(self.db)

        self.user = self.auth_svc.register(
            "student_res", "res@univ.edu", "pass123Word", "Resource User", "STUDENT"
        )
        self.group = self.group_svc.create_group(
            self.user.id, "Compiler Design Hub", "CSE3003"
        )

    def test_upload_and_search_resource(self):
        res = self.res_svc.upload_resource(
            group_id=self.group.id,
            uploader_id=self.user.id,
            title="Lexical Analyzer Lex Lexemes",
            resource_type=ResourceType.NOTES.value,
            file_or_url="https://drive.google.com/lex.pdf",
            description="Grammars and tokens cheatsheet",
            tags="compiler, lexical, tokens",
        )
        self.assertIsNotNone(res.id)
        self.assertEqual(res.title, "Lexical Analyzer Lex Lexemes")

        # Search by tag
        results = self.res_svc.search_resources(tag="lexical")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, res.id)

        # Download counter
        count1 = self.res_svc.record_download(res.id)
        self.assertEqual(count1, 1)
        count2 = self.res_svc.record_download(res.id)
        self.assertEqual(count2, 2)


if __name__ == "__main__":
    unittest.main()
