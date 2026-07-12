# Quickstart: Cloud File Migration

## Prerequisites

- Frontend dev server running (`pnpm dev` in `frontend/`)
- Backend server running with cloud routes (`uvicorn src.main:app` in `backend/`)
- `NEXTAUTH_SECRET` set in both frontend `.env.local` and backend `.env` (must match — HS256 symmetic key)
- `NEXT_PUBLIC_API_URL` pointing to the backend (default: `http://localhost:8000`)
- CockroachDB connection via `DATABASE_URL` on both sides
- Users signed in via Google OAuth (at least one session exists in the DB)

## Implementation Order

### Step 1: Expose JWT token in NextAuth session

**Files**: `frontend/src/lib/auth.config.ts`

Add `access_token` to the `session` callback by reading it from the `jwt` callback:

```typescript
async jwt({ token }) {
  // token.sub is the user_id from the DB
  return token;
},
async session({ session, token }) {
  if (token.sub) session.user.id = token.sub;
  session.user.access_token = token.jti || token.sub;  // FIXME: verify actual token claim
  return session;
},
```

> **Note**: The exact JWT claim name depends on Auth.js internals. The goal is to get the raw JWT string that the backend can verify.

### Step 2: Create cloud API types

**Files**: `frontend/src/types/cloud-history.types.ts`

New types for cloud API request/response shapes. Simpler than the local `history.types.ts` — cloud returns only file names, no metadata.

### Step 3: Create cloud history client

**Files**: `frontend/src/lib/api/cloudHistoryClient.ts`

- `listCloudFiles(token)`: GET `/api/cloud/load_files_cloud` with Bearer header
- `saveCloudFile(token, fileName, fileData)`: POST `/api/cloud/save_files_cloud` with Bearer header

### Step 4: Update upload page with greeting

**Files**: `frontend/src/app/upload/page.tsx`

Add "Assalamu Alaikum [user.name]" greeting below the page title using data from `auth()`.

### Step 5: Update UploadForm to load from cloud

**Files**: `frontend/src/components/upload/UploadForm.tsx`

Replace the `historyClient.listHistory()` call with `cloudHistoryClient.listCloudFiles()`. Get the token from `useSession()`.

### Step 6: Update ReconciliationResults to save to cloud

**Files**: `frontend/src/components/results/ReconciliationResults.tsx`

Replace the `historyClient.saveHistory()` call with `cloudHistoryClient.saveCloudFile()`. The data mapping is nearly identical.

## Verification

1. Sign in with Google
2. See "Assalamu Alaikum [name]" on the upload page
3. See your previously saved files in the "Open Maazi" dropdown
4. Complete a reconciliation and save it
5. Refresh the page — the new file appears in the dropdown

## Rollback

If issues arise:
1. Revert changes to `auth.config.ts` (remove JWT exposure)
2. Swap cloud client calls back to `historyClient` in `UploadForm.tsx` and `ReconciliationResults.tsx`
3. Revert `upload/page.tsx` greeting addition
