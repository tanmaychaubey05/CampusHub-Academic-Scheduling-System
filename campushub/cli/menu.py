"""
Interactive Command-Line Application for CampusHub.
Implements menus, user navigation, role switching, and operations.
"""

import sys
from typing import Optional
from campushub.database.db_manager import DatabaseManager, get_db
from campushub.models.user import User, UserRole
from campushub.models.resource import ResourceType
from campushub.services.auth_service import AuthService
from campushub.services.group_service import GroupService
from campushub.services.scheduler_service import SchedulerService
from campushub.services.resource_service import ResourceService
from campushub.services.analytics_service import AnalyticsService
from campushub.services.integrity_service import IntegrityService
from campushub.cli.terminal_ui import TerminalUI as UI
from campushub.utils.exceptions import CampusHubException


class CampusHubCLI:
    """Main CLI Controller orchestrating user journeys across modules."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or get_db()
        self.auth_svc = AuthService(self.db)
        self.group_svc = GroupService(self.db)
        self.sched_svc = SchedulerService(self.db)
        self.res_svc = ResourceService(self.db)
        self.anal_svc = AnalyticsService(self.db)
        self.integ_svc = IntegrityService()
        self.current_user: Optional[User] = None

    def run(self) -> None:
        """Main execution loop."""
        while True:
            if not self.current_user:
                self._auth_menu()
            else:
                self._main_dashboard()

    # ==========================================
    # 1. AUTHENTICATION & ONBOARDING
    # ==========================================
    def _auth_menu(self) -> None:
        UI.print_header("CAMPUSHUB", "Academic Resource & Study Group Scheduling System")
        options = [
            "Log In",
            "Register New Student / Tutor",
            "Populate Sample Demonstration Data (1-Click Setup)",
            "Exit Application",
        ]
        choice = UI.prompt_choice(options, "Welcome to CampusHub")

        if choice == 1:
            self._handle_login()
        elif choice == 2:
            self._handle_register()
        elif choice == 3:
            self._seed_sample_data()
        elif choice == 4:
            print("\nThank you for using CampusHub. Goodbye!\n")
            sys.exit(0)

    def _handle_login(self) -> None:
        UI.print_header("USER LOGIN")
        ident = UI.prompt_input("Username or Email")
        pwd = UI.prompt_input("Password")
        try:
            user = self.auth_svc.login(ident, pwd)
            self.current_user = user
            UI.print_success(f"Welcome back, {user.full_name} ({user.role})!")
        except CampusHubException as e:
            UI.print_error(str(e))

    def _handle_register(self) -> None:
        UI.print_header("CREATE NEW ACCOUNT")
        username = UI.prompt_input("Username")
        full_name = UI.prompt_input("Full Name")
        email = UI.prompt_input("Email (e.g. user@univ.edu)")
        password = UI.prompt_input("Password (min 6 chars, alphanumeric)")
        department = UI.prompt_input("Department", default="Computer Science & Engineering")

        role_choice = UI.prompt_choice(
            ["Student", "Tutor / Peer Mentor"], "Select Account Role"
        )
        role = UserRole.STUDENT.value if role_choice == 1 else UserRole.TUTOR.value

        try:
            user = self.auth_svc.register(
                username=username,
                email=email,
                password=password,
                full_name=full_name,
                role=role,
                department=department,
            )
            self.current_user = user
            UI.print_success(f"Registration successful! Logged in as {user.full_name}.")
        except CampusHubException as e:
            UI.print_error(str(e))

    def _seed_sample_data(self) -> None:
        """Populates comprehensive sample data for immediate testing and presentation."""
        try:
            # Users
            tutor = self.auth_svc.register(
                "arjun_tutor", "arjun@univ.edu", "pass123", "Arjun Sharma", UserRole.TUTOR.value, "CSE"
            )
            student1 = self.auth_svc.register(
                "tanmay_s", "tanmay@univ.edu", "pass123", "Tanmay Chaubey", UserRole.STUDENT.value, "CSE"
            )
            student2 = self.auth_svc.register(
                "priya_k", "priya@univ.edu", "pass123", "Priya Kumar", UserRole.STUDENT.value, "ECE"
            )

            # Groups
            grp1 = self.group_svc.create_group(
                tutor.id, "Algorithms & DS Mastery", "CSE2001", "Advanced algorithm practice and leetcode discussions."
            )
            grp2 = self.group_svc.create_group(
                student1.id, "Database Systems & SQL Lab", "CSE3002", "Relational database concepts and indexing."
            )

            # Join
            self.group_svc.join_group(grp1.id, student1.id)
            self.group_svc.join_group(grp1.id, student2.id)
            self.group_svc.join_group(grp2.id, student2.id)

            # Sessions
            s1 = self.sched_svc.schedule_session(
                group_id=grp1.id,
                host_id=tutor.id,
                title="Dynamic Programming Deep Dive",
                description="Solving Knapsack, LCS, and Matrix Chain Multiplication.",
                location_or_link="SJT-401 / meet.google.com/dsa-study",
                start_time_str="2026-10-01 10:00",
                end_time_str="2026-10-01 12:00",
            )
            self.sched_svc.rsvp_session(s1.id, student1.id)
            self.sched_svc.rsvp_session(s1.id, student2.id)
            self.sched_svc.mark_attendance(s1.id, student1.id)

            s2 = self.sched_svc.schedule_session(
                group_id=grp2.id,
                host_id=student1.id,
                title="B-Tree Indexing & Normalization",
                description="Discussion on 3NF, BCNF, and query optimization.",
                location_or_link="Library Discussion Room 3",
                start_time_str="2026-10-02 14:00",
                end_time_str="2026-10-02 15:30",
            )
            self.sched_svc.rsvp_session(s2.id, student2.id)

            # Resources
            self.res_svc.upload_resource(
                group_id=grp1.id,
                uploader_id=tutor.id,
                title="DP Cheatsheet & Recurrence Patterns",
                resource_type=ResourceType.NOTES.value,
                file_or_url="https://drive.google.com/dsa-notes.pdf",
                description="Complete reference sheet for tabular and memoized DP.",
                tags="algorithms, dynamic-programming, dsa",
            )
            self.res_svc.upload_resource(
                group_id=grp2.id,
                uploader_id=student1.id,
                title="SQL Query Optimization Lab Manual",
                resource_type=ResourceType.CODE.value,
                file_or_url="https://github.com/campus/db-lab.git",
                description="Schema definitions and indexing scripts.",
                tags="database, sql, indexing, lab",
            )

            # Reviews
            self.anal_svc.submit_review(
                session_id=s1.id,
                reviewer_id=student1.id,
                rating=5,
                comments="Exceptional breakdown of Knapsack DP states! Very helpful.",
                reviewee_id=tutor.id,
            )

            UI.print_success("Demonstration dataset seeded successfully! (Accounts: arjun_tutor, tanmay_s, priya_k | pass123)")
        except Exception as e:
            UI.print_warning(f"Demo data may already be seeded: {e}")

    # ==========================================
    # 2. MAIN DASHBOARD
    # ==========================================
    def _main_dashboard(self) -> None:
        user = self.current_user
        UI.print_header(
            "CAMPUSHUB DASHBOARD",
            f"User: {user.full_name} | Role: {user.role} | Dept: {user.department}",
        )
        options = [
            "Study Group Management (Module 1: Browse, Create, Join, Manage)",
            "Session Scheduler & Attendance (Module 2: Book Sessions, RSVP, Check-in)",
            "Academic Resource Repository (Search & Share Study Materials)",
            "Peer Review & Analytics Engine (Module 3: Reports & Feedback)",
            "Academic Integrity Suite (Plagiarism & AI Code Detector)",
            "View My Personal Academic Profile",
            "Log Out",
        ]
        choice = UI.prompt_choice(options, "Select Feature Module")

        if choice == 1:
            self._groups_menu()
        elif choice == 2:
            self._scheduler_menu()
        elif choice == 3:
            self._resources_menu()
        elif choice == 4:
            self._analytics_menu()
        elif choice == 5:
            self._integrity_menu()
        elif choice == 6:
            self._view_my_profile()
        elif choice == 7:
            UI.print_info(f"User {user.username} logged out.")
            self.current_user = None

    # ==========================================
    # MODULE 1: STUDY GROUP MANAGEMENT
    # ==========================================
    def _groups_menu(self) -> None:
        UI.print_header("STUDY GROUP MANAGEMENT (MODULE 1)")
        options = [
            "Browse All Public Study Groups",
            "Search Groups by Course Code",
            "Create a New Study Group",
            "View My Enrolled Groups",
            "View Members of a Group",
            "Join a Study Group",
            "Review Pending Join Requests (Group Leaders)",
            "Return to Main Dashboard",
        ]
        choice = UI.prompt_choice(options, "Group Management Options")

        if choice == 1:
            self._browse_groups()
        elif choice == 2:
            course = UI.prompt_input("Enter Course Code (e.g. CSE2001)")
            self._browse_groups(course_code=course)
        elif choice == 3:
            self._create_group()
        elif choice == 4:
            self._view_my_groups()
        elif choice == 5:
            self._view_group_members()
        elif choice == 6:
            self._join_group()
        elif choice == 7:
            self._manage_pending_requests()

    def _browse_groups(self, course_code: Optional[str] = None) -> None:
        groups = self.group_svc.list_groups(course_code=course_code)
        headers = ["ID", "Name", "Course", "Creator", "Members", "Access"]
        rows = [
            [
                g.id,
                g.name,
                g.course_code,
                g.creator_name or "N/A",
                f"{g.member_count}/{g.max_members}",
                "Private" if g.is_private else "Public",
            ]
            for g in groups
        ]
        UI.print_table(headers, rows)

    def _create_group(self) -> None:
        UI.print_header("CREATE STUDY GROUP")
        name = UI.prompt_input("Group Name")
        course = UI.prompt_input("Course Code (e.g. CSE2001)")
        desc = UI.prompt_input("Description / Syllabus Focus")
        cap = UI.prompt_input("Max Member Capacity", default="20")
        is_priv = UI.prompt_choice(["Public (Direct Join)", "Private (Leader Approval Required)"]) == 2

        try:
            grp = self.group_svc.create_group(
                creator_id=self.current_user.id,
                name=name,
                course_code=course,
                description=desc,
                max_members=int(cap),
                is_private=is_priv,
            )
            UI.print_success(f"Study Group '{grp.name}' created with ID: {grp.id}!")
        except CampusHubException as e:
            UI.print_error(str(e))

    def _view_my_groups(self) -> None:
        groups = self.group_svc.get_user_groups(self.current_user.id)
        headers = ["ID", "Group Name", "Course", "Leader", "Members"]
        rows = [[g.id, g.name, g.course_code, g.creator_name, g.member_count] for g in groups]
        UI.print_table(headers, rows)

    def _join_group(self) -> None:
        self._browse_groups()
        grp_id = UI.prompt_input("Enter Group ID to join")
        try:
            mem = self.group_svc.join_group(int(grp_id), self.current_user.id)
            if mem.status == "ACTIVE":
                UI.print_success("Joined group successfully!")
            else:
                UI.print_info("Join request submitted. Awaiting leader approval.")
        except CampusHubException as e:
            UI.print_error(str(e))

    def _view_group_members(self) -> None:
        grp_id = UI.prompt_input("Enter Group ID")
        try:
            members = self.group_svc.get_group_members(int(grp_id))
            headers = ["User ID", "Full Name", "Username", "Role in Group", "Joined At"]
            rows = [[m.user_id, m.full_name, m.username, m.role_in_group, m.joined_at] for m in members]
            UI.print_table(headers, rows)
        except CampusHubException as e:
            UI.print_error(str(e))

    def _manage_pending_requests(self) -> None:
        grp_id = UI.prompt_input("Enter Group ID where you are Leader/Moderator")
        try:
            pending = [
                m for m in self.group_svc.get_group_members(int(grp_id), include_pending=True)
                if m.status == "PENDING"
            ]
            if not pending:
                UI.print_info("No pending join requests for this group.")
                return

            headers = ["User ID", "Full Name", "Username", "Status", "Requested At"]
            rows = [[p.user_id, p.full_name, p.username, p.status, p.joined_at] for p in pending]
            UI.print_table(headers, rows)

            target_uid = UI.prompt_input("Enter User ID to review")
            action = UI.prompt_choice(["Approve", "Reject"], "Select Action")
            if action == 1:
                self.group_svc.approve_membership(int(grp_id), int(target_uid), self.current_user.id)
                UI.print_success(f"User {target_uid} approved into group!")
            else:
                self.group_svc.reject_membership(int(grp_id), int(target_uid), self.current_user.id)
                UI.print_info(f"User {target_uid} request rejected.")
        except CampusHubException as e:
            UI.print_error(str(e))

    # ==========================================
    # MODULE 2: SESSION SCHEDULER
    # ==========================================
    def _scheduler_menu(self) -> None:
        UI.print_header("SESSION SCHEDULER & ATTENDANCE (MODULE 2)")
        options = [
            "Schedule a New Study Session (with Algorithmic Conflict Check)",
            "View Upcoming Sessions for My Groups",
            "View Sessions for a Specific Group",
            "RSVP / Reserve a Spot in a Session",
            "Check-In / Mark Verified Attendance",
            "Complete a Session (Host Only)",
            "Return to Main Dashboard",
        ]
        choice = UI.prompt_choice(options, "Scheduler Options")

        if choice == 1:
            self._schedule_session()
        elif choice == 2:
            self._view_my_upcoming_sessions()
        elif choice == 3:
            grp_id = UI.prompt_input("Enter Group ID")
            try:
                sessions = self.sched_svc.list_sessions_for_group(int(grp_id))
                self._display_sessions_table(sessions)
            except CampusHubException as e:
                UI.print_error(str(e))
        elif choice == 4:
            self._rsvp_session()
        elif choice == 5:
            self._check_in_attendance()
        elif choice == 6:
            self._complete_session()

    def _schedule_session(self) -> None:
        UI.print_header("SCHEDULE STUDY SESSION")
        grp_id = UI.prompt_input("Target Group ID")
        title = UI.prompt_input("Session Topic / Title")
        desc = UI.prompt_input("Description / Agenda")
        loc = UI.prompt_input("Location or Meeting URL (e.g. SJT-401 or meet.google.com/xyz)")
        start_str = UI.prompt_input("Start Time (YYYY-MM-DD HH:MM)")
        end_str = UI.prompt_input("End Time (YYYY-MM-DD HH:MM)")

        try:
            sess = self.sched_svc.schedule_session(
                group_id=int(grp_id),
                host_id=self.current_user.id,
                title=title,
                description=desc,
                location_or_link=loc,
                start_time_str=start_str,
                end_time_str=end_str,
            )
            UI.print_success(f"Session '{sess.title}' scheduled successfully without conflicts! (ID: {sess.id})")
        except CampusHubException as e:
            UI.print_error(f"Scheduling failed: {e}")

    def _display_sessions_table(self, sessions) -> None:
        headers = ["ID", "Title", "Group", "Host", "Start Time", "End Time", "Status", "RSVPs"]
        rows = [
            [
                s.id,
                s.title,
                s.group_name or s.group_id,
                s.host_name or s.host_id,
                s.start_time,
                s.end_time,
                s.status,
                s.attendee_count,
            ]
            for s in sessions
        ]
        UI.print_table(headers, rows)

    def _view_my_upcoming_sessions(self) -> None:
        sessions = self.sched_svc.list_upcoming_sessions_for_user(self.current_user.id)
        self._display_sessions_table(sessions)

    def _rsvp_session(self) -> None:
        sess_id = UI.prompt_input("Enter Session ID to RSVP")
        try:
            self.sched_svc.rsvp_session(int(sess_id), self.current_user.id)
            UI.print_success(f"Successfully RSVP'd to session {sess_id}!")
        except CampusHubException as e:
            UI.print_error(str(e))

    def _check_in_attendance(self) -> None:
        sess_id = UI.prompt_input("Enter Session ID for Attendance Check-In")
        try:
            record = self.sched_svc.mark_attendance(int(sess_id), self.current_user.id)
            UI.print_success(f"Attendance verified at {record.check_in_time}!")
        except CampusHubException as e:
            UI.print_error(str(e))

    def _complete_session(self) -> None:
        sess_id = UI.prompt_input("Enter Session ID to mark completed")
        try:
            self.sched_svc.complete_session(int(sess_id), self.current_user.id)
            UI.print_success(f"Session {sess_id} marked as completed!")
        except CampusHubException as e:
            UI.print_error(str(e))

    # ==========================================
    # ACADEMIC RESOURCE REPOSITORY
    # ==========================================
    def _resources_menu(self) -> None:
        UI.print_header("ACADEMIC RESOURCE REPOSITORY")
        options = [
            "Search & Browse Resources (By Tag / Keyword)",
            "Upload / Index New Study Material",
            "Download / Access Material (Increments Counter)",
            "Return to Main Dashboard",
        ]
        choice = UI.prompt_choice(options, "Resource Options")

        if choice == 1:
            query = UI.prompt_input("Enter search keyword (or leave blank to view all)")
            tag = UI.prompt_input("Enter tag filter (or leave blank)")
            res_list = self.res_svc.search_resources(search_query=query, tag=tag)
            headers = ["ID", "Title", "Type", "Group", "Tags", "Downloads", "Uploader"]
            rows = [
                [r.id, r.title, r.resource_type, r.group_name, r.tags, r.download_count, r.uploader_name]
                for r in res_list
            ]
            UI.print_table(headers, rows)
        elif choice == 2:
            grp_id = UI.prompt_input("Study Group ID")
            title = UI.prompt_input("Resource Title")
            type_choice = UI.prompt_choice(
                ["Notes", "Past Paper", "Code", "Slides", "Reference"], "Select Resource Type"
            )
            r_types = [ResourceType.NOTES.value, ResourceType.PAST_PAPER.value, ResourceType.CODE.value, ResourceType.SLIDES.value, ResourceType.REFERENCE.value]
            r_type = r_types[type_choice - 1]
            url = UI.prompt_input("File Link / Repository URL")
            desc = UI.prompt_input("Description")
            tags = UI.prompt_input("Tags (comma separated, e.g. dsa, trees, exam)")

            try:
                res = self.res_svc.upload_resource(
                    group_id=int(grp_id),
                    uploader_id=self.current_user.id,
                    title=title,
                    resource_type=r_type,
                    file_or_url=url,
                    description=desc,
                    tags=tags,
                )
                UI.print_success(f"Resource '{res.title}' uploaded successfully! (ID: {res.id})")
            except CampusHubException as e:
                UI.print_error(str(e))
        elif choice == 3:
            rid = UI.prompt_input("Enter Resource ID to Access")
            try:
                res = self.res_svc.get_resource_by_id(int(rid))
                new_count = self.res_svc.record_download(int(rid))
                UI.print_success(f"Accessing: '{res.title}' [{res.resource_type}]")
                print(f"  Location / URL: {res.file_or_url}")
                print(f"  Total Downloads: {new_count}\n")
            except CampusHubException as e:
                UI.print_error(str(e))

    # ==========================================
    # MODULE 3: PEER REVIEW & ANALYTICS
    # ==========================================
    def _analytics_menu(self) -> None:
        UI.print_header("PEER REVIEW & ANALYTICS ENGINE (MODULE 3)")
        options = [
            "Submit Peer Review & Session Rating",
            "Generate Study Group Analytics Report",
            "View Tutor / Peer Mentor Rating Breakdown",
            "Return to Main Dashboard",
        ]
        choice = UI.prompt_choice(options, "Analytics Options")

        if choice == 1:
            sess_id = UI.prompt_input("Enter Session ID")
            rating = UI.prompt_input("Rating (1 to 5 Stars)")
            comments = UI.prompt_input("Feedback Comments")
            try:
                rev = self.anal_svc.submit_review(
                    session_id=int(sess_id),
                    reviewer_id=self.current_user.id,
                    rating=int(rating),
                    comments=comments,
                )
                UI.print_success(f"Review submitted with {rev.rating} stars! Thank you for the feedback.")
            except CampusHubException as e:
                UI.print_error(str(e))
        elif choice == 2:
            grp_id = UI.prompt_input("Enter Group ID for Academic Report")
            try:
                report = self.anal_svc.generate_text_report(int(grp_id))
                print(report)
            except CampusHubException as e:
                UI.print_error(str(e))
        elif choice == 3:
            uid = UI.prompt_input("Enter Tutor / Peer User ID")
            try:
                data = self.anal_svc.get_user_rating_summary(int(uid))
                print(f"\nTUTOR RATING BREAKDOWN (User ID: {uid})")
                print(f"Average Rating : {data['average_rating']} / 5.0")
                print(f"Total Reviews  : {data['total_reviews']}")
                print("Distribution   :")
                for stars in range(5, 0, -1):
                    bar = "★" * stars + "☆" * (5 - stars)
                    print(f"  {bar} : {data['rating_breakdown'][stars]} review(s)")
                print()
            except CampusHubException as e:
                UI.print_error(str(e))

    def _view_my_profile(self) -> None:
        summary = self.anal_svc.get_student_academic_summary(self.current_user.id)
        UI.print_header("MY ACADEMIC LEARNING PROFILE")
        print(f"  Full Name        : {summary['full_name']}")
        print(f"  Role             : {summary['role']}")
        print(f"  Department       : {summary['department']}")
        print(f"  Enrolled Groups  : {summary['groups_joined']}")
        print(f"  Sessions Hosted  : {summary['sessions_hosted']}")
        print(f"  Sessions RSVP'd  : {summary['sessions_rsvpd']}")
        print(f"  Sessions Attended: {summary['sessions_attended']}")
        print(f"  Attendance Rate  : {summary['attendance_rate_percent']}%")
        print(f"  Resources Shared : {summary['resources_shared']}")
        print()

    # ==========================================
    # ACADEMIC INTEGRITY & AI CODE DETECTOR
    # ==========================================
    def _integrity_menu(self) -> None:
        UI.print_header("ACADEMIC INTEGRITY & AI CODE DETECTOR")
        options = [
            "Scan Code for AI Generation Likelihood (AI Code Detector)",
            "Compare Two Code/Text Files for Plagiarism Similarity",
            "Return to Main Dashboard",
        ]
        choice = UI.prompt_choice(options, "Integrity Analysis Tools")

        if choice == 1:
            print("\nEnter or paste code snippet to analyze (end with line 'END'):")
            lines = []
            while True:
                line = input()
                if line.strip() == "END":
                    break
                lines.append(line)
            code_text = "\n".join(lines)
            if not code_text.strip():
                UI.print_error("No code provided for analysis.")
                return

            try:
                res = self.integ_svc.detect_ai_code(code_text)
                UI.print_header("AI CODE DETECTION REPORT")
                print(f"  AI Probability   : {res['ai_probability_percent']}%")
                print(f"  Verdict          : {res['verdict']}")
                m = res['metrics']
                print(f"  Token Count      : {m['token_count']} (Unique: {m['unique_tokens']})")
                print(f"  Shannon Entropy  : {m['shannon_entropy']} bits/token")
                print(f"  Type-Token Ratio : {m['type_token_ratio']}")
                print(f"  Line Variance    : {m['line_length_std_dev']}")
                print(f"  AI Cliche Hits   : {m['ai_cliche_hits']}")
                print()
            except CampusHubException as e:
                UI.print_error(str(e))

        elif choice == 2:
            print("\nEnter or paste Original / Source Code (end with line 'END'):")
            src_lines = []
            while True:
                l = input()
                if l.strip() == "END":
                    break
                src_lines.append(l)
            src_text = "\n".join(src_lines)

            print("\nEnter or paste Comparison / Target Code (end with line 'END'):")
            tgt_lines = []
            while True:
                l = input()
                if l.strip() == "END":
                    break
                tgt_lines.append(l)
            tgt_text = "\n".join(tgt_lines)

            try:
                res = self.integ_svc.calculate_plagiarism(src_text, tgt_text)
                UI.print_header("PLAGIARISM ANALYSIS REPORT")
                print(f"  Similarity Index : {res['similarity_percentage']}% (Jaccard)")
                print(f"  Containment      : {res['containment_percentage']}%")
                print(f"  Verdict          : {res['verdict']}")
                print(f"  Matched Hashes   : {res['matching_fingerprints']}")
                print()
            except CampusHubException as e:
                UI.print_error(str(e))

