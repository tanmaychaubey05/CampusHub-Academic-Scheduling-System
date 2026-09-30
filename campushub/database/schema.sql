-- CampusHub Database Schema
-- Relational Schema with Foreign Keys and Indexes

PRAGMA foreign_keys = ON;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('STUDENT', 'TUTOR', 'ADMIN')),
    department TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Study Groups Table
CREATE TABLE IF NOT EXISTS study_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    course_code TEXT NOT NULL,
    description TEXT,
    creator_id INTEGER NOT NULL,
    max_members INTEGER DEFAULT 20,
    is_private INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (creator_id) REFERENCES users (id) ON DELETE CASCADE
);

-- 3. Group Members Table (Many-to-Many with Status)
CREATE TABLE IF NOT EXISTS group_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role_in_group TEXT NOT NULL CHECK(role_in_group IN ('LEADER', 'MEMBER', 'MODERATOR')),
    status TEXT NOT NULL CHECK(status IN ('ACTIVE', 'PENDING', 'REJECTED')),
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(group_id, user_id),
    FOREIGN KEY (group_id) REFERENCES study_groups (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- 4. Study Sessions Table
CREATE TABLE IF NOT EXISTS study_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    host_id INTEGER NOT NULL,
    location_or_link TEXT NOT NULL,
    start_time TEXT NOT NULL, -- Format: YYYY-MM-DD HH:MM
    end_time TEXT NOT NULL,   -- Format: YYYY-MM-DD HH:MM
    status TEXT NOT NULL DEFAULT 'SCHEDULED' CHECK(status IN ('SCHEDULED', 'COMPLETED', 'CANCELLED')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES study_groups (id) ON DELETE CASCADE,
    FOREIGN KEY (host_id) REFERENCES users (id) ON DELETE CASCADE
);

-- 5. Session Attendance Table
CREATE TABLE IF NOT EXISTS session_attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('RSVP', 'ATTENDED', 'ABSENT')),
    check_in_time TIMESTAMP,
    UNIQUE(session_id, user_id),
    FOREIGN KEY (session_id) REFERENCES study_sessions (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- 6. Study Resources Table
CREATE TABLE IF NOT EXISTS study_resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    uploader_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    resource_type TEXT NOT NULL CHECK(resource_type IN ('NOTES', 'PAST_PAPER', 'CODE', 'SLIDES', 'REFERENCE')),
    file_or_url TEXT NOT NULL,
    description TEXT,
    tags TEXT, -- comma-separated tags
    download_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES study_groups (id) ON DELETE CASCADE,
    FOREIGN KEY (uploader_id) REFERENCES users (id) ON DELETE CASCADE
);

-- 7. Session Reviews & Peer Feedback Table
CREATE TABLE IF NOT EXISTS session_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    reviewer_id INTEGER NOT NULL,
    reviewee_id INTEGER, -- Optional: target tutor or group leader
    rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES study_sessions (id) ON DELETE CASCADE,
    FOREIGN KEY (reviewer_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (reviewee_id) REFERENCES users (id) ON DELETE SET NULL
);

-- Indexes for Fast Query Optimization
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_groups_course ON study_groups(course_code);
CREATE INDEX IF NOT EXISTS idx_sessions_times ON study_sessions(start_time, end_time);
CREATE INDEX IF NOT EXISTS idx_resources_group ON study_resources(group_id);
CREATE INDEX IF NOT EXISTS idx_attendance_session ON session_attendance(session_id);
