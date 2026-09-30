# CampusHub: Academic Resource & Peer Study Group Scheduling System

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Testing](https://img.shields.io/badge/tests-23%20passed%20%7C%20100%25-brightgreen.svg)](#instructions-for-testing)
[![Architecture](https://img.shields.io/badge/architecture-modular%20MVC%20%2F%20Service%20Layer-orange.svg)](#system-architecture)
[![Dependencies](https://img.shields.io/badge/dependencies-0%20external%20(Pure%20Python)-success.svg)](#technologiestools-used)

---

## Overview of the Project
**CampusHub** is a modular, high-reliability academic peer collaboration and scheduling system designed for university students, peer mentors, and course study groups. 

In university environments, peer-assisted learning often suffers from disorganized communication channels, scheduling collisions, lost study materials, and unverified participation. **CampusHub** overcomes these challenges through:
1. **Curated Course Study Groups**: Student and tutor driven group spaces with role-based member permissions and approval queues.
2. **Conflict-Free Session Scheduler**: An interval collision detection algorithm that guarantees hosts and groups never double-book overlapping review slots.
3. **Academic Resource Repository**: Tagged categorization and tracking of cheatsheets, past papers, lab code, and lecture slides.
4. **Peer Evaluation & Analytics Engine**: Verified check-ins, attendance percentage metrics, and peer feedback ratings.
5. **Academic Integrity Engine**: Token-based plagiarism fingerprinting (MOSS-style winnowing) and multi-signal AI code detection heuristics.

Built with **pure Python** using clean modular architecture, relational SQLite persistence, and dual presentation layers (Interactive Terminal CLI and Browser Web Dashboard), CampusHub runs out-of-the-box on any computer without requiring third-party package installations.

---

## Features

### 👥 Module 1: User & Study Group Management
- **Role-Based Access Control (RBAC)**: Support for `STUDENT`, `TUTOR`, and `ADMIN` profiles.
- **Cryptographic Security**: Salted PBKDF2 SHA-256 password hashing (100,000 rounds).
- **Group Creation & Governance**: Create public or private study groups indexed by course code (e.g., `CSE2001`, `MAT2002`).
- **Membership Approval Workflow**: Public groups allow instant joining; private groups maintain an approval queue managed by group leaders and moderators.
- **Capacity Constraints**: Enforces maximum member thresholds to keep study cohorts focused and effective.

### 📅 Module 2: Session Scheduler & Conflict Detector
- **Algorithmic Collision Detection**: Applies mathematical interval clash detection:
  $$\text{Overlap} \iff (\text{Start}_A < \text{End}_B) \land (\text{End}_A > \text{Start}_B)$$
  Prevents scheduling clashing sessions for either the host or the group.
- **Session Management**: Title, location/meeting URL, agenda description, start and end timestamps.
- **RSVP & Attendance Verification**: Students reserve seats via RSVP; leaders verify attendance with real-time timestamp check-in.
- **Status Lifecycle**: Transitions smoothly across `SCHEDULED` $\rightarrow$ `COMPLETED` or `CANCELLED`.

### 📚 Academic Resource Repository
- **Multi-Type Categorization**: Classifies materials into `NOTES`, `PAST_PAPER`, `CODE`, `SLIDES`, and `REFERENCE`.
- **Search & Tag Indexing**: Fast multi-criteria search filtering by topic tags, course codes, or keyword strings.
- **Access & Download Metrics**: Tracks document popularity and access frequencies.

### 📊 Module 3: Peer Review & Analytics Engine
- **Peer & Tutor Evaluations**: 1 to 5 star rating scale with qualitative feedback comments.
- **Anti-Self-Rating Safeguards**: System strictly prevents hosts from reviewing themselves.
- **Automated Attendance Ratios**: Real-time calculation of verified attendance percentages:
  $$\text{Attendance Rate} = \left(\frac{\text{Verified Attendees}}{\text{Total RSVPs}}\right) \times 100\%$$
- **Academic Performance Reports**: Generates detailed ASCII and JSON summary reports covering sessions held, member engagement, and satisfaction scores.

### 🛡️ Academic Integrity Suite (Plagiarism & AI Code Detector)
- **Token Winnowing Plagiarism Engine**: Fingerprints token streams with rolling k-grams to calculate Jaccard similarity and containment indices regardless of variable renaming.
- **AI Code Detector**: Measures token entropy, Type-Token Ratio (TTR), line length burstiness variance, and checks for AI boilerplate comment patterns.

---

## Technologies/Tools Used
- **Language**: Python 3.10+ (Tested on Python 3.14)
- **Database**: Relational SQLite3 with Foreign Key constraints and Write-Ahead Logging (WAL)
- **Security**: Cryptographic `hashlib` (PBKDF2 SHA-256), `secrets` module
- **Testing**: Python standard `unittest` framework (23 automated test cases)
- **Presentation**:
  - Interactive Terminal Interface (ANSI / ASCII tables and styled menus)
  - Native Web Dashboard (Built-in `http.server`, HTML5, CSS3, modern Vanilla JavaScript)
- **Version Control**: Git workflow

---

## System Architecture

```
                                  +------------------------------+
                                  |     User / Client Tier       |
                                  |  (Terminal CLI / Web UI)     |
                                  +--------------+---------------+
                                                 |
                                                 v
                                  +------------------------------+
                                  |      Presentation Layer      |
                                  |  (menu.py / web/app.py)      |
                                  +--------------+---------------+
                                                 |
            +------------------------------------+------------------------------------+
            |                                    |                                    |
            v                                    v                                    v
+-----------------------+            +-----------------------+            +-----------------------+
|     Auth Service      |            |  Group & Schedulers   |            |   Analytics Engine    |
| (PBKDF2 Password Hash)|            |  (Interval Collision) |            | (Metrics, Reports)    |
+-----------+-----------+            +-----------+-----------+            +-----------+-----------+
            |                                    |                                    |
            |                        +-----------+-----------+                        |
            |                        |   Integrity Service   |                        |
            |                        | (Plagiarism / AI Code)|                        |
            |                        +-----------+-----------+                        |
            |                                    |                                    |
            +------------------------------------+------------------------------------+
                                                 |
                                                 v
                                  +------------------------------+
                                  |      Database Manager        |
                                  |  (sqlite3 + schema.sql)      |
                                  +--------------+---------------+
                                                 |
                                                 v
                                  +------------------------------+
                                  | Relational SQLite Data Store |
                                  |  (Users, Groups, Sessions,   |
                                  |   Attendance, Resources)     |
                                  +------------------------------+
```

---

## Steps to Install & Run the Project

### Prerequisites
- Python 3.10 or higher installed. (No external pip libraries required!)

### 1. Run the Interactive Terminal Application (Default CLI)
```bash
python main.py
```
> **Quick Start Tip**: Select Option `[3] Populate Sample Demonstration Data (1-Click Setup)` to automatically create demo student accounts (`tanmay_s`, `arjun_tutor`, `priya_k` / password: `pass123`), groups, sessions, and resources!

### 2. Run the Modern Web Dashboard (Browser Interface)
```bash
python main.py --web
```
Open your web browser and navigate to:
```
http://127.0.0.1:8000
```
Use the tabs to browse groups, book sessions, test interval collision errors, search files, run live plagiarism comparisons, and inspect AI code detection scores!

---

## Instructions for Testing
CampusHub includes an automated unit and integration test suite with 23 comprehensive test cases covering authentication security, capacity limits, scheduling conflict detection, analytics, and academic integrity checks.

### Run All Tests via CLI flag:
```bash
python main.py --test
```

### Or Run via the Dedicated Test Runner:
```bash
python run_tests.py
```

### Expected Test Output:
```
=======================================================
 EXECUTING CAMPUSHUB AUTOMATED TEST SUITE
=======================================================

test_academic_summary_generation (test_analytics.TestAnalyticsService) ... ok
test_group_analytics_metrics (test_analytics.TestAnalyticsService) ... ok
test_self_review_prohibition (test_analytics.TestAnalyticsService) ... ok
test_submit_peer_review_and_rating (test_analytics.TestAnalyticsService) ... ok
test_duplicate_username_rejection (test_auth.TestAuthService) ... ok
test_invalid_email_format (test_auth.TestAuthService) ... ok
test_invalid_login_credentials (test_auth.TestAuthService) ... ok
test_successful_registration_and_login (test_auth.TestAuthService) ... ok
test_weak_password_validation (test_auth.TestAuthService) ... ok
test_capacity_constraint_enforcement (test_groups.TestGroupService) ... ok
test_create_group_and_leader_assignment (test_groups.TestGroupService) ... ok
test_join_private_group_and_approval (test_groups.TestGroupService) ... ok
test_join_public_group (test_groups.TestGroupService) ... ok
test_detect_ai_code_markers (test_integrity.TestIntegrityService) ... ok
test_distinct_code_low_similarity (test_integrity.TestIntegrityService) ... ok
test_empty_content_validation (test_integrity.TestIntegrityService) ... ok
test_identical_plagiarism_detection (test_integrity.TestIntegrityService) ... ok
test_upload_and_search_resource (test_resources.TestResourceService) ... ok
test_group_conflict_detection (test_scheduler.TestSchedulerService) ... ok
test_host_conflict_detection_algorithm (test_scheduler.TestSchedulerService) ... ok
test_invalid_time_windows (test_scheduler.TestSchedulerService) ... ok
test_rsvp_and_attendance_checkin (test_scheduler.TestSchedulerService) ... ok
test_schedule_session_success (test_scheduler.TestSchedulerService) ... ok

----------------------------------------------------------------------
Ran 23 tests in 0.742s

OK
```

---

## Directory Structure
```
tanmay/
├── campushub/
│   ├── database/
│   │   ├── db_manager.py        # Connection lifecycle & transactions
│   │   └── schema.sql           # Normalized DDL relational schema
│   ├── models/
│   │   ├── user.py              # User & RBAC roles
│   │   ├── study_group.py       # Group & membership entities
│   │   ├── session.py           # Study session & attendance models
│   │   ├── resource.py          # Academic materials & tags
│   │   └── review.py            # Peer feedback & ratings
│   ├── services/
│   │   ├── auth_service.py      # Registration & salted PBKDF2 hashing
│   │   ├── group_service.py     # Module 1: Study groups & approvals
│   │   ├── scheduler_service.py # Module 2: Conflict-free scheduler
│   │   ├── resource_service.py  # Repository & search indexing
│   │   ├── analytics_service.py # Module 3: Attendance & peer analytics
│   │   └── integrity_service.py # Academic Integrity: Plagiarism & AI detector
│   ├── utils/
│   │   ├── exceptions.py        # Custom domain exceptions
│   │   ├── validators.py        # Data integrity & format validators
│   │   └── logger.py            # Centralized rotating file logger
│   ├── cli/
│   │   ├── menu.py              # Terminal user journeys & integrity tools
│   │   └── terminal_ui.py       # ASCII tables & UI formatters
│   └── web/
│       ├── app.py               # Native HTTP REST API server
│       └── static/              # Dashboard Web UI (HTML5, CSS, JS)
├── tests/
│   ├── test_auth.py             # Auth & security tests
│   ├── test_groups.py           # Group workflow tests
│   ├── test_scheduler.py        # Algorithmic collision detection tests
│   ├── test_resources.py        # Repository & tag search tests
│   ├── test_analytics.py        # Metrics & rating tests
│   └── test_integrity.py        # Plagiarism & AI detection tests
├── docs/
│   ├── PROJECT_REPORT.md        # 15-Section Academic Report (Humanized)
│   ├── report.html              # Printable HTML Report
│   └── PROJECT_REPORT.pdf       # Ready-to-Upload Submission PDF (658 KB)
├── main.py                      # Master application entry point
├── run_tests.py                 # Standalone test runner
├── statement.md                 # Humanized Problem statement & scope
├── requirements.txt             # Dependency specification
└── README.md                    # Project documentation
```

---

## Authors & Acknowledgments
- Developed for **VITyarthi - Build Your Own Project** Course Evaluation.
- Designed strictly according to the syllabus guidelines, evaluation rubric, and software engineering best practices.
