# Research: Cloud File Migration

## Decision Records

### 1. Bearer Token Acquisition (Frontend → Cloud API)

**Decision**: Expose the raw JWT token string via NextAuth session callback so client components can pass it in `Authorization: Bearer` headers.

**Rationale**: The backend already validates Auth.js JWTs using `NEXTAUTH_SECRET` (HS256). The frontend needs the raw token string to authenticate with `/api/cloud/*`. Exposing it via `session.user.access_token` in the NextAuth `jwt()` and `session()` callbacks is the standard pattern — no new auth infrastructure needed.

**Alternatives considered**:
- Reading `next-auth.session-token` cookie directly — fragile, cookie name varies
- Server-side proxy (Next.js API route that adds the token) — unnecessary indirection for a direct API call

### 2. Cloud Client Architecture

**Decision**: Create a dedicated `cloudHistoryClient.ts` module alongside the existing `historyClient.ts`, keeping them separate to avoid conflating old and new patterns.

**Rationale**: The cloud endpoints have different URL paths (`/api/cloud/*` vs `/history/*`), different auth requirements (Bearer token vs no auth), and different response shapes. A separate client keeps concerns clean and makes rollback trivial if needed.

**Alternatives considered**:
- Modifying `historyClient.ts` in-place — riskier, mixes concerns
- A generic `apiClient` with interceptors — over-engineered for two endpoints

### 3. Cloud API Response Format Mapping

**Decision**: The frontend maps existing `ReconciliationResult.discrepancies[]` to the cloud save format (file_name + list of dicts) and maps the cloud load format (list of file name strings) to the existing `Select` dropdown.

**Rationale**: The cloud `load_files_cloud` returns `FileListResponse.files: list[str]` (just file names as strings), not `HistoryFile[]` objects. The existing `UploadForm` expects `HistoryFile[]` with `file_name`, `file_path`, etc. Since cloud storage has no per-file metadata beyond the name, we simplify the type and adapt the UI accordingly.

**Alternatives considered**:
- Enriching the cloud API to match the old response schema — unnecessary, the old metadata fields are meaningless in cloud context

### 4. Save Data Format

**Decision**: The `save_files_cloud` POST body sends `{file_name: string, file_data: list<dict>}` where each dict contains the same fields currently saved: `name`, `details`, `amount`, `category`.

**Rationale**: The backend's `SaveReconciliationRequest` model already expects `file_data: list[dict[str, Any]]` with `file_name: str`. The existing `HistoryEntry[]` mapping in `ReconciliationResults` (which maps discrepancies to category, transaction_details, transaction_date, debit_credit_amount) is adapted to match the cloud contract.

**Alternatives considered**: None — backend contract is fixed.

### 5. Offline / Fallback Strategy

**Decision**: No offline mode and no local fallback. Cloud-only.

**Rationale**: Explicitly clarified during spec clarification. The app is cloud-only going forward. If the network or API is unavailable, users see an error message with a Retry button.

**Alternatives considered**: Keep local as fallback — rejected per user decision.

### 6. Greeting Implementation

**Decision**: Add the "Assalamu Alaikum [user.name]" greeting to `upload/page.tsx` (server component) using data from `auth()`.

**Rationale**: The `upload/page.tsx` is already a server component that calls `auth()`. The session object contains `user.name` from Google OAuth. No client-side API call needed — it's static per page load.

**Alternatives considered**: Client-side `useSession()` — unnecessary, the data is already on the server.
