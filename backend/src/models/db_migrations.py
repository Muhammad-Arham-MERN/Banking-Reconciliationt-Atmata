# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Database migration SQL statements
Creates Auth.js adapter tables + custom tables
"""
from typing import List

# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ

# Auth.js adapter tables (auto-creation fallback)
CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),
    emailVerified TIMESTAMPTZ,
    image TEXT
);
"""

CREATE_ACCOUNTS = """
CREATE TABLE IF NOT EXISTS accounts (
    id SERIAL PRIMARY KEY,
    userId INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(255) NOT NULL,
    provider VARCHAR(255) NOT NULL,
    providerAccountId VARCHAR(255) NOT NULL,
    refresh_token TEXT,
    access_token TEXT,
    expires_at BIGINT,
    id_token TEXT,
    scope TEXT,
    session_state TEXT,
    token_type TEXT
);
"""

CREATE_SESSIONS = """
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    userId INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires TIMESTAMPTZ NOT NULL,
    sessionToken VARCHAR(255) NOT NULL
);
"""

CREATE_VERIFICATION_TOKENS = """
CREATE TABLE IF NOT EXISTS verification_token (
    identifier TEXT NOT NULL,
    expires TIMESTAMPTZ NOT NULL,
    token TEXT NOT NULL,
    PRIMARY KEY (identifier, token)
);
"""

# Custom table
CREATE_RECONCILIATION_DATA = """
CREATE TABLE IF NOT EXISTS reconciliation_data (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) UNIQUE NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

# Column additions
ALTER_USERS_ADD_FILES = """
ALTER TABLE users ADD COLUMN IF NOT EXISTS files JSONB DEFAULT '[]'::jsonb;
"""

ALTER_RECONCILIATION_ADD_USER_ID = """
ALTER TABLE reconciliation_data
ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id);
"""

CREATE_IDX_RECONCILIATION_USER_ID = """
CREATE INDEX IF NOT EXISTS idx_reconciliation_data_user_id
ON reconciliation_data(user_id);
"""

# Ordered migration statements
MIGRATIONS: List[str] = [
    CREATE_USERS,
    CREATE_ACCOUNTS,
    CREATE_SESSIONS,
    CREATE_VERIFICATION_TOKENS,
    CREATE_RECONCILIATION_DATA,
    ALTER_USERS_ADD_FILES,
    ALTER_RECONCILIATION_ADD_USER_ID,
    CREATE_IDX_RECONCILIATION_USER_ID,
]

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
