# Project Statement: CampusHub

## 1. Problem Statement
Every semester, engineering students struggle to coordinate peer study groups and share course materials efficiently. While studying together is one of the best ways to crack difficult technical subjects like Data Structures, Operating Systems, and DBMS, students constantly run into four practical problems:

1. **Messy WhatsApp and Telegram Groups**: Study groups get buried in general chat feeds. Important session timings, meeting links, and problem agendas get scrolled away, and people constantly ask "when is the session happening?"
2. **Scheduling Collisions & Tutor Double-Booking**: Peer tutors teaching multiple junior batches often accidentally commit to overlapping review slots on the same evening, leading to last-minute delays or cancellations.
3. **Scattered Course Materials**: Previous year exam solutions, lecture notes, lab sheets, and code snippets are shared across random Google Drive links. By exam week, links expire, permissions get revoked, or files are impossible to search by course code or topic tag.
4. **No Participation Tracking or Quality Checks**: Nobody keeps track of who actually attended the study session or whether the peer tutor did a good job explaining the concepts.

**CampusHub** solves these pain points by giving students and tutors a single centralized platform to manage course study circles, schedule conflict-free review sessions with automated overlap checking, catalog verified study materials, and track attendance with peer reviews.

---

## 2. Scope of the Project
CampusHub is designed as a modular, lightweight academic system for university course batches:

### What the System Delivers:
- **Student & Tutor Authentication**: User sign-up with email validation, password checks, and secure PBKDF2 SHA-256 password hashing.
- **Course Study Groups**: Create and browse study groups by course code (e.g. CSE2001, MAT2002) with capacity limits. Public groups allow direct joining; private groups require leader approval.
- **Conflict-Free Session Scheduler**: Uses mathematical interval collision checks `(startA < endB and endA > startB)` to guarantee that tutors and groups are never booked for overlapping time slots.
- **Attendance Verification**: RSVP seat reservation followed by attendance check-in timestamps.
- **Academic Resource Catalog**: Upload and tag cheatsheets, past papers, lab code, and presentation slides with download counters.
- **Peer Feedback & Performance Analytics**: 5-star ratings and written reviews for tutors, attendance percentage tracking, and formatted performance dossiers.
- **Academic Integrity Engine**: Built-in plagiarism comparison (token winnowing) and AI code detection heuristics to ensure shared materials are original and self-written.
- **Dual User Interfaces**: Interactive command-line terminal interface (CLI) and a clean web dashboard running on Python's built-in HTTP server.

### System Boundaries:
- Video meetings are conducted through external links (Google Meet, Zoom, MS Teams) or physical classroom locations rather than built-in media streaming servers.
- The project focuses on peer study collaboration within campus departments without commercial payment gateways.

---

## 3. Target Users
1. **Undergraduate Students**: Students looking for active study partners to prepare for quizzes, lab exams, and final exams.
2. **Peer Tutors & Mentors**: Senior students conducting doubt-clearing sessions and revision classes who need conflict-free scheduling and feedback records.
3. **Group Leaders & Class Representatives**: Organizers managing course study circles, approving join requests, and curating syllabus materials.
4. **Faculty Advisors & Course Coordinators**: Instructors reviewing peer group attendance and engagement reports across course batches.

---

## 4. Key Functional Modules
| Module Name | Core Features |
| :--- | :--- |
| **Module 1: User & Study Group Management** | Multi-role user login (Student, Tutor, Admin), salted password security, course code indexing, private group approval queues, and capacity limits. |
| **Module 2: Session Scheduler & Attendance** | Mathematical interval collision checks, slot booking, RSVP reservations, and verified check-in timestamps. |
| **Academic Resource Repository** | 5 resource categories (Notes, Papers, Code, Slides, References), tag-based multi-criteria search, and download auditing. |
| **Module 3: Peer Review & Analytics** | 5-star review system, anti-self-rating safeguards, attendance percentage calculation, and automated group summary reports. |
| **Academic Integrity Engine** | MOSS-style token fingerprinting for plagiarism similarity, and multi-signal AI code detection heuristics. |
| **Dual Access Interfaces** | Formatted ANSI/ASCII Terminal CLI and zero-dependency local web dashboard. |
