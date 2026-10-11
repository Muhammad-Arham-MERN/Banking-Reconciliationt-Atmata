# Feature Specification: Employee Access Request (Subscription Layer)

**Feature Branch**: `009-employee-access-request`  
**Created**: 2026-09-30  
**Status**: Draft  
**Input**: User description: "Second part of the trial and payment system. Part one was the Admin Dashboard (008) where the Developer adds and manages client companies. This specification deals with the Employee part, which sits between the Developer part (done) and the Company Dashboard (a later specification). An employee signs in, then instead of the application they see a subscription layer offering 'Company Request' and 'Employee Request'. This specification covers the Employee Request flow: the employee submits their name, a unique `adam-` prefixed ID, and the company they want access to; the request is stored and waits for the company (later specification) to grant access. Keep it concise and simple — no tests."

## Clarifications

### Session 2026-09-30

- Q: Employee ID uniqueness scope — global, composite, or pending-only? → A: Composite — an ID may hold at most one request per company; the same ID requesting a different company is recorded as a new request.
- Q: What identifies the requested company on the stored record? → A: The company's stable ID (foreign key) plus a snapshot of the company name as displayed at request time.
- Q: What are the `adam-` ID format and normalization rules? → A: After the prefix, 6–12 characters of lowercase letters and digits; typed input is trimmed and lowercased, the prefix is added when missing, and uniqueness is compared case-insensitively.
- Q: Where does the dedicated sign-in page live? → A: A dedicated `/login` route; signed-out visits to `/` redirect to `/login`, and signed-in visits to `/` redirect to the Subscription page.
- Q: How is a company-list fetch failure handled? → A: Show a distinct "Couldn't load companies" error with a Retry action and keep Submit disabled until the list loads.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Sign in and land on the subscription choice page (Priority: P1)

An employee opens the application and signs in with their existing account. Instead of landing directly in the reconciliation application, they arrive on a **Subscription** page titled "Reconciliation AI for Companies" presenting two options — **Company Request** and **Employee Request** — alongside an **Individual Plans** panel. Sign-in now lives on its own dedicated page/route (`/login`) rather than being embedded as a component, and signing in with Google no longer triggers the browser's "Leave site?" confirmation.

**Why this priority**: This is the new gate between authentication and the application; nothing else in this feature is reachable without it.

**Independent Test**: Sign in with a valid account and confirm arrival at the subscription page with the title, both actions, and the plans panel visible; confirm no "Leave site?" prompt appears during Google sign-in.

**Acceptance Scenarios**:

1. **Given** a signed-out visitor, **When** they open the application, **Then** they are shown the sign-in page on its own dedicated route (`/login`).
2. **Given** a successful sign-in, **When** authentication completes, **Then** the user is taken to the subscription page showing "Reconciliation AI for Companies", "Company Request", "Employee Request", and the Individual Plans panel.
3. **Given** the sign-in page, **When** the user starts Google sign-in, **Then** no browser "Leave site?" unload confirmation is shown.
4. **Given** a user who is not signed in, **When** they open the subscription page directly, **Then** they are redirected to sign in.
5. **Given** a signed-in user, **When** they open the application root `/`, **Then** they are redirected to the subscription page.

---

### User Story 2 - Submit an employee access request (Priority: P1)

From the subscription page the employee clicks **Employee Request**, and a popup dialog asks for their **Employee Name**, their **ID**, and the **Company** they are requesting access to. The ID can be typed or generated randomly on the spot, and is always issued with an `adam-` prefix. The company is chosen from a list of the companies the Developer has onboarded, each shown with its logo (or a placeholder when none exists). Submitting sends the request and shows a confirmation.

**Why this priority**: This is the core action of the feature — how an employee asks a company to grant them access.

**Independent Test**: Click "Employee Request", fill the form (using a generated ID), choose a company, submit, and confirm the success message; verify the request is recorded.

**Acceptance Scenarios**:

1. **Given** the subscription page, **When** the employee clicks "Employee Request", **Then** a popup dialog opens with Employee Name, ID, and Company to Request.
2. **Given** the dialog, **When** any required field is empty, **Then** the request is not sent and the missing fields are indicated.
3. **Given** the ID field, **When** the employee asks to generate one, **Then** a unique `adam-` prefixed ID is generated into the field and remains editable.
4. **Given** the ID field, **When** the employee enters a value, **Then** the stored ID carries the automatic `adam-` prefix.
5. **Given** the Company to Request dropdown, **When** it opens, **Then** it lists all companies the Developer has added, each with its logo or a placeholder when none exists.
6. **Given** a completed dialog, **When** the employee submits, **Then** the request is stored and the employee sees "Your request has been sent to the designated company successfully, you may contact them to grant you access by providing them your ID or Name".
7. **Given** an ID that has already requested the selected company, **When** the request is submitted, **Then** the request is rejected with a clear message and no duplicate is created.
8. **Given** the companies list cannot be loaded, **When** the dialog is open, **Then** it shows a distinct error with a Retry action and Submit remains disabled.

---

### User Story 3 - See the other plan options (Priority: P2)

Alongside the employee request, the subscription page shows a **Company Request** action and an **Individual Plans** panel with two options — **Rs 300 for 1 day** and **Rs 1500 for 1 month**. These are visible and clickable but intentionally do nothing yet.

**Why this priority**: Surfaces the intended product menu without building the future flows, keeping the page coherent.

**Independent Test**: Click "Company Request" and both plan buttons and confirm the page state is unaffected.

**Acceptance Scenarios**:

1. **Given** the subscription page, **When** the user clicks "Company Request", **Then** nothing happens (reserved for a later specification).
2. **Given** the Individual Plans panel, **Then** it shows "Rs 300 - 1 day" and "Rs 1500 - 1 month".
3. **Given** either plan button, **When** clicked, **Then** no navigation or action occurs.

---

### Edge Cases

- An employee ID that has already requested the selected company → the request is rejected and the employee is asked to choose or generate another.
- Required fields left empty or whitespace → the request is not sent and the missing fields are indicated.
- No companies have been onboarded yet → the Company dropdown is empty and communicates that no companies are available.
- The companies list fails to load (API or network error) → the dialog shows a distinct error with a Retry action and Submit stays disabled until the list loads.
- The employee types an ID that already includes the `adam-` prefix → the prefix is not duplicated.
- The employee types an ID in a different letter case → it is normalized to lowercase before uniqueness is checked.
- A signed-out user opens the subscription page directly → redirected to sign in.
- The same employee submits more than one request over time → each request is recorded, including one per different company under the same ID; the company decision is handled by the later company specification.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sign-in MUST live on its own dedicated page/route at `/login`, reachable directly, rather than being an embedded component. Signed-out visits to `/` MUST redirect to `/login`, and signed-in visits to `/` MUST redirect to the Subscription page.
- **FR-002**: Starting Google sign-in MUST NOT trigger the browser's "Leave site?" unload confirmation.
- **FR-003**: After a successful sign-in, the user MUST land on the Subscription page instead of the application.
- **FR-004**: The Subscription page MUST display the title "Reconciliation AI for Companies" and two actions: "Company Request" and "Employee Request".
- **FR-005**: On the Subscription page, "Company Request" MUST be present and MUST perform no action (reserved for a later specification).
- **FR-006**: The Subscription page MUST be reachable only by signed-in users; unauthenticated visitors MUST be redirected to sign in.
- **FR-007**: "Employee Request" MUST open a popup dialog to request access.
- **FR-008**: The dialog MUST capture Employee Name (required), ID (required), and Company to Request (required).
- **FR-009**: The Company to Request field MUST present a list populated from the companies the Developer has added, each showing its logo when available or a placeholder when it is not. If the list cannot be loaded, the dialog MUST show a distinct error with a Retry action and MUST keep Submit disabled until the list loads.
- **FR-010**: The ID field MUST offer on-the-spot random generation, and the generated value MUST remain editable.
- **FR-011**: Every employee ID MUST automatically begin with the prefix `adam-`, whether typed or generated; employees never type the prefix themselves. After the prefix, an ID MUST be 6–12 characters of lowercase letters and digits; typed input MUST be trimmed and lowercased, and the prefix MUST be added when it is missing.
- **FR-012**: Submitting the dialog MUST record the request and show the confirmation: "Your request has been sent to the designated company successfully, you may contact them to grant you access by providing them your ID or Name".
- **FR-013**: The system MUST reject a request that would create a second request for the same company under an already-used ID (compared case-insensitively), with a clear message, without creating a duplicate. The same ID requesting a different company is recorded as a new request.
- **FR-014**: The system MUST reject a request that is missing any required field.
- **FR-015**: All employee requests MUST be stored in a dedicated Employees record set, separate from companies and from the application's user accounts, and MUST survive application restarts.
- **FR-016**: Each stored request MUST record the employee's name, their `adam-` prefixed ID, the requested company as its stable company ID together with a snapshot of the company name shown when requested, the signed-in account that submitted it, the request status, and when it was made. New requests MUST start in a pending state; acceptance or denial by the company is handled by a later specification.
- **FR-017**: The employee ID MUST be the primary reference used to look up an employee. Uniqueness MUST be enforced on the combination of employee ID and requested company, so an ID may hold one request per company but never two for the same company.
- **FR-018**: The Subscription page MUST include an "Individual Plans" panel showing exactly two options — "Rs 300 - 1 day" and "Rs 1500 - 1 month" — both clickable and both performing no action (reserved for a later specification).

### Key Entities

- **Employee (access request)**: A person who has requested access to a company from the subscription page. Attributes: Employee Name, Employee ID (`adam-` prefixed, 6–12 lowercase letters/digits after the prefix), requested Company (stored as the company's stable ID plus the name snapshot shown when requested), requesting account (the signed-in user who submitted it), request status (starting at pending), and creation time. Uniqueness is enforced on Employee ID + requested Company, so one employee ID may hold at most one request per company. Stored in a dedicated Employees record set.
- **Company**: (Existing) the Developer-onboarded client organization whose name and logo populate the request dropdown. This specification does not change the company record set.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A signed-in employee reaches the Subscription page in under one minute and sees the title, both request actions, and the plans panel.
- **SC-002**: 100% of sign-in attempts with Google produce no browser "Leave site?" confirmation.
- **SC-003**: An employee can complete an access request (name, ID, company) in under 90 seconds and receives the confirmation message.
- **SC-004**: 100% of stored employee IDs begin with `adam-` and match the `adam-` + 6–12 lowercase letters/digits shape; 0 requests duplicate an existing request for the same company under the same ID (case-insensitive).
- **SC-005**: 100% of requests missing any required field are rejected and no incomplete record is stored.
- **SC-006**: The Company dropdown shows 100% of the companies the Developer has added, each with a logo or a placeholder; when the list cannot be loaded, the dialog shows the error state and 0 submissions are possible.
- **SC-007**: Employee requests persist across an application restart — 100% of submitted requests remain available afterwards.
- **SC-008**: "Company Request" and the two Individual Plans buttons produce no state change or navigation in 100% of clicks.

## Assumptions

- Employee identity is the existing application sign-in (Google); the request records which signed-in account submitted it so the company can later grant that account access. No separate employee username/password is introduced.
- The Employee ID is a self-chosen or auto-generated handle, unique per company: an employee may request several companies under one ID, but may hold only one request per company. Its shape is the `adam-` prefix followed by 6–12 lowercase letters and digits. The prefix is applied by the system and never typed by the employee.
- New requests start in a pending state; the company's accept/deny decision and the company-facing dashboard belong to a later specification.
- The subscription page is the post-sign-in landing page. Gating the existing application pages behind a granted subscription is deferred to the later specification.
- "Company Request" and the Individual Plans buttons are intentional placeholders — visible, clickable, and inert — until their later specifications.
- The dropdown's company list is read from the companies the Developer manages on the hidden AdminDashAccess dashboard.
- No automated tests are included, per the Developer's standing instruction; verification is a manual pass.
