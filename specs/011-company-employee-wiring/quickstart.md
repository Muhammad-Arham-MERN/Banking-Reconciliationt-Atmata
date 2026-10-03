# Quickstart — Manual Verification for `011-company-employee-wiring`

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Contracts**: [contracts/](./contracts/)

No automated tests (Developer standing instruction). This is the manual pass that proves the feature. Run the backend (`uvicorn`) and frontend (Next.js) against CockroachDB.

Prerequisite env (backend): `RESEND_API_KEY`, `RESEND_FROM_EMAIL`, `COMPANY_REQUEST_NOTIFY_EMAIL` (default `ArhamBrowser@gmail.com`) — the email step is skipped with a warning when `RESEND_API_KEY` is empty.

---

## A. Employee request → company dashboard (User Story 1, FR-001…FR-005)

1. As a signed-in employee, open the subscription page → **Employee Request**; submit name + generated ID to a real company.
2. As that company, sign in on `CompanyDashboard` → **Employees**: the request appears with name, `adam-` ID, status `Pending`.
3. Type part of the **ID** in the search box → the row matches. Clear, type part of the **name** → the row still matches. Type a string that matches neither → "no matches" state. (FR-002; ID precedence)
4. Click **Grant Access** → status becomes `Granted`/`Accepted` immediately.
5. Submit a second request from another account, then **Delete** it → it disappears (FR-004).

## B. The gate (User Story 2, FR-009/FR-010/FR-015/FR-016/FR-017/FR-025)

1. As a signed-in account **with no grant**, navigate to `/upload-ai` → redirected to `/subscription`; the app links in the header are hidden. (FR-009)
2. Directly call a gated backend endpoint (e.g. `POST /reconcile-ai`) with a valid session token but no membership → `403 membership_required`. (FR-009, server-enforced)
3. Have the company **grant** the request → the same account can now use `/upload-ai`. (FR-003)
4. Header shows the company name + **Leave company**. Attempt to open `/subscription` → redirected away (must leave first). (FR-016)
5. Click **Leave company** → confirm → returned to the subscription layer; `/upload-ai` is blocked again; the company's employee list no longer contains the record. (FR-015)
6. While holding a pending request, click **Employee Request** again → blocked with "cancel your existing request" (any company); cancel → the record is gone from the company. (FR-017)

## C. Company onboarding requests + email (User Story 3, FR-006/FR-007/FR-008)

1. On the subscription page click **Company Request**; complete the cinematic flow.
2. Open the Admin Dashboard → **Company Requests**: the new request is listed with Company Name, Role, Website/Socials, Email, Phone, submitted time. (FR-006)
3. Confirm the notification email arrived at `COMPANY_REQUEST_NOTIFY_EMAIL` (`ArhamBrowser@gmail.com`). (FR-007)
4. Temporarily set an invalid `RESEND_API_KEY` and submit again → the request is still stored and listed (email failure does not lose it). (FR-007)
5. Confirm no placeholder rows remain anywhere (Company dashboard list, Company Requests, Admin companies). (FR-008)

## D. Admin employee count + hover modal (User Story 4, FR-018)

1. Admin Dashboard → **Companies**: each row shows an employee count.
2. Hover the count → a modal lists that company's employees (name, ID, status). (FR-018)
3. A company with no employees shows `0` and an empty-state modal.
4. Delete the company → its employees are gone from the count/roster and their access is revoked. (FR-023)

## E. Manager role + hidden dashboard entry (User Story 5, FR-019/FR-020)

1. In the Company Dashboard, toggle an accepted employee to **Manager**. (FR-019)
2. As that manager, use the application → the header shows a **Company Dashboard** entry; clicking it opens the dashboard. (FR-020)
3. As a non-manager member → no **Company Dashboard** entry, and the dashboard address is not present anywhere in the app. (FR-020)
4. A manager who is not an app user reaches the dashboard via the company credentials (company login), not the nav entry.

## F. Sign convention end-to-end (User Story 6, FR-012…FR-014)

1. Run a **Bank** reconciliation. On the results, subtotals, adjustment panel, totals/verdict: Unpresented = −, Uncleared = +, Bank Debited-not-Credited = +, Bank Credited-not-Debited = −. (FR-012)
2. Run a **Vendor** reconciliation: Unpresented = −, Uncleared = +, Vendor Debits = −, Vendor Credit = +. (FR-013)
3. Save each, then reopen from history → identical signs; confirm the stored `Debit/Credit` values match `contracts/sign-convention.md` §2. (FR-014)
4. Confirm the verdict never contradicts the displayed signs (no flipped sign next to a balanced/unbalanced verdict).

## G. Animations (User Story 7, FR-022)

1. Exercise the onboarding overlay, sidebar section changes, table reveals, loaders, and page transitions → smooth and consistent.
2. Enable the OS reduced-motion setting → motion-heavy animation is skipped/softened; every screen stays usable.

---

## Schema sanity (in CockroachDB)

- `SELECT column_name FROM information_schema.columns WHERE table_name='employees'` includes `is_manager`.
- `SELECT * FROM company_requests ORDER BY submitted_at DESC;` returns submitted rows.
- Indexes exist: `idx_employees_account_user_id`, `idx_employees_company_id`, `idx_company_requests_submitted_at`.
