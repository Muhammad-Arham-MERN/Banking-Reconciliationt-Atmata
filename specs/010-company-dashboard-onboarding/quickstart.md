# Quickstart & Manual Verification — Company Dashboard & Onboarding Flow

No automated tests are written for this feature (Developer instruction). This document is the verification pass instead: bring the stack up, walk the acceptance scenarios, and confirm each success criterion by hand.

---

## 1. Configure the environment

**One new backend variable** — the company session signing secret (separate from `ADMIN_JWT_SECRET` and `NEXTAUTH_SECRET`):

```dotenv
# backend/.env — add alongside the existing 008 variables
COMPANY_JWT_SECRET=<a long random string>
COMPANY_JWT_TTL_HOURS=24        # optional; defaults to 24
```

Everything else already exists from 008/009: `DATABASE_URL`, `NEXTAUTH_SECRET`, `CORS_ORIGINS`, `FERNET_KEY`, `COMPANY_LOGO_DIR`.

**No dependency installs** — nothing was added to `backend/requirements*.txt`, `pyproject.toml`, or `frontend/package.json`. The Aceternity sidebar's dependencies (`motion`, `@tabler/icons-react`) and the `TypewriterEffect` were already present.

Confirm the backend starts and logs `Database initialized and migrations applied`. **No new table is created** by this feature (`SHOW TABLES;` is unchanged).

---

## 2. Run the stack

```bash
cd backend && uvicorn src.main:app --reload --port 8000
```

```bash
cd frontend && npm run dev
```

Prerequisites: at least **one company** created in the Admin Dashboard (008) with a known name and password, and a signed-in Google user (the subscription page is behind that sign-in from 009).

---

## 3. Walk the acceptance scenarios

### US1 — Cinematic "Company Request" onboarding (P1)

1. Sign in and land on `/subscription`. Click **Company Request** → a full-screen cherry-colored block slides in and covers the app with a motion-blur feel. **(FR-001, FR-002, SC-002)**
2. Watch the intro: stars streak **from the center toward the viewer**, a company building grows steadily, and after ~5s the view enters a window and the building fades. **(FR-003–FR-005)**
3. Confirm the bored-boss character appears **near the lower-center** and is tapping his pen. **(FR-006, FR-009)**
4. Answer **Company Name**, **Role**, **Website/Socials**, and **Email and Phone Number** one at a time; each fades in. Verify the boss plays a brief **hands-up** pose when you advance, then resumes tapping. **(FR-007, FR-009)**
5. Submit a **malformed** value in a step (e.g. `not-an-email` in Email, or a bare word in Website/Socials) → you **cannot advance**; the field is flagged inline. **(FR-008, SC-011)**
6. After the final answer, the boss **smiles**, the animation clears, and the typewriter writes **"Request Sent Successfully - Please Wait For The Team To Contact Your Representative"**. **(FR-010, FR-011)**
7. Wait 5 seconds → the overlay **fades out** and the subscription page returns. **(FR-012)**
8. Reopen and dismiss with the **top-right cross** mid-flow → the overlay closes immediately and no request is recorded anywhere (by design nothing is stored). **(FR-013, FR-026, SC-003)**
9. With the OS **"reduce motion"** setting on, reopen → the motion-heavy intro is skipped/parked but all four questions remain completable. **(FR-014, SC-009)**

### US2 — Company sign-in to the Company Dashboard (P1)

10. Open `/CompanyDashboard` signed out → the **Company Name + Password** form is shown; no dashboard content. **(FR-015, SC-005)**
11. Submit an **unknown company** and separately a **wrong password** for a real company → both are denied with the **same generic message** (no field disclosed). **(FR-017, SC-004)**
12. Submit the **correct** name and password → the Company Dashboard opens. **(FR-016, US2 scenario 3)**
13. Close and **reopen the browser** (still within 24h) → the dashboard opens again without re-entering credentials. **(FR-018)**
14. In DevTools, clear or expire the stored session (e.g. set `expires_at` in the past / delete the `localStorage` key) and reload → the **sign-in form returns**. **(FR-018, US2 scenario 5)**
15. Try the company name with **different casing and surrounding spaces** (` greaves PAKISTAN `) → it still signs in. **(FR-027)**

### US3 — Company Dashboard: Employees and Subscription (P2)

16. After sign-in, confirm the sidebar shows **exactly two** sections: **Employees** and **Subscription**. **(FR-019, SC-006)**
17. Open **Employees** → a shadcn table lists the company's employees with a **Grant Access** checkmark per row; click it → the row's state visibly changes to granted. **(FR-020, FR-021, SC-007)**
18. If the placeholder employee list is empty → a clear **empty state** is shown. **(FR-020, edge case)**
19. Open **Subscription** → a small card reads **"Start 30 days free trial"**; click it → nothing happens. **(FR-022, SC-008)**

### US4 — Admin "Company Requests" category (P3)

20. Open `/AdminDashAccess`, sign in, and confirm the new **Company Requests** category alongside the existing companies list. **(FR-023, SC-010)**
21. Open a request → its **Company Name, Role, Website/Socials, and Email and Phone Number** are shown for contacting the company. **(FR-023)**
22. When there are no requests → a clear **empty state** is shown. **(FR-023, SC-010)**

---

## 4. Verify the tricky paths

23. **Session expiry is enforced on read.** Set the stored `expires_at` to a past time and reload → signed out. **(FR-018)**
24. **No request is ever stored** (FR-026). After completing the onboarding flow, check:
    - DevTools → Application → Local/Session Storage: **no** company-request entry is written.
    - The network tab: **no** request to the backend other than (optionally) none at all during the flow.
    - `SELECT count(*) FROM employees;` is unchanged by the flow.
25. **Only one backend endpoint exists.** Confirm `POST /api/company/login` is the sole new route; the dashboard's tables and the admin request view make **no** API calls. **(FR-024, scope fence)**
26. **Fail-closed auth.** With `COMPANY_JWT_SECRET` empty, the login returns **503 `company_auth_not_configured`**; with `FERNET_KEY` empty, it returns **503 `encryption_unavailable`**. Neither issues a session. **(R1/R5, 008 precedent)**

---

## 5. Verify the security-critical invariants

27. **Generic denial.** Compare the 401 body for an unknown company vs. a wrong password — they must be **byte-identical** (`invalid_credentials`). **(FR-017)**
28. **The admin surface did not widen.** `GET /api/admin/companies` still requires the admin token; an employee/company token returns 401. **(non-regression)**
29. **The company sign-in path is the only public company path.** `GET /api/company/anything-else` without a company token returns 401. **(R2)**
30. **No secret material is returned.** The login response contains only id/name/logo_url — never the password or its ciphertext. **(R5, 008 precedent)**

---

## 6. Confirm the deliberate non-goals

31. **Placeholder data is used.** The employees table, the Company Requests category, and the subscription card render from `company-placeholder.ts` with empty states — no real data. **(FR-024, scope fence)**
32. **Grant Access is visual only.** Clicking it does not write to the `employees` table; verify with `SELECT count(*)` before/after. **(FR-021)**
33. **Billing is untouched.** The subscription card performs no action; no payment code exists. **(scope fence)**
34. **The boss reference file is gone.** `frontend/boss-loader.html` no longer exists; the animation lives in `components/company-request/`. **(Developer instruction)**
35. **No automated tests** were added — check `backend/tests` and `frontend/src/app/tests`. **(Developer instruction)**
36. **No new dependencies** — `git diff backend/pyproject.toml backend/requirements.txt frontend/package.json` shows nothing related to this feature.

---

## Expected end state

| Check | Expected |
|-------|----------|
| "Company Request" on `/subscription` | Opens the full-screen cinematic onboarding |
| Intro sequence | Cherry block → center-origin star streaks → growing building → window entry |
| Boss guide | Lower-center; taps while typing, hands-up on advance, smiles at the end |
| Questions | Four, one at a time, fading in; basic format validation blocks bad input |
| After the last answer | Typewriter success message; auto-fade after 5s; cross skips anytime |
| `/CompanyDashboard` signed out | Company Name + Password form |
| Wrong name or wrong password | Identical generic denial |
| Correct credentials | Dashboard opens; session persists 24h across browser restarts |
| Sidebar | Exactly "Employees" and "Subscription" |
| Employees | shadcn table + Grant Access toggle (local only); empty state when none |
| Subscription | Inert "Start 30 days free trial" card |
| `/AdminDashAccess` | New "Company Requests" category with detail view; empty state when none |
| Request submission | Nothing persisted anywhere (client or server) |
| New DB tables | None |
| New backend endpoints | One (`POST /api/company/login`) |
| New dependencies | None |
| Automated tests added | None |
