-- PostgreSQL Schema for file storage and LLM-generated tags
-- Run: psql -U <user> -d <database> -f schema.sql

-- Users (Telegram users)
CREATE TABLE IF NOT EXISTS "user" (
    id          INTEGER PRIMARY KEY,      -- Telegram user ID
    username    TEXT NOT NULL DEFAULT ''
);

-- Tags (unique, case-normalized)
CREATE TABLE IF NOT EXISTS tag (
    id          SERIAL PRIMARY KEY,
    name        TEXT UNIQUE NOT NULL
);

-- Files (uploaded files per user)
CREATE TABLE IF NOT EXISTS file (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    file_path   TEXT NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- File-Tags (many-to-many relationship)
CREATE TABLE IF NOT EXISTS file_tag (
    file_id     INTEGER NOT NULL REFERENCES file(id) ON DELETE CASCADE,
    tag_id      INTEGER NOT NULL REFERENCES tag(id) ON DELETE CASCADE,
    PRIMARY KEY (file_id, tag_id)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_file_user_id ON file(user_id);
CREATE INDEX IF NOT EXISTS idx_file_tag_file_id ON file_tag(file_id);
CREATE INDEX IF NOT EXISTS idx_file_tag_tag_id ON file_tag(tag_id);
