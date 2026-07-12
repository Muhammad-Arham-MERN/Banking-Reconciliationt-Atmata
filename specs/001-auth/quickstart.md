# Quickstart: Auth.js Google OAuth

## Prerequisites

- Node.js 22+
- Python 3.11+
- CockroachDB instance (or PostgreSQL-compatible database)
- Google Cloud Project with OAuth 2.0 credentials

## Setup

### 1. Environment Variables

**Frontend** (`frontend/.env.local`):
```
AUTH_GOOGLE_ID=your-google-client-id
AUTH_GOOGLE_SECRET=your-google-client-secret
AUTH_SECRET=a-generated-secret-at-least-32-chars
DATABASE_URL=cockroachdb://user:password@host:26257/dbname?sslmode=require
```

**Backend** (`backend/.env`):
```
NEXTAUTH_SECRET=a-generated-secret-at-least-32-chars
DATABASE_URL=cockroachdb://user:password@host:26257/dbname?sslmode=require
```

> `AUTH_SECRET` and `NEXTAUTH_SECRET` MUST be the same value.

### 2. Install Dependencies

```bash
# Frontend
cd frontend
npm install next-auth@beta @auth/pg-adapter pg

# Backend
cd backend
pip install pyjwt
```

### 3. Google Cloud OAuth Setup

1. Go to Google Cloud Console → APIs & Services → Credentials
2. Create OAuth 2.0 Client ID (Web application)
3. Add Authorized redirect URI: `http://localhost:3000/api/auth/callback/google`
4. Copy Client ID and Client Secret to `AUTH_GOOGLE_ID` and `AUTH_GOOGLE_SECRET`

### 4. Database Setup

Auth.js auto-creates the `users`, `accounts`, `sessions`, and `verification_token` tables on first run.

Create the `reconciliation_data` table manually:
```sql
CREATE TABLE IF NOT EXISTS reconciliation_data (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) UNIQUE NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Add the `files` column to existing `users` table:
```sql
ALTER TABLE users ADD COLUMN IF NOT EXISTS files JSONB DEFAULT '[]'::jsonb;
```

### 5. Verify

1. Start both frontend and backend
2. Open `http://localhost:3000` — should see Google Sign-In button
3. Sign in with Google
4. Verify session persists; verify backend receives authenticated user context
