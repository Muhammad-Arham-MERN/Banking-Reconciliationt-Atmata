# Phase 0 Research — Company Dashboard & Onboarding Flow

All Technical Context unknowns are resolved below. Each entry records the decision, why it was chosen, and what else was considered. Findings are grounded in the existing code (file paths cited).

**Scope reminder (from the spec):** this specification adds exactly **one backend endpoint** — the company sign-in. Everything else (the cinematic onboarding, the company dashboard's Employees and Subscription sections, and the Admin Dashboard's new "Company Requests" category) is frontend structure rendered from placeholder data. **No new database tables**, and **no automated tests** (Developer instruction).

---

## R1. Company authentication mechanism

**Decision**: A new public **`POST /api/company/login`** that verifies the submitted **Company Name** (case-insensitive, trimmed) and **Password** against the `companies` row created in 008 — decrypting the stored Fernet token with the existing `company_crypto_service.decrypt_password` and comparing constant-time. On success it mints a **company JWT** (PyJWT, HS256) signed with a **new dedicated `COMPANY_JWT_SECRET`**, valid for **24 hours**, and returns it with the company identity and expiry.

**Rationale**: FR-015–FR-018 and the clarification (session lasts 24 hours, survives browser restarts). This is the single behaviour the Developer asked to wire to the backend ("Connect with backend only for this feature"). Everything needed already exists: the `companies` table + Fernet key (008), `company_crypto_service`, and `PyJWT` (already a dependency). A signing secret separate from `ADMIN_JWT_SECRET` and `NEXTAUTH_SECRET` keeps the three principals (company / admin / Google user) independent, exactly as 008 separated the admin.

**Alternatives considered**:
- *No token — return company identity and let the client hold a flag* — rejected: the spec frames sign-in as establishing a **session** with a 24-hour expiry (FR-018); a server-issued, expiring token is the honest, pattern-consistent implementation, and the next specification (real company endpoints) will need it. (Flagged as reversible in Complexity Tracking.)
- *Reuse `ADMIN_JWT_SECRET`* — rejected: the company and the admin are different principals; sharing a secret would let either impersonate the other.
- *Reuse `NEXTAUTH_SECRET`* — rejected: that signs the Google-user tokens the middleware already verifies; mixing principals would blur the auth model.

## R2. Where company auth sits in `auth_middleware`

**Decision**: Add a company branch mirroring the admin branch:
- `COMPANY_PREFIX = "/api/company"`, `COMPANY_LOGIN_PATH = "/api/company/login"`.
- `POST /api/company/login` → **public** (skipped), like `/api/admin/login`.
- Any other `/api/company/*` path → verified against the **company JWT**; on success sets `request.state.company_id` (and the name), else 401.

**Rationale**: `auth_middleware` runs globally and 401s every non-exempt path that lacks a valid **NextAuth** Bearer token (`src/api/auth_middleware.py`). A company has no Google session, so its login cannot ride the NextAuth branch, and its future endpoints cannot either. A dedicated branch matches the admin pattern exactly: the login is the one public path, everything else under the prefix is gated centrally (fail-closed — a forgotten per-route check cannot open company data).

**Alternative considered**: *Add `/api/company...` to `AUTH_EXEMPT_PREFIXES`* — rejected: prefix exemption is coarse and would make any future company endpoint silently public. An exact-path public check for the login plus a gated branch for the rest is clearer and safer.

## R3. Company session storage and lifetime

**Decision**: The company JWT and identity are persisted in **`localStorage`** as a session object — `{ token, company: { id, name, logo_url }, expires_at }`. The frontend treats the company as signed in only while `expires_at` is in the future (24h) and clears the entry when it has passed. A route-level client shell owns the gate.

**Rationale**: The clarification fixed **24 hours, surviving browser restarts** — which rules out `sessionStorage` (008's admin choice, which ends at browser close) and points at `localStorage` with an explicit expiry check. The pattern mirrors `frontend/src/lib/admin/admin-session.ts` (an external store read via `useSyncExternalStore` to avoid hydration mismatch), swapped to `localStorage` and extended with an expiry.

**Alternatives considered**: *`sessionStorage`* — rejected: browser-close expiry contradicts the 24-hour clarification. *httpOnly cookie* — rejected: the API is called cross-origin (localhost:3000 → :8000, plus a Vercel origin) and the repo uses Bearer tokens everywhere; a cookie would force `SameSite=None; Secure` + credentialed CORS. *No expiry* — rejected by FR-018.

## R4. Company name matching at sign-in

**Decision**: Look the company up with `WHERE lower(name) = lower($1)` using the trimmed input. A missing/unusable Fernet key fails closed with **503 `encryption_unavailable`**; an unknown company and a wrong password both return the **same generic 401**.

**Rationale**: FR-027 + the clarification ("case-insensitive and trimmed"). 008 already created `uq_company_name_lower` (`db_migrations.py`), so this is an indexed lookup and stays consistent with how the name is stored as the company identifier. The generic error prevents probing which companies exist (FR-017).

**Alternatives considered**: *`ILIKE`* — rejected: unnecessary; the functional index already makes `lower(name) = lower($1)` efficient. *Case-sensitive exact match* — rejected by FR-027.

## R5. Verifying the password

**Decision**: Decrypt the stored ciphertext with `company_crypto_service.decrypt_password` and compare with **`hmac.compare_digest`** (both sides UTF-8 encoded, the idiom already used in `admin_auth_service._compare_digest`). Both fields are always evaluated; the response never discloses which was wrong.

**Rationale**: 008 deliberately stores company passwords with **reversible** Fernet precisely so they can be read back and later verified by the company-facing sign-in (008 research R4). Constant-time comparison avoids a timing side channel; the single generic error matches FR-017. A `DecryptionError` (rotated key/corrupt token) surfaces as a clear 500/503 rather than a false "wrong password".

**Alternatives considered**: *Store/verify a hash* — impossible: 008 already stores reversible ciphertext; re-hashing would require a schema and data migration. *Reuse the admin reveal endpoint to compare* — rejected: it is admin-gated and would leak the plaintext password to the browser.

## R6. Route naming and placement

**Decision**: The company dashboard lives at **`/CompanyDashboard`** (`frontend/src/app/CompanyDashboard/page.tsx`), a thin `export const dynamic = "force-dynamic"` **server** shell rendering a `'use client'` `<CompanyDashboard/>`. Unlike `AdminDashAccess`, it is **not hidden** — the Developer gives companies the URL. The sign-in gate lives in the client shell (the session is client-held).

**Rationale**: The Developer named the route "CompanyDashboard", and the uppercase-segment App Router approach is the established precedent from 008's `AdminDashAccess` (which builds cleanly). The sign-in is client-side because the company session lives in `localStorage`; there is no NextAuth session to check server-side, so a server `auth()` guard (used by `/subscription`) would be wrong here.

**Alternative considered**: *lowercase `/company-dashboard`* — rejected: inconsistent with the Developer's explicit naming and 008's route convention; revisit only if the toolchain objects to the uppercase segment.

## R7. Cinematic onboarding — implementation approach

**Decision**: A full-screen overlay (fixed, above the app) driven by a phase state machine — **`intro → questions → success`** — built with **`motion`** (already a dependency, `motion@^13`, already used by `typewriter-effect.tsx`):
- **Intro**: a `motion.div` block in the cherry theme color (`bg-primary` — the app's peach-red `--primary`, `oklch(0.65 0.15 25)`) slides in to cover the viewport with a motion-blur transition; a **center-origin star streak** field conveys motion into the screen; a centered **company-building SVG** starts small and scales up over ~5s; the view then "enters a window" (mask/scale transition) and the building fades out.
- **Questions**: four steps, each fading in (see R10), with the boss guide (R8) fixed near the lower-center.
- **Success**: the typewriter message (R9), auto-close after 5s, with a top-right cross available throughout (FR-013).

**Rationale**: `motion` already ships in the project, so the whole sequence needs no new dependency. The spec's narrative maps cleanly onto a small timeline of opacity/scale/blur transitions. FR-014 (reduced motion) is honoured with `useReducedMotion()` — when set, the intro is skipped/parked and the questions still run.

**Alternatives considered**: *Hand-rolled `requestAnimationFrame`* — rejected: `motion` covers it with less code. *A pre-rendered video* — rejected: heavier, and not animatable per-question.

**Reuse note**: the repo already contains `components/ui/stars-background.tsx` and `components/ui/shooting-stars.tsx` (Aceternity). The star-streak field may reuse/adapt their technique, but the required radial, center-origin "warp" streak is its own small component (`company-request/star-field.tsx`) since neither existing component streaks *from the center outward*.

## R8. Porting the bored-boss loader

**Decision**: Transplant `frontend/boss-loader.html` (pure SVG + CSS keyframes, no JS) into `frontend/src/components/company-request/boss-loader.tsx` + `boss-loader.module.css` **verbatim**, then **delete `frontend/boss-loader.html`** (Developer instruction). The flow drives three states: **idle** (pen tapping — always on), **hands-up** (played when the visitor advances a question, then back to idle), and **smile** (after the final answer).

**Rationale**: The Developer instructed using the animation directly in Next.js and removing the reference file. The reference is already dependency-free ("nothing animates via inline styles, so it transplants cleanly", per its own header comment), and a CSS module keeps the keyframes out of the global sheet. Its `--boss-*` palette maps onto the app's shadcn tokens so it themes with light/dark automatically.

**Alternatives considered**: *Keep the `.html` file in the repo* — rejected (explicit instruction to remove it). *Add a third-party animation package* — rejected: unnecessary.

## R9. The success message (text-generate effect)

**Decision**: Reuse the existing **`TypewriterEffect`** (`components/ui/typewriter-effect.tsx` — the Aceternity *text-generate-effect* the Developer linked) with the exact string **"Request Sent Successfully - Please Wait For The Team To Contact Your Representative"**; all other animation clears first, and the overlay auto-fades five seconds after the message begins (FR-011, FR-012).

**Rationale**: The component already exists in the repo, so the requested effect needs no new dependency and no hand-rolling (satisfying the standing "prefer official components" preference). The five-second auto-close and the always-available cross implement FR-012/FR-013.

## R10. Onboarding questions and validation

**Decision**: Four steps, one at a time, each fading in via `motion`: **Company Name**, **Role**, **Website/Socials**, and **Email and Phone Number** (email + phone together). Each is gated by the clarification's basic format checks before the visitor can advance, with an inline per-field message:
- Company Name, Role — non-empty.
- Website/Socials — a web address (URL/domain) **or** a social handle (e.g. `@acme`).
- Email — a standard email shape.
- Phone — digits with optional `+ ( ) -` and spaces.

**Rationale**: FR-007/FR-008 + the clarification. Validation is a small pure helper so it is testable by hand and reused by every step.

**Alternatives considered**: *Non-empty only* — rejected in the clarification. *Strict URL/phone libraries* — rejected: new dependencies for rules the spec states loosely.

## R11. The Aceternity sidebar (company dashboard, and admin category nav)

**Decision**: Add the Aceternity **sidebar** the Developer referenced to `frontend/src/components/ui/sidebar.tsx` via the project's own registry (`components.json` declares `@aceternity`), then wrap it in `components/company-dashboard/company-sidebar.tsx` with exactly two sections: **Employees** and **Subscription**. **Reuse the same sidebar** for the Admin Dashboard's new category navigation ("Companies" / "Company Requests").

**Rationale**: The Developer explicitly linked the Aceternity sidebar, and the registry (`https://ui.aceternity.com/registry/sidebar.json`) lists only two dependencies — `@tabler/icons-react` and `motion` — **both already installed** (`package.json`), so this adds **no new dependency**. Reusing one sidebar component keeps a single navigation idiom across both dashboards and avoids hand-rolling a second one.

**Alternatives considered**: *Hand-rolled sidebar* — rejected (Developer prefers official components). *shadcn `sidebar`* — n/a: the Developer asked for the Aceternity one specifically.

## R12. Employees table and "Grant Access"

**Decision**: A shadcn **`Table`** (`components/ui/table.tsx`, already used by `companies-table.tsx`) listing the company's employees with columns **Employee**, **Employee ID**, **Status**, and a **Grant Access** checkmark action. Clicking toggles a local `granted` state (the checkmark fills); rows come from placeholder data; an empty state is shown when there are none. **No backend call** (FR-020/021/024).

**Rationale**: FR-020/021 and the placeholder-data decision (FR-024). Reusing the existing Table keeps the dashboard visually consistent with the admin's `companies-table.tsx`.

## R13. Subscription section

**Decision**: A small `Card` reading **"Start 30 days free trial"** with **no handler** (inert). It is the only content of the Subscription section.

**Rationale**: FR-022 — visible and clickable but performing no action; payment/billing is out of scope (spec Assumptions).

## R14. Admin "Company Requests" category

**Decision**: The Admin Dashboard gains a category navigation (the reused sidebar) with **Companies** (the existing table, unchanged) and **Company Requests** (a new `components/admin/company-requests-table.tsx`). The new table lists placeholder requests with **Company**, **Role**, **Website/Socials**, **Email**, and **Phone**, and opening a row reveals the full details in a shadcn `Dialog` so the Developer can contact the company. An empty state is shown when there are none. **No backend** (FR-023/024).

**Rationale**: FR-023 requires the category and a detail view; the spec defers request persistence to the backend specification, so the view renders placeholder data (FR-024). Reuses the existing `Table`/`Dialog`/`Card` primitives.

**Alternative considered**: *A plain toggle instead of a sidebar* — rejected in favour of reusing the sidebar already added for the company dashboard, which gives a coherent "category" UX in both places.

## R15. Placeholder data and empty states

**Decision**: `frontend/src/lib/company/company-placeholder.ts` holds sample employees and sample company requests; each component renders its own explicit empty state when its array is empty. Commented as a deliberate stand-in for the backend specification.

**Rationale**: FR-024. Keeping the samples in one file makes them trivial to delete when real data arrives.

## R16. Dependencies

**Decision**: **None added**, on either side.

**Rationale**: Backend already has FastAPI, asyncpg, pydantic, PyJWT, cryptography. Frontend already has `motion`, `@tabler/icons-react` (the sidebar's deps), the `TypewriterEffect`, and every shadcn primitive used. Constitution Principle II (Developer Stack Authority) is satisfied by adding no framework or library.

## R17. Automated tests

**Decision**: **None.** No pytest, no Playwright, no test tasks. Verification is the manual pass in `quickstart.md`.

**Rationale**: The Developer instructed "no tests" in the spec input; 008 and 009 set the precedent; Constitution Principles I/II make that the correct reading. Recorded here so the omission is deliberate rather than an oversight.

---

## Resolved unknowns summary

| # | Unknown | Resolution |
|---|---------|------------|
| R1 | Company auth | `POST /api/company/login` verifies name+password, mints a 24h company JWT (`COMPANY_JWT_SECRET`) |
| R2 | Middleware integration | Company branch: login public, rest gated by the company JWT |
| R3 | Session storage | `localStorage` session object with a 24h `expires_at` check (mirrors `admin-session.ts`) |
| R4 | Name matching | `lower(name) = lower($1)`, trimmed; unknown company → generic 401 |
| R5 | Password check | Fernet decrypt + `hmac.compare_digest`; generic error; fail closed if key missing |
| R6 | Route | `/CompanyDashboard` uppercase segment, thin server shell + client dashboard |
| R7 | Cinematic intro | `motion` phase machine: block → star streaks → building growth → window entry; reduced-motion honored |
| R8 | Boss loader | Port SVG/CSS to `boss-loader.tsx` + `.module.css`; delete `boss-loader.html` |
| R9 | Success message | Reuse existing `TypewriterEffect`; 5s auto-close; skip cross |
| R10 | Questions | Four fading steps with basic format validation |
| R11 | Sidebar | Add Aceternity `sidebar.tsx` (deps already present); reuse for admin category nav |
| R12 | Employees table | shadcn `Table` + Grant Access toggle; placeholder data; empty state |
| R13 | Subscription | Inert "Start 30 days free trial" `Card` |
| R14 | Admin category | Sidebar nav (Companies / Company Requests) + placeholder requests table + detail dialog |
| R15 | Placeholder data | One `company-placeholder.ts` module + explicit empty states |
| R16 | Dependencies | None added |
| R17 | Tests | None, per explicit Developer instruction |
