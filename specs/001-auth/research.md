# Research: Google OAuth Authentication with Auth.js

## Auth.js (NextAuth v5) in Next.js 16 App Router

**Decision**: Use `next-auth@5` with the App Router's `@/api/auth/[...nextauth]/route.ts` handler pattern. Auth.js v5 is now under Better Auth but `@auth/*` and `next-auth` packages remain available for existing projects. The App Router integration uses `NextAuth()` returning `{ handlers, auth, signIn, signOut }`.

**Rationale**: The spec explicitly requires Auth.js. v5 supports App Router, Google provider, and PostgreSQL adapter out of the box. Minimal custom code needed.

**Key findings**:
- Install: `npm install next-auth@beta @auth/pg-adapter pg`
- Google provider: `import Google from "next-auth/providers/google"`
- Session strategy: Use JWT (default) for simplicity with 24-hour `maxAge`
- Route handler: `/api/auth/[...nextauth]/route.ts` re-exporting `handlers`

## CockroachDB with Auth.js PostgreSQL Adapter

**Decision**: Use `@auth/pg-adapter` directly with CockroachDB. CockroachDB is PostgreSQL-wire-compatible, so the standard `pg` Node.js driver and Auth.js PostgreSQL adapter work without modifications.

**Rationale**: CockroachDB speaks PostgreSQL protocol. The Auth.js PostgreSQL adapter uses standard SQL queries that CockroachDB supports. No custom adapter needed.

**Key findings**:
- Connection via `pg.Pool` with CockroachDB connection string
- Auth.js auto-creates tables: `users`, `accounts`, `sessions`, `verification_token`
- Custom `Reconciliation_data` table added separately via migration SQL
- `users` table extended with `files` column (JSONB array of file_name strings)

## Session Token Verification on FastAPI Backend

**Decision**: FastAPI backend validates requests by receiving the Auth.js session JWT token from the frontend via `Authorization: Bearer <token>` header. The backend decodes and verifies the JWT using the same `NEXTAUTH_SECRET` environment variable.

**Rationale**: This avoids duplicating Auth.js server-side. The JWT strategy means sessions are self-contained tokens. The backend only needs the secret and the JWT library to verify.

**Key findings**:
- Use `PyJWT` to decode/verify the Auth.js JWT
- Middleware extracts `sub` (user ID) and `email` from verified token
- Pass user context to reconciliation services for data isolation
- Secret shared via `NEXTAUTH_SECRET` env var on both frontend and backend

## Frontend Project Structure (Next.js 16 + Auth.js)

**Frontend dependency additions**:
- `next-auth@beta` (or `next-auth@5`)
- `@auth/pg-adapter`
- `pg` (PostgreSQL client for Node.js)

**Structure**:
- `src/lib/auth.ts` — Auth.js configuration (providers, adapter, callbacks)
- `src/app/api/auth/[...nextauth]/route.ts` — Route handler
- `src/components/auth/sign-in-button.tsx` — Google Sign-In button
- `src/components/auth/session-status.tsx` — User avatar/session display
- `src/components/providers/session-provider.tsx` — SessionProvider wrapper

**Environment variables**:
- `AUTH_GOOGLE_ID` — Google OAuth client ID
- `AUTH_GOOGLE_SECRET` — Google OAuth client secret
- `AUTH_SECRET` — Auth.js encryption secret
- `DATABASE_URL` — CockroachDB connection string
