# Feature Specification: Company-Employee Dashboard Wiring, Finalized Sign Conventions & Edge Cases

**Feature Branch**: `011-company-employee-wiring`  
**Created**: 2026-10-02  
**Status**: Draft  
**Input**: User description: "Finalized implementation of the company-employee dashboard system, the vendor and bank Credit-Debit signs convention finalized, edge cases to be covered, plus some animation improvement. [Company-Employee Dashboard Wiring] The entire frontend is established; only backend wiring is needed: (1) when an employee makes a request associated with a company, that employee is added to the Company Table of that company, so the company dashboard receives an employee request; (2) the Company Dashboard has a search bar that searches names or IDs automatically, evaluating the input against ID and then name without the user selecting a mode; (3) a successful 'Company Request' submission surfaces that company and its details in the Admin Dashboard under Company Requests; (4) all dummy data is removed; (5) Resend is used to send a simple new-company-request email to ArhamBrowser@gmail.com; (6) employee requests can be deleted; (7) granting access to an employee enables application access for that particular user and employee — beforehand they must not bypass access toward /upload-ai; to access /upload-ai they must be assigned a granted request by a company; the individual plan 'coming soon' stays as is. [Signs Finalized Throughout App] Bank — Unpresented Checks: credited in cashbook is negative; Uncleared Checks: debited in cashbook is positive; Bank Debited but not credited in cashbook is positive; Bank Credited but not debited in cashbook is negative. Vendor — Unpresented Checks: credited in cashbook is negative; Uncleared Checks: debited in cashbook is positive; Vendor Debits is negative; Vendor Credit is positive. The sign convention must be followed throughout the entire app. [Edge Cases] (1) after being granted access, the user can leave the company from the navigation bar with confirmation, which also makes them lose application access back to subscriptions or sign-in; (2) an employee who has accessed the application cannot view the subscription page again without leaving the company; (3) a user who has requested access with a company cannot make a new request via 'Employee Request' — they are asked to cancel the older request, and cancellation deletes the employee request from company records; (4) in the Admin Dashboard, a company whose account was created also shows the number of employees, and hovering opens a modal listing all employees associated with the company using the application; (5) the app is not usable unless an employee with access is granted; (6) user data at sign-in and employee information must be linked and reference each other for future features; (7) a user with company dashboard access can see the list of all their employees, can request as an employee to the company they manage and grant themselves access, and can assign any account as 'Manager', which enables a 'Company Dashboard' entry in the application navigation bar — letting the manager reach the dashboard without the URL, while keeping the dashboard URL hidden from others."

**Testing Policy**: **No tests are to be written for this feature.** No test files, test suites, test cases, or test tasks MUST be added on either the backend or the frontend — this is the Developer's standing instruction. Verification is entirely the manual pass documented in [quickstart.md](./quickstart.md).

## Clarifications

### Session 2026-10-02

- Q: How far should the finalized sign convention reach — presentation only, or also the saved/underlying values? → A: End-to-end. The finalized convention is canonical from the frontend presentation, through the backend reconciliation logic, to the values stored in the database — the same sign governs display, computation, and persistence.
- Q: How much of the application should be locked until an employee has a company-granted access? → A: Everything is hidden except the subscription page and the sign-in page. A signed-in account with no granted access can reach only those two surfaces; every other application page is blocked.
- Q: What should the "animation improvement" cover? → A: Polish the existing transitions app-wide — a smoothness and consistency pass over the current animations (onboarding overlay, sidebar, list/table reveals, loaders, route/page transitions), honoring the system's reduced-motion preference.
- Q: Is a signed-in account limited to one active employee request at a time overall, or one per company? → A: One active request at a time overall — a new "Employee Request" is blocked until the existing pending request is cancelled or resolved, regardless of which company it targets.
- Q: Does being designated Manager grant application access on its own, or only the Company Dashboard shortcut? → A: The Manager flag is additive and only surfaces the "Company Dashboard" navigation entry for an account that is already using the application (holds a granted employee request). A manager who is not using the app opens the Company Dashboard directly with the company credentials; the manager who uses the app requests access to the company, grants themselves the request, and assigns themselves Manager, which then reveals the navigation entry.
- Q: When an employee leaves the company, is their record deleted, retained with a "Left" status, or kept as granted? → A: Hard delete — leaving removes the employee record from the company's records entirely (the same outcome as the company deleting the request), so a clean slate is left and returning requires a brand-new request.
- Q: How should a company onboarding request relate to the company account the Developer creates? → A: It is a standalone, view-only record whose only purpose is to be reviewed in the Admin Dashboard's "Company Requests" category. It has no status lifecycle and no link to account creation — the Developer onboards companies through a separate manual process after contacting them.
- Q: What happens to an employee when the Developer deletes their company? → A: Cascade delete — deleting a company deletes its employee (access request) records, so those accounts lose application access, while the underlying signed-in user accounts remain intact. The company is the cause and the request the effect.
- Q: Does company-granted access put the employee inside the company's data, or is the company only a gate to the employee's own application? → A: The company is only a gate — the granted account uses the application with its own personal data, and the company neither owns nor sees the employee's reconciliations or other personal data.
- Q: Can one account belong to more than one company at once? → A: One company at a time. A request creates the employee record (and ID); cancelling it deletes that record. Once a company grants access, the subscription page is closed to the account, and making a new request requires leaving the current company first (which deletes the current employee record).
- Q: Who can assign the "Manager" role? → A: Anyone with access to the Company Dashboard (the company account and any existing Managers) can assign or remove the Manager role for any account.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A company sees, searches, grants, and deletes employee requests (Priority: P1)

A company signs into its Company Dashboard and finds every employee who has requested access to it, each with their name, their `adam-` prefixed ID, and their request status. A single search box lets the company filter the list by typing either a name or an ID — the system decides which one the input is, with no mode to choose. For any pending request the company can **grant access** (admitting that specific account to the application) or **delete** the request (removing it from the company's records).

**Why this priority**: This is the core wiring of the feature. Until requests become real, searchable, actionable rows bound to the company, the dashboard and every later edge case are inert.

**Independent Test**: Submit an employee request for a company, sign into that company's dashboard, confirm the request appears, filter the list by typing part of the name and part of the ID (both match), then grant one request and delete another and confirm both outcomes persist.

**Acceptance Scenarios**:

1. **Given** an employee has submitted an access request for a company, **When** the company opens its dashboard, **Then** that employee appears in the company's Employees list with their name, employee ID, and status.
2. **Given** the Employees list, **When** the company types text into the search box, **Then** the list is filtered automatically by matching the employee ID first and the employee name second, with no field-selection mode required.
3. **Given** a pending employee request, **When** the company grants access, **Then** the request's status changes to granted and the account that submitted it is allowed to use the application.
4. **Given** an employee request, **When** the company deletes it, **Then** it is removed from the company's records and any access that employee had been granted for that company is revoked.
5. **Given** a company with no employee requests, **When** the Employees list is shown, **Then** a clear empty state is displayed instead of an empty table.

---

### User Story 2 - Granted access gates the application, and can be left (Priority: P1)

An employee signs in and, until a company grants their request, the entire application is hidden — only the subscription page and the sign-in page are reachable, and the reconciliation/upload area (`/upload-ai`) refuses them. Once a company grants access, that specific account can use the application. The application's navigation bar then shows the company the employee belongs to together with a **Leave company** action; leaving asks for confirmation and, on confirm, removes the account's access and returns the user to the subscription (or sign-in) layer. While an employee has granted access, the subscription page cannot be viewed again without first leaving the company. The "Individual Plans — coming soon" items are untouched.

**Why this priority**: This is the authorization core. It is what makes "granted access" meaningful, closes the bypass toward `/upload-ai` and every other page, and gives employees a supported exit. Without it, granting access changes nothing.

**Independent Test**: Sign in with an account that has no granted access and confirm every page except subscription/sign-in is blocked; have the company grant the request and confirm the account can now use the app and sees the company plus a Leave company action; confirm the subscription page is unreachable until the user leaves, then confirm leaving returns them to the subscription/sign-in layer and re-blocks the app.

**Acceptance Scenarios**:

1. **Given** a signed-in employee with no company-granted access, **When** they open any application page other than the subscription or sign-in page (including `/upload-ai`), **Then** access is denied, the page is hidden, and they are directed to the subscription page.
2. **Given** a signed-in employee whose request a company has granted, **When** they open the application, **Then** they can use it without re-requesting access.
3. **Given** an employee with granted access, **When** the application navigation bar is shown, **Then** it displays the company the employee belongs to and a **Leave company** action.
4. **Given** the "Leave company" action, **When** the employee activates it, **Then** a confirmation is required; on confirm, the employee's record is deleted from the company's records, their access is removed, and they are returned to the subscription (or sign-in) layer.
5. **Given** an employee with granted access, **When** they attempt to open the subscription page, **Then** they cannot view it unless they first leave the company.
6. **Given** a signed-in employee who already has an active pending request, **When** they click "Employee Request", **Then** they are told they already have a pending request and must cancel it first; cancelling deletes that request from the company's records.

---

### User Story 3 - Company onboarding requests reach the Admin Dashboard and the Developer's inbox (Priority: P2)

When a company successfully submits the "Company Request" onboarding flow, the submission is stored and appears in the Admin Dashboard under **Company Requests** with the details the company gave. The category is view-only — it exists so the Developer can read the request; it is not tied to company account creation, which the Developer performs separately after contacting the company. At the same time, a simple notification email about the new request is sent to the Developer at `ArhamBrowser@gmail.com`. Everything shown in these views is real data — no sample rows remain.

**Why this priority**: It closes the acquisition loop opened by the onboarding flow, and it removes the last of the placeholder data from the company/admin surfaces. It depends on the onboarding form already existing, so it follows the P1 wiring.

**Independent Test**: Submit the company onboarding flow, open the Admin Dashboard's Company Requests category, confirm the new request with all its details is listed, and confirm the notification email was sent to `ArhamBrowser@gmail.com`.

**Acceptance Scenarios**:

1. **Given** the company onboarding flow, **When** a company submits it successfully, **Then** the request is stored and appears in the Admin Dashboard's **Company Requests** category showing its Company Name, Role, Website/Socials, Email and Phone, and submission time.
2. **Given** a successful company request submission, **When** it is stored, **Then** a simple notification email describing the new request is sent to `ArhamBrowser@gmail.com`.
3. **Given** the Company Requests category with no submissions, **When** it is opened, **Then** a clear empty state is shown.
4. **Given** a listed company request in the Admin Dashboard, **When** the Developer opens it, **Then** the submitted details are shown so the Developer can contact the company.
5. **Given** the Company Dashboard, the Company Requests category, and the Admin company views, **When** they are displayed, **Then** no placeholder, sample, or dummy records are shown — all rows come from real submissions.

---

### User Story 4 - Admin sees how many employees each company has (Priority: P3)

In the Admin Dashboard companies table, each company row shows the number of employees associated with it. Hovering over that number opens a modal listing all the employees associated with that company, so the Developer can see at a glance who is using the application under each client.

**Why this priority**: Valuable administration insight once the employee wiring exists, but it depends on real employee data, so it follows the P1 work.

**Independent Test**: With a company that has associated employees, open the Admin Dashboard, confirm the row shows the employee count, hover it, and confirm the modal lists exactly that company's employees.

**Acceptance Scenarios**:

1. **Given** the Admin Dashboard companies table, **When** it is displayed, **Then** each company row shows a numeric count of its associated employees.
2. **Given** the employee count on a company row, **When** the Developer hovers over it, **Then** a modal opens listing all employees associated with that company (name, employee ID, and status).
3. **Given** a company with no associated employees, **When** its row is displayed, **Then** the count shows zero and the hover modal shows an empty state.

---

### User Story 5 - Manager role and a hidden Company Dashboard entry (Priority: P3)

A company can designate any account associated with it as a **Manager**. A manager who is not an application user reaches the Company Dashboard directly with the company credentials; a manager who *is* using the application requests access to the company, grants the request to themselves, and assigns themselves Manager. Only that special case — an account that is both using the application and a Manager — gains a **Company Dashboard** entry in the main application's navigation bar, so the manager can open the dashboard without remembering its address, while the dashboard's address stays hidden from everyone else.

**Why this priority**: It makes the dashboard reachable for the people who run it without exposing the route, but it builds on the employee/list wiring, so it ranks below the P1 and P2 work.

**Independent Test**: In the Company Dashboard, mark an associated account as Manager; confirm that account's application navigation bar gains a "Company Dashboard" entry that opens the dashboard, and confirm a non-manager account sees no such entry and no dashboard address anywhere.

**Acceptance Scenarios**:

1. **Given** the Company Dashboard employee list, **When** a user with dashboard access designates an account as Manager, **Then** that account gains the Manager role and this is visible in the dashboard.
2. **Given** an account that is both using the application and designated as a Manager for a company, **When** the application navigation bar is shown, **Then** it displays a **Company Dashboard** entry.
3. **Given** the "Company Dashboard" navigation entry, **When** the manager activates it, **Then** the Company Dashboard opens without the manager having been given its address.
4. **Given** an account that is neither a Manager nor an authorized company user, **When** they use the application, **Then** no "Company Dashboard" entry is shown and the dashboard's address is not revealed anywhere in the application.
5. **Given** an account with access to a company it manages, **When** it submits an employee request to that company, **Then** it can grant itself access from the Company Dashboard.

---

### User Story 6 - One finalized sign convention everywhere (Priority: P2)

Everywhere the application presents reconciliation categories and amounts — the categorized results tables, per-category subtotals, the adjustment panels, the reconciliation totals and verdict, saved/history views, and any export — the amounts carry the finalized sign for their category, in both Bank and Vendor reconciliation modes. The same convention is canonical behind the scenes: it governs how the reconciliation logic classifies and computes the categories and the signs persisted to the database, so frontend, backend, and stored data never disagree. The table the app must honor:

- **Bank** — Unpresented Checks (credited in cashbook) → **negative**; Uncleared Checks (debited in cashbook) → **positive**; Bank Debited but not credited in cashbook → **positive**; Bank Credited but not debited in cashbook → **negative**.
- **Vendor** — Unpresented Checks (credited in cashbook) → **negative**; Uncleared Checks (debited in cashbook) → **positive**; Vendor Debits → **negative**; Vendor Credit → **positive**.

**Why this priority**: The signs are accounting-correct outputs the finance user relies on; a mismatch anywhere undermines trust in every screen. It is independent of the dashboard wiring and can be delivered and verified on its own.

**Independent Test**: Run a reconciliation in Bank mode and one in Vendor mode, and confirm on every surface (results, subtotals, adjustment panel, totals/verdict, saved history, export) that each category shows exactly the finalized sign; confirm the same signs were computed and persisted, and repeat on a saved/history view.

**Acceptance Scenarios**:

1. **Given** a Bank-mode reconciliation, **When** its results are displayed, **Then** Unpresented Checks is negative, Uncleared Checks is positive, Bank Debited but not credited is positive, and Bank Credited but not debited is negative, on every surface.
2. **Given** a Vendor-mode reconciliation, **When** its results are displayed, **Then** Unpresented Checks is negative, Uncleared Checks is positive, Vendor Debits is negative, and Vendor Credit is positive, on every surface.
3. **Given** a reconciliation is saved, **When** it is later viewed in history or exported, **Then** the same finalized signs are shown as when it was produced, because the same signs were computed and stored.
4. **Given** the finalized signs, **When** the reconciliation totals and verdict are computed, **Then** they remain internally consistent with those signs (the app never shows a sign that contradicts its own verdict).

---

### User Story 7 - Smoother animations app-wide (Priority: P3)

The application's existing transitions are polished for smoothness and consistency across the whole app — the company onboarding overlay, the dashboards' sidebar and section changes, list/table reveals, loading states, and route/page transitions — without changing what any screen does. Every polished animation continues to honor the system's reduced-motion preference.

**Why this priority**: Presentation polish that does not block any functional flow, so it ranks last.

**Independent Test**: Exercise the application's key transitions (onboarding overlay, sidebar section change, employee table reveal, loading states, page navigation) and confirm each plays smoothly and consistently, and that with reduced motion enabled the motion-heavy parts are skipped or softened while every screen stays fully usable.

**Acceptance Scenarios**:

1. **Given** the application's key transitions, **When** they play, **Then** each is smooth and consistent with the others, with no abrupt or janky changes.
2. **Given** the system's reduced-motion preference is enabled, **When** the affected screens animate, **Then** motion-heavy animation is skipped or softened while the screen remains fully usable.

---

### Edge Cases

- **Employee with no granted access opens any application page directly** → the page is hidden/blocked and they are directed to the subscription page; only the subscription and sign-in pages remain reachable.
- **Employee with granted access opens the subscription page directly** → they cannot view it without first leaving the company.
- **Employee clicks "Leave company"** → a confirmation is shown; cancelling keeps their access and current state; confirming deletes their record from the company's records, revokes their access, and returns them to the subscription (or sign-in) layer.
- **Employee who already has an active pending request clicks "Employee Request"** → the new request (to any company) is blocked with a message telling them to cancel the existing one; cancelling deletes the pending request from the company's records, after which a new request may be made.
- **Company deletes an employee request that had already been granted** → the request is removed from the company's records and that account's application access is revoked.
- **Company grants access, then the employee leaves the company** → the employee's access ends and does not silently reappear.
- **Developer deletes a company** → that company's employee (access request) records are deleted with it and those accounts lose application access; the underlying signed-in user accounts remain intact (the company is the cause, the request the effect).
- **Search input matches neither a name nor an ID** → the list shows a clear "no matches" state without error.
- **Search input could plausibly match both a name and an ID** → ID matches take precedence over name matches.
- **Company submits a request while the notification email cannot be sent (provider/network error)** → the request is still stored and visible in the Admin Dashboard; the email failure does not lose the request.
- **Company has no employees** → the Admin row shows a count of zero and the hover modal shows an empty state.
- **Company Requests category has no submissions** → a clear empty state is shown.
- **Non-manager account uses the application** → no "Company Dashboard" entry appears and the dashboard address is never revealed.
- **Manager account with no employee access of its own** → it can still reach the Company Dashboard via the navigation entry, and can request/grant itself employee access from there.
- **A reconciliation is produced in one mode and viewed later** → the signs shown always match the finalized table for that mode, because the same signs were computed and stored.
- **A category has no transactions** → its subtotal is shown as zero and its sign is not misleading.
- **Reduced motion is enabled** → polished animations degrade gracefully and every screen stays fully usable.

## Requirements *(mandatory)*

### Functional Requirements

**Company-Employee Dashboard Wiring**

- **FR-001**: When an employee submits an access request for a company, the request MUST be recorded against that company and MUST appear in that company's dashboard employee list.
- **FR-002**: The Company Dashboard MUST provide a single search box that filters the employee list automatically by employee ID first and employee name second, with no user-selected search mode.
- **FR-003**: The company MUST be able to grant access to an employee request; granting MUST enable the specific signed-in account that submitted the request to use the application.
- **FR-004**: The company MUST be able to delete an employee request; deleting MUST remove it from the company's records and MUST revoke any access that employee had been granted for that company.
- **FR-005**: The Company Dashboard MUST show the status of each employee request (e.g., pending, granted) and update it immediately after a grant or delete.
- **FR-006**: A successful "Company Request" onboarding submission MUST be persisted and MUST appear in the Admin Dashboard's "Company Requests" category with its Company Name, Role, Website/Socials, Email and Phone, and submission time. The category is view-only: a request MUST NOT create, link to, or modify a company account, and company accounts continue to be created by the Developer through a separate manual Admin process.
- **FR-007**: On a successful company request submission, the system MUST send a simple notification email about the new company request to `ArhamBrowser@gmail.com`. A failure to send the email MUST NOT prevent or roll back the stored request.
- **FR-008**: All placeholder, sample, and dummy data backing the Company Dashboard, the Company Requests category, the employee lists, and the Admin company views MUST be removed and replaced by real data.
- **FR-009**: A signed-in user MUST NOT be able to use the application without a company-granted employee access. Except for the subscription page and the sign-in page, every application route — including `/upload-ai` and the reconciliation area — MUST be hidden and blocked for an account with no granted access, and that account MUST be directed to the subscription page.
- **FR-010**: A granted access MUST be bound to the specific signed-in account that requested it, so access follows that account rather than being inferred from a shared employee ID alone.
- **FR-011**: The signed-in user's identity and the employee information MUST be linked and reference each other so future features can traverse the relationship in both directions.

**Signs Finalized Throughout the App**

- **FR-012**: In Bank mode, the presented sign for each category MUST be: Unpresented Checks = negative (−); Uncleared Checks = positive (+); Bank Debited but not credited in cashbook = positive (+); Bank Credited but not debited in cashbook = negative (−).
- **FR-013**: In Vendor mode, the presented sign for each category MUST be: Unpresented Checks = negative (−); Uncleared Checks = positive (+); Vendor Debits = negative (−); Vendor Credit = positive (+).
- **FR-014**: The sign convention in FR-012 and FR-013 MUST be canonical end-to-end. It MUST govern: (a) the presented amounts everywhere the categories appear — categorized results, per-category subtotals, adjustment panels, reconciliation totals and verdict, saved/history views, and any export; (b) the backend reconciliation logic that classifies and computes the categories; and (c) the values persisted to the database. Frontend, backend, and stored data MUST NOT disagree, and the reconciliation totals and verdict MUST remain internally consistent with the presented signs.

**Edge Cases**

- **FR-015**: The main application navigation bar MUST offer a "Leave company" action to an employee with granted access. Leaving MUST require confirmation and, on confirm, MUST delete that employee's record from the company's records (the same outcome as the company deleting the request), revoke their access, and return them to the subscription or sign-in layer.
- **FR-016**: An employee with granted access MUST NOT be able to view the subscription page again without first leaving the company.
- **FR-017**: An employee who already has an active (pending) request MUST NOT be able to submit another "Employee Request" to any company; they MUST be prompted to cancel the existing request, and cancelling MUST delete that request from the company's records. Only one active request per signed-in account may exist at a time.
- **FR-018**: The Admin Dashboard companies table MUST display, for each company, the number of employees associated with it; hovering over that count MUST open a modal listing all employees associated with that company (name, employee ID, status), with an empty state when there are none.
- **FR-019**: A company MUST be able to designate any account associated with it as a "Manager", and MUST be able to remove the designation. Any user with access to the Company Dashboard (the company account and existing Managers) MUST be able to assign or remove the Manager role for any account. The Manager designation is additive and MUST NOT by itself grant application access. An account that manages a company MUST also be able to submit an employee request to that company and grant itself access from the Company Dashboard.
- **FR-020**: For an account that is both using the application (holds a granted employee access) and designated as a Manager of a company, the application navigation bar MUST show a "Company Dashboard" entry that opens the Company Dashboard without requiring the address to be memorized. A manager who is not using the application reaches the Company Dashboard through the existing company credentials. The Company Dashboard's address MUST NOT be revealed, linked, or listed anywhere in the application for accounts that are neither Managers nor authorized company users.
- **FR-021**: The "Individual Plans — coming soon" items on the subscription page MUST remain present and unchanged.
- **FR-022**: The application's existing animations MUST be polished app-wide for smoother, more consistent transitions (including the onboarding overlay, dashboards' sidebar and section changes, list/table reveals, loading states, and route/page transitions), without changing what any screen does. The polish MUST honor the system's reduced-motion preference.
- **FR-023**: Deleting a company MUST cascade to its employee (access request) records: every employee record associated with the deleted company MUST be deleted with it, and those accounts MUST immediately lose application access. The underlying signed-in user accounts MUST NOT be deleted — only the employee records are removed.
- **FR-024**: Company-granted access MUST act solely as an authorization gate: a granted account uses the application with its own data, and the company MUST NOT gain access to or visibility of the employee's reconciliations or other personal data by virtue of granting access.
- **FR-025**: An account MUST belong to at most one company at a time. While it holds a granted membership, the subscription page is unreachable (FR-016) and a new request requires leaving the current company first; leaving deletes the employee record (FR-015).

### Key Entities *(include if feature involves data)*

- **Employee (access request)**: (Existing, extended) a person who has requested access to a company. Gains: a request status that can move from pending to granted, the ability to be deleted from a company's records (including self-deletion by leaving the company), an exclusive relationship from the requesting signed-in account (at most one active request, and at most one company membership, at a time), and an optional Manager flag when the account is designated as a manager. The record is deleted when its company is deleted (cascade); the linked user account is not.
- **User Account**: (Existing) the signed-in application account (Google). Newly referenced by employee records both ways so a signed-in user can be resolved to their employee/membership information and vice versa.
- **Access Grant**: The realized authorization that lets a specific account use the application for a company (created when a company grants a request, removed when the request is deleted or the employee leaves). It is an entry gate only — it grants no ownership of or visibility into the account's data.
- **Company**: (Existing) the Developer-onboarded client organization; now the owner of a searchable employee request list and the assigner of Manager roles. Deleting a company cascades to delete its employee records (but not the user accounts).
- **Company Request (onboarding)**: (New, persisted) a submission from the "Company Request" onboarding flow. Attributes: Company Name, Role, Website/Socials, Email, Phone, and submission time. It is view-only with no status lifecycle and no link to company account creation; the Developer onboards companies through a separate manual process after contacting them. Replaces the placeholder data previously shown in the Admin Dashboard.
- **Manager**: A flag on an account associated with a company. When that account is also using the application (holds a granted employee access), the flag surfaces the "Company Dashboard" navigation entry without exposing the address. The flag alone does not grant application access; a manager not using the application reaches the dashboard through the company credentials. The role can be assigned or removed by any user with access to the Company Dashboard.
- **Notification Email**: A simple message reporting a new company request, sent to `ArhamBrowser@gmail.com`. Not a stored entity beyond its delivery outcome.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of employee requests a company receives appear in that company's dashboard employee list, and 0 sample/dummy rows remain in that list.
- **SC-002**: Typing into the company search box filters by both name and ID with 0 mode selections required, and ID matches take precedence when both could match.
- **SC-003**: 100% of accounts without a company-granted access can reach only the subscription page and the sign-in page, and 100% of granted accounts can use the application.
- **SC-004**: 100% of granted employees can see and use the "Leave company" action, and after leaving, 0 of them retain application access and 0 leave a lingering employee record on the company.
- **SC-005**: 100% of successful company request submissions produce both a stored request visible in the Admin Dashboard and a notification email to `ArhamBrowser@gmail.com`, in under one minute.
- **SC-006**: 0 dummy/placeholder records remain anywhere in the Company Dashboard, Company Requests category, or Admin company views.
- **SC-007**: 100% of displayed, exported, computed, and stored category amounts match the finalized sign table in both Bank and Vendor modes, and the reconciliation verdict never contradicts the presented signs.
- **SC-008**: 100% of Admin company rows show an employee count whose hover modal lists exactly that company's employees, with an empty state at zero.
- **SC-009**: 100% of granted employees cannot reach the subscription page without leaving the company, and 0 non-manager accounts see a "Company Dashboard" entry.
- **SC-010**: A company representative can grant access, delete a request, or assign a Manager, and see the effect reflected across the application (including the employee's navigation bar) in under one minute.
- **SC-011**: 100% of employees with an active pending request are blocked from submitting a second request to any company until the first is cancelled, and cancelling removes the request from the company's records in 100% of cases.
- **SC-012**: Across the application's key transitions, 0 visibly abrupt or janky transitions remain, and with reduced motion enabled 0 motion-heavy animations play while 100% of screens stay usable.
- **SC-013**: With access granted, 100% of employees keep their own application data, and 0 companies can view an employee's reconciliations by virtue of having granted access.
- **SC-014**: 0 accounts hold a membership in more than one company at the same time; 100% of attempts to join a second company while holding a membership are blocked until the account leaves the current company.

## Assumptions

- The company dashboard's data (employees, requests, search) must read from the backend rather than placeholder data; the Admin company views and Company Requests category likewise render real submissions.
- "Access" means the employee's signed-in application account is authorized because a company granted their request; a grant is bound to the requesting account, while the `adam-` ID remains the human-facing handle.
- The application access gate covers the end-user application: without a granted access, only the subscription page and the sign-in page are reachable and every other page is hidden. The Company Dashboard and the hidden Admin Dashboard are separate surfaces with their own independent authentication (company credentials, admin credentials, and Manager access) and sit outside the employee gate.
- The finalized sign convention is canonical end-to-end — presentation, backend reconciliation logic, and stored database values all use it — so the totals/verdict arithmetic is updated rather than left contradicting the display.
- The notification email is a simple informational message (who requested, and their submitted details) sent to `ArhamBrowser@gmail.com`; it is not a branded template and carries no credentials.
- Company onboarding requests and company account creation are separate: requests are stored solely for the Developer to view (and to trigger the notification email), and never create, link to, or modify a company account.
- An employee record is the effect of a request to a company (the cause); therefore deleting a company cascades to delete its employee records, while the user accounts that submitted those requests remain intact.
- The company relationship is an authorization gate, not a data boundary: granting access does not move, share, or expose the employee's reconciliation data to the company.
- An account holds at most one company membership at a time; switching companies is done by leaving the current one (which deletes the employee record) and making a fresh request.
- A "Manager" is an account associated with a company; designating one does not by itself create a new login or grant application access — the manager signs in with their normal account, and the "Company Dashboard" navigation entry appears only for a manager who is also using the application.
- The Company Dashboard remains at its existing hidden address; the "Company Dashboard" navigation entry is simply a shortcut for managers, and the address stays undiscoverable for everyone else.
- The company onboarding form and the Company Dashboard shell already exist from earlier specifications; this specification wires them to real data and adds the described behavior rather than rebuilding the UI.
- The animation work is a polish pass over existing transitions app-wide; it introduces no new screens or functional behavior.
- The Individual Plans "coming soon" items remain intentionally inert.
- No tests are to be written for this feature, per the Developer's standing instruction — no test files, suites, cases, or test tasks on either side. Verification is entirely the manual pass in quickstart.md.
