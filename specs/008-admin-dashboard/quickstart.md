# Quickstart & Manual Verification — Admin Dashboard (Camri Desk)

No automated tests are written for this feature (Developer instruction). This document is the verification pass instead: bring the stack up, walk the acceptance scenarios, and confirm each success criterion by hand.

---

## 1. Configure the environment

Add to `backend/.env` (and document the same keys in `backend/.env.example`):

```dotenv
ADMIN_USERNAME=arham
ADMIN_PASSWORD=change-me-please
ADMIN_JWT_SECRET=<a long random string>
ADMIN_JWT_TTL_HOURS=12

# Generate once with:
#   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
FERNET_KEY=<base64 urlsafe 32-byte key>

# Optional; defaults to backend/data/company_logos
COMPANY_LOGO_DIR=
```

Add the dependency and install:

```bash
cd backend
uv add cryptography      # updates pyproject.toml + uv.lock
```

> **Do not** ever set `FERNET_KEY` to a throwaway value once real companies exist — losing the key makes every stored password unrecoverable (accepted consequence, spec edge case).

## 2. Run the stack

```bash
cd backend && uvicorn src.main:app --reload --port 8000
```

```bash
cd frontend && npm run dev
```

On startup the backend logs `Database migrations completed successfully`; confirm the `companies` table now exists.

## 3. Walk the acceptance scenarios

### US1 — Hidden-route sign-in (P1)

1. Visit `http://localhost:3000/AdminDashAccess` directly → a username/password form appears; no company data is shown. **(SC-001)**
2. Submit a wrong username, then a wrong password → the same generic denial both times; nothing hints which field was wrong. **(FR-004)**
3. Submit the configured credentials → the dashboard opens. **(FR-002, FR-005)**
4. Click every link in the app header and each page's UI → nothing anywhere references `AdminDashAccess`. **(SC-002)**
5. Sign in, **close the browser entirely**, reopen and return to the route → you are asked to sign in again. **(SC-008)**

### US2 — Register a company (P1)

6. Click **"+ Add Companies"** → a dialog opens with Name, Logo (file), Password, and Price fields. **(FR-008, FR-009)**
7. Leave the name empty and submit → the form blocks and prompts for the name. **(FR-011)**
8. Click the password generator → a random value fills the field; edit it manually to confirm it stays editable. **(FR-010)**
9. Save with only a name + price (no logo) → the row appears immediately, logo shows a placeholder, and the status reads **Pending**. **(SC-003, SC-006)**
10. Add another company with an uploaded PNG (then a JPG, then an SVG) → logos render. Add a third attempt with a `.txt` → rejected with a message and the form is preserved. **(SC-009)**

### US3 — Manage companies (P2)

11. Edit a company's name, price, and status (e.g. to **Free Trial**, then **Paid**) → the row reflects each change. **(FR-012, FR-014)**
12. Click reveal on the password cell → the value matches what you set, and copy places it on the clipboard. **(SC-007)**
13. Create a second company with the same name in different casing → rejected as a duplicate. **(edge case)**
14. Delete a company → it disappears from the list. **(FR-013)**

## 4. Verify the security-critical invariants

15. **Passwords are encrypted at rest (SC-004).** In CockroachDB:
    ```sql
    SELECT name, password_encrypted FROM companies;
    ```
    Every value is a Fernet token (`gAAAAA...`) — no plaintext anywhere.
16. **No plaintext in logs (FR-017).** Grep the backend console output and log files for a password you just created — expect zero matches.
17. **Secrets never reach the browser unnecessarily (research R5).** Open devtools → Network → the `GET /api/admin/companies` response contains **no** `password` or ciphertext field, only `has_password`.
18. **Fail-closed encryption (edge case).** Temporarily unset `FERNET_KEY`, restart, and try to create a company → a clear configuration error (503) and **no** new row.
19. **Data survives restarts (SC-005).** Restart the backend, reload the dashboard → companies, logos, and statuses are all intact. **Also confirm the logo files still exist in `COMPANY_LOGO_DIR`** — this is the check that proves logos are outside `UPLOAD_DIR` and were not swept by the shutdown cleanup (research R6).
20. **Unauthorized access is blocked.** With no token, call each endpoint directly:
    ```bash
    curl -i http://localhost:8000/api/admin/companies
    ```
    Expect 401. Then call it with `Authorization: Bearer <admin token>` → 200.

## 5. Confirm the deliberate non-goals

21. **No billing anywhere.** Search the codebase for invoice/charge/billing logic — there must be none; `price_rupees` is stored and displayed only. **(FR-015)**
22. **No company-facing login.** There is no company sign-in, employee list, or payment UI — those are later specs. **(FR-019)**
23. **No automated tests** were added (check `git status` under `backend/tests` and `frontend/src/app/tests`) — intentional, per instruction.

---

## Expected end state

| Check | Expected |
|-------|----------|
| `companies` table | Exists with 2 constraints + a unique index on `lower(name)` |
| `GET /api/admin/companies` without a token | 401 |
| `GET /api/admin/companies` with a token | Company list, no secrets |
| Stored passwords | Fernet ciphertext only |
| Logo files | In `COMPANY_LOGO_DIR`, still present after a restart |
| Route `/AdminDashAccess` | Reachable only by direct address; no in-app link |
| Session after browser close | Gone; sign-in required again |
| Billing logic | Absent (by design) |
