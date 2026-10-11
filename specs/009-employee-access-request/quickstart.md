# Quickstart & Manual Verification — Employee Access Request (Subscription Layer)

No automated tests are written for this feature (Developer instruction). This document is the verification pass instead: bring the stack up, walk the acceptance scenarios, and confirm each success criterion by hand.

---

## 1. Configure the environment

**No new environment variables.** The feature reuses what already exists:

```dotenv
# backend/.env — already present from 008; unchanged
DATABASE_URL=<cockroachdb dsn>
NEXTAUTH_SECRET=<same value the frontend signs its access tokens with>
CORS_ORIGINS=http://localhost:3000
COMPANY_LOGO_DIR=            # optional; defaults to backend/data/company_logos
```

**No dependency installs** — nothing was added to `backend/requirements*.txt`, `pyproject.toml`, or `frontend/package.json`.

On startup the backend logs `Database migrations completed successfully`; confirm the `employees` table now exists:

```sql
SHOW TABLES;
SELECT * FROM employees LIMIT 0;
```

---

## 2. Run the stack

```bash
cd backend && uvicorn src.main:app --reload --port 8000
```

```bash
cd frontend && npm run dev
```

Have at least **two companies** in the admin dashboard (one with a logo, one without) and be signed out.

---

## 3. Walk the acceptance scenarios

### US1 — Sign in and land on the Subscription page (P1)

1. Visit `http://localhost:3000/` while signed out → you are redirected to `http://localhost:3000/login`, which shows the sign-in page. **(FR-001, SC-001)**
2. Start Google sign-in and watch for a native "Leave site?" / "Changes you made may not be saved" prompt → **none appears**. **(FR-002, SC-002)**
3. Complete sign-in → you land on `/subscription`, titled **"Reconciliation AI for Companies"**, showing **Company Request**, **Employee Request**, and the **Individual Plans** panel — **not** the reconciler. **(FR-003, FR-004)**
4. Visit `/subscription` in a private window while signed out → redirected to sign in. **(FR-006, US1 scenario 4)**
5. While signed in, visit `/` → redirected to `/subscription`. **(US1 scenario 5)**
6. Confirm the existing app still works: navigate directly to `/upload-ai` → it loads as before (gating is deferred to the later spec). **(scope fence)**

### US2 — Submit an employee access request (P1)

7. On `/subscription`, click **Employee Request** → a dialog opens with Employee Name, ID, and Company to Request. **(FR-007, FR-008, SC-003)**
8. Submit with everything blank → the dialog does not send; the missing fields are indicated. **(FR-014, SC-005)**
9. Click **Generate** on the ID field → a value like `adam-7f3k92qz` appears; edit it → the edit sticks. **(FR-010)**
10. Type an ID **without** the prefix (e.g. `AB12cd34`) → after submitting, the stored value reads `adam-ab12cd34` (lowercased, single prefix). **(FR-011, SC-004)**
11. Type an ID **with** the prefix (`adam-ab12cd34`) → the prefix is **not** duplicated. **(edge case)**
12. Open the Company dropdown → every company the Developer added is listed, each with its logo or a placeholder for the one without. **(FR-009, SC-006)**
13. Complete the dialog and submit → the confirmation reads exactly:
    > "Your request has been sent to the designated company successfully, you may contact them to grant you access by providing them your ID or Name" **(FR-012)**
14. Check the row exists with `status = 'pending'`:
    ```sql
    SELECT employee_name, employee_id, company_id, company_name, account_user_id, status, created_at
    FROM employees ORDER BY created_at DESC LIMIT 5;
    ```
    Confirm `company_name` matches what the dropdown showed and `account_user_id` is your signed-in user. **(FR-016, FR-017)**

### US3 — The other plan options (P2)

15. Click **Company Request** → nothing happens. **(FR-005, SC-008)**
16. Confirm the Individual Plans panel shows **"Rs 300 - 1 day"** and **"Rs 1500 - 1 month"**; click both → no navigation, no state change. **(FR-018, SC-008)**

---

## 4. Verify the tricky paths

17. **Duplicate ID for the same company (FR-013, SC-004).** Submit a second request with the same ID and the same company → rejected with a clear message next to the ID field; the dialog stays open with your values; the row count for that (ID, company) pair is still 1.
    ```sql
    SELECT employee_id, company_id, COUNT(*) FROM employees
    GROUP BY employee_id, company_id HAVING COUNT(*) > 1;
    -- expect zero rows
    ```
18. **Same ID, different company (the resolved contradiction).** Submit the same ID against a *different* company → **accepted** and recorded as a new row. **(FR-013)**
19. **Bad ID shape.** Force a bad value (e.g. `adam-abc`) by calling the API directly → 400 `invalid_employee_id` and **no** row written.
    ```bash
    curl -i -X POST http://localhost:8000/api/employees/requests \
      -H "Authorization: Bearer <session access token>" \
      -H "Content-Type: application/json" \
      -d '{"employee_name":"Test","employee_id":"adam-abc","company_id":"1"}'
    ```
20. **Empty company list.** Delete every company in the admin dashboard, reopen the dialog → the dropdown communicates that no companies are available and submit is disabled. **(edge case)**
21. **Company list fetch failure.** Stop the backend (or block `/api/companies` in devtools), reopen the dialog → a distinct **"Couldn't load companies"** message with a **Retry** control; submit stays disabled. This must **not** look identical to the empty state. **(FR-009, clarification)**
22. **Case-insensitive duplicate.** Submit the same ID with different letter casing against the same company → rejected (normalization lowercases before the unique check). **(FR-011, SC-004)**

---

## 5. Verify the security-critical invariants

23. **Auth is required on every new endpoint.** With no token:
    ```bash
    curl -i http://localhost:8000/api/companies
    curl -i http://localhost:8000/api/companies/1/logo
    curl -i -X POST http://localhost:8000/api/employees/requests -H "Content-Type: application/json" -d "{}"
    ```
    Expect **401** from all three. **(FR-006)**
24. **The admin surface did not widen.** With only an employee bearer token, `GET /api/admin/companies` still returns **401** (the admin branch is untouched). **(non-regression)**
25. **No "Leave site?" anywhere it used to fire.** Navigate between the header links (`/upload-ai`, etc.) while signed in → no unload confirmation. **(FR-002)**
26. **In-flight cancellation still works.** Start an AI reconciliation upload, then close the tab → the `UploadAIConfig` unload handler still cancels processing server-side (check the backend log). Removing `CloseTabWarning` must not have broken this. **(non-regression)**

---

## 6. Confirm the deliberate non-goals

27. **Company Request and the plans are inert.** No handler logic exists behind them. **(FR-005, FR-018)**
28. **No gating yet.** `/upload-ai`, `/upload`, and `/tests` remain reachable by any signed-in user — the subscription layer gates nothing in this spec. **(scope fence)**
29. **Nothing else was built.** No company-facing dashboard, no accept/deny action, no billing. Any `status` other than `pending` is unreachable from the UI. **(scope fence)**
30. **No automated tests** were added — check `git status` under `backend/tests` and `frontend/src/app/tests`. **(Developer instruction)**
31. **No new dependencies** — `git diff backend/pyproject.toml backend/requirements.txt frontend/package.json` shows nothing related to this feature.

---

## Expected end state

| Check | Expected |
|-------|----------|
| `/` signed out | Redirects to `/login` |
| `/` signed in | Redirects to `/subscription` |
| `/subscription` | Titled "Reconciliation AI for Companies"; Company Request, Employee Request, Individual Plans |
| Google sign-in | No "Leave site?" prompt |
| Stored `employee_id` | Always `adam-` + 6–12 lowercase alphanumerics |
| Stored row | `status = 'pending'`; company id + name snapshot; submitting account recorded |
| Duplicate (ID + company) | 409, no second row |
| Same ID, different company | Accepted, new row |
| `GET /api/companies` without a token | 401 |
| `GET /api/admin/companies` with an employee token | 401 (admin surface unchanged) |
| Empty vs. failed company list | Two visibly different states |
| `/upload-ai` | Still reachable (gating deferred) |
| New dependencies | None |
| Automated tests added | None |
