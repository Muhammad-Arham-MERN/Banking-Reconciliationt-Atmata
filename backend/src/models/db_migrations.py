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

# Past Reconciliations feature: which ledger type a stored file belongs to.
# Needed so an EMPTY created file still knows whether its four Excel sections
# are the Bank set or the Vendor set (not derivable from zero discrepancy rows).
ALTER_RECONCILIATION_ADD_TYPE = """
ALTER TABLE reconciliation_data
ADD COLUMN IF NOT EXISTS reconciliation_type VARCHAR(20) NOT NULL DEFAULT 'bank';
"""

# ---- Judge Structure by its Cover (pdf structure profiles) -----------------
# Stores previously-extracted PDF structures keyed by normalized entity name +
# entity type ("bank" | "vendor"), so the Judge agent can short-circuit full
# structure detection on repeat uploads from the same bank/vendor. The
# `structure` JSONB holds the full FileStructureOutput contract that
# assess_structure consumes and the deterministic extractor needs.
CREATE_PDF_STRUCTURE_PROFILES = """
CREATE TABLE IF NOT EXISTS pdf_structure_profiles (
    id                     SERIAL PRIMARY KEY,
    entity_name            VARCHAR(255) NOT NULL,
    entity_name_normalized VARCHAR(255) NOT NULL,
    entity_type            VARCHAR(16)  NOT NULL,   -- 'bank' | 'vendor'
    structure              JSONB        NOT NULL,   -- full FileStructureOutput
    created_at             TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at             TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
"""

CREATE_UQ_PDF_STRUCTURE_PROFILE = """
CREATE UNIQUE INDEX IF NOT EXISTS uq_pdf_structure_profile
ON pdf_structure_profiles(entity_name_normalized, entity_type);
"""

CREATE_IDX_PDF_STRUCTURE_PROFILE_TYPE = """
CREATE INDEX IF NOT EXISTS idx_pdf_structure_profile_type
ON pdf_structure_profiles(entity_type);
"""

# ---- Admin Dashboard (Camri Desk) — client companies -----------------------
# Companies onboarded by the Developer from the hidden admin dashboard. This is
# a brand-new domain: no link to `users` (the company-facing login and its
# employee membership are later specs). `password_encrypted` holds a Fernet
# token — the plaintext password is never stored. `payment_status` is constrained
# at the DB level so an out-of-range value can never be persisted.
CREATE_COMPANIES = """
CREATE TABLE IF NOT EXISTS companies (
    id                 SERIAL PRIMARY KEY,
    name               VARCHAR(255) NOT NULL,
    logo_filename      VARCHAR(255),
    password_encrypted TEXT         NOT NULL,
    price_rupees       INTEGER      NOT NULL,
    payment_status     VARCHAR(16)  NOT NULL DEFAULT 'pending',
    created_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_company_payment_status
        CHECK (payment_status IN ('pending', 'free_trial', 'paid')),
    CONSTRAINT chk_company_price_non_negative
        CHECK (price_rupees >= 0)
);
"""

# Case-insensitive uniqueness: the company name doubles as the company's
# identifier for the later company-facing sign-in, so "Acme Ltd" and "acme ltd"
# must not both exist.
CREATE_UQ_COMPANY_NAME_LOWER = """
CREATE UNIQUE INDEX IF NOT EXISTS uq_company_name_lower
ON companies (lower(name));
"""

# ---- Employee Access Request (subscription layer) --------------------------
# Employees who asked a company to grant them access, submitted from the
# subscription page. A dedicated record set, separate from `companies` and from
# the NextAuth `users` accounts. `employee_id` is the `adam-` prefixed handle the
# employee hands to the company; uniqueness is per (employee_id, company_id), so
# one employee may request several companies but never the same one twice.
# `company_name` is a snapshot so the record still reads correctly after a
# rename — and there is deliberately NO foreign key, so the admin's hard delete
# of a company keeps working. The prefix CHECK is the DB-level backstop.
CREATE_EMPLOYEES = """
CREATE TABLE IF NOT EXISTS employees (
    id              SERIAL       PRIMARY KEY,
    employee_name   VARCHAR(255) NOT NULL,
    employee_id     VARCHAR(64)  NOT NULL,
    company_id      INTEGER      NOT NULL,
    company_name    VARCHAR(255) NOT NULL,
    account_user_id INTEGER      NOT NULL,
    account_email   VARCHAR(255) NOT NULL DEFAULT '',
    status          VARCHAR(16)  NOT NULL DEFAULT 'pending',
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_employee_status
        CHECK (status IN ('pending', 'accepted', 'denied')),
    CONSTRAINT chk_employee_id_prefix
        CHECK (employee_id LIKE 'adam-%')
);
"""

# The employee id is stored already lowercased and prefixed, so a plain
# (non-expression) index is enough. Enforcing this in the database rather than
# only in the service means a concurrent second submit cannot slip a duplicate
# through without a transaction.
CREATE_UQ_EMPLOYEE_ID_COMPANY = """
CREATE UNIQUE INDEX IF NOT EXISTS uq_employee_id_company
ON employees (employee_id, company_id);
"""

# ---- Company onboarding requests (view-only admin inbox) --------------------
# A "Company Request" submission from the onboarding flow. Stored purely so the
# Developer can read it in the Admin Dashboard's "Company Requests" category;
# it has NO status lifecycle and NO link to company account creation (companies
# are still onboarded manually after the Developer contacts them). The
# account_* columns are informational snapshots of the signed-in submitter.
CREATE_COMPANY_REQUESTS = """
CREATE TABLE IF NOT EXISTS company_requests (
    id              SERIAL       PRIMARY KEY,
    company_name    VARCHAR(255) NOT NULL,
    role            VARCHAR(255) NOT NULL DEFAULT '',
    website_socials VARCHAR(255) NOT NULL DEFAULT '',
    email           VARCHAR(255) NOT NULL DEFAULT '',
    phone           VARCHAR(64)  NOT NULL DEFAULT '',
    account_user_id INTEGER,
    account_email   VARCHAR(255) NOT NULL DEFAULT '',
    submitted_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
"""

# Newest-first listing is the admin inbox's only read pattern.
CREATE_IDX_COMPANY_REQUESTS_SUBMITTED_AT = """
CREATE INDEX IF NOT EXISTS idx_company_requests_submitted_at
ON company_requests (submitted_at DESC);
"""

# ---- Manager flag on employee records ---------------------------------------
# The Manager designation is additive: it only surfaces the "Company Dashboard"
# navigation entry for an account that already holds accepted employee access
# (FR-019/FR-020). It never grants application access on its own.
ALTER_EMPLOYEES_ADD_IS_MANAGER = """
ALTER TABLE employees ADD COLUMN IF NOT EXISTS is_manager BOOLEAN NOT NULL DEFAULT false;
"""

# Serves the membership gate and the "one active request per account" lookup.
CREATE_IDX_EMPLOYEES_ACCOUNT_USER_ID = """
CREATE INDEX IF NOT EXISTS idx_employees_account_user_id
ON employees (account_user_id);
"""

# Serves the company dashboard employee list and the company-delete cascade.
CREATE_IDX_EMPLOYEES_COMPANY_ID = """
CREATE INDEX IF NOT EXISTS idx_employees_company_id
ON employees (company_id);
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
    ALTER_RECONCILIATION_ADD_TYPE,
    CREATE_IDX_RECONCILIATION_USER_ID,
    CREATE_PDF_STRUCTURE_PROFILES,
    CREATE_UQ_PDF_STRUCTURE_PROFILE,
    CREATE_IDX_PDF_STRUCTURE_PROFILE_TYPE,
    CREATE_COMPANIES,
    CREATE_UQ_COMPANY_NAME_LOWER,
    CREATE_EMPLOYEES,
    CREATE_UQ_EMPLOYEE_ID_COMPANY,
    CREATE_COMPANY_REQUESTS,
    CREATE_IDX_COMPANY_REQUESTS_SUBMITTED_AT,
    ALTER_EMPLOYEES_ADD_IS_MANAGER,
    CREATE_IDX_EMPLOYEES_ACCOUNT_USER_ID,
    CREATE_IDX_EMPLOYEES_COMPANY_ID,
]

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
