# Feature Specification: Company Dashboard & Onboarding Flow

**Feature Branch**: `010-company-dashboard-onboarding`  
**Created**: 2026-10-01  
**Status**: Draft  
**Input**: User description: "Final block of the employee/company dashboard system, after the Admin Dashboard (008) and the Employee Access Request layer (009). A company arrives at the application, signs in, and clicks 'Company Request'; a full-screen cinematic onboarding overlay plays and then asks four questions (Company Name, Role, Website/Socials, Email and Phone) one at a time, guided by the bored-boss character, and ends with a typed success message and an auto-fade. Requests surface in the Admin Dashboard under a new 'Company Requests' category. The Developer contacts the company, creates their account, and hands over credentials; the company then signs in to a new Company Dashboard with a two-section sidebar — Employees (with a shadcn table and a Grant Access action per row) and Subscription (a 'Start 30 days free trial' card). Frontend-structure heavy, one small company sign-in API only, no tests."

## Clarifications

### Session 2026-10-01

- Q: The description says both "connect with backend only for this feature" (company sign-in) and "we will not implement any Backend in this." Which is it? → A: Not a contradiction — this specification implements the **company sign-in API only** (validating against the company record the Developer created in 008). No other backend/APIs are added; the request submission, employee list, and subscription are frontend structure with placeholder data.
- Q: Is the Admin Dashboard "Company Requests" category part of this specification? → A: Yes — add the "Company Requests" category and a request detail view to the existing AdminDashAccess dashboard. Its data wiring stays deferred (no request API this specification), so it renders from placeholder data with an empty state.
- Q: How is the contact question structured — one step or two? → A: One contact step capturing both Email and Phone Number ("Email and Phone Number"), keeping the flow at exactly four questions.
- Q: Should a submitted company request be stored on the client (e.g., browser storage) so the Admin view can see it? → A: No — the submission is a purely visual confirmation; nothing is persisted on the client or the server. The Admin "Company Requests" view renders placeholder data with an empty state until the later backend specification.
- Q: How long should a company's sign-in to the Company Dashboard stay valid? → A: 24 hours — the session persists across browser restarts and expires 24 hours after sign-in, after which the Company Name and Password are required again.
- Q: What are the exact labels for the two Company Dashboard sidebar sections? → A: "Employees" and "Subscription". The description's alternative wordings ("Employee Requests" and "Payments") are not used.
- Q: How strictly should the four onboarding answers be validated? → A: Basic format checks — Company Name and Role must be non-empty; Website/Socials must be a recognizable web address or social handle; Email must look like an email; Phone must look like a phone number. Malformed answers block advancing.
- Q: How should the entered Company Name be matched at sign-in? → A: Case-insensitively and after trimming surrounding whitespace, so casing or stray spaces do not cause a rejection.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cinematic "Company Request" onboarding flow (Priority: P1)

A company representative is on the subscription page and clicks **Company Request**. A full-screen block in the application's cherry theme color slides in and covers everything, settling with a smooth motion-blur feel. Stars then streak outward from the center toward the viewer, conveying motion into the screen. In the center, a company-building illustration starts small and grows steadily, as if the camera is flying toward it. After about five seconds of approach, the view enters one of the building's lit windows and the building fades away. The bored-boss character then appears near the lower-center — not pinned to the very bottom — as a guide for the onboarding. The visitor is asked four questions, one at a time, each fading in: **Company Name**, **Role**, **Website/Socials**, and **Email and Phone Number**. The boss keeps tapping his pen while the visitor types; each time the visitor advances, he plays a brief hands-up pose and resumes. After the final answer he smiles. All cinematic and character animation then clears and a text-generation effect writes: "Request Sent Successfully - Please Wait For The Team To Contact Your Representative". The overlay fades out automatically five seconds later, and a close ("cross") control at the top-right lets the visitor abandon the flow at any moment.

**Why this priority**: This is the acquisition entry point — the only way a company asks to be onboarded — and it supersedes the inert "Company Request" placeholder from the earlier specification.

**Independent Test**: On the subscription page, click "Company Request", watch the intro sequence play, then complete all four questions and confirm the boss states, the typed success line, the automatic close after five seconds, and that the top-right cross dismisses the overlay.

**Acceptance Scenarios**:

1. **Given** the subscription page, **When** the visitor clicks "Company Request", **Then** a full-screen cherry-themed block slides in, covers the viewport, and settles with a motion-blur feel.
2. **Given** the block has covered the screen, **When** the intro continues, **Then** stars streak from the center toward the viewer and a centered company-building illustration grows steadily.
3. **Given** the building has been approached for about five seconds, **When** the sequence finishes, **Then** the view enters one of the building's windows and the building fades away smoothly.
4. **Given** the intro is complete, **When** the first question appears, **Then** the bored-boss character is visible near the lower-center and the **Company Name** question fades in.
5. **Given** a question is shown, **When** the visitor types, **Then** the boss continues his pen-tapping idle motion.
6. **Given** the visitor has typed an answer, **When** they advance, **Then** the boss plays a brief hands-up pose, the current question is replaced by the next faded-in question, and the boss resumes tapping.
7. **Given** all four questions have been answered, **When** the last answer is submitted, **Then** the boss plays a smile and, after the animation clears, a text-generation effect writes "Request Sent Successfully - Please Wait For The Team To Contact Your Representative".
8. **Given** the success message has begun, **When** five seconds elapse, **Then** the overlay fades out automatically and the subscription page is shown again.
9. **Given** the overlay is open at any point, **When** the visitor clicks the top-right cross, **Then** the overlay dismisses immediately and no request is recorded.
10. **Given** a question is shown, **When** the visitor enters an answer that fails that question's format check (e.g., an invalid email, or a bare word in Website/Socials), **Then** they cannot advance and the field is flagged inline.

---

### User Story 2 - Company sign-in to the Company Dashboard (Priority: P1)

A company the Developer has onboarded opens the Company Dashboard route and is shown a sign-in form asking for **Company Name** and **Password**. Submitting checks the credentials against the company record the Developer created on the Admin Dashboard. Correct credentials open the dashboard; incorrect ones are rejected with a generic message. This is the only part of this specification that talks to the backend.

**Why this priority**: Nothing in the company dashboard is reachable without this gate, and it is the one behavior the Developer explicitly asked to wire to the backend now.

**Independent Test**: Open the Company Dashboard route signed-out, submit an unknown company or wrong password (denied, generic message), then submit the correct company name and password (dashboard opens).

**Acceptance Scenarios**:

1. **Given** a visitor who is not signed in to the Company Dashboard, **When** they open its route, **Then** they are shown a sign-in form asking for Company Name and Password, and no dashboard content is visible.
2. **Given** the sign-in form, **When** the visitor submits an unknown company name or an incorrect password, **Then** access is denied with a generic message that reveals neither field.
3. **Given** the correct Company Name and Password of a company the Developer onboarded, **When** the visitor submits them, **Then** the Company Dashboard opens.
4. **Given** a company that signed in less than 24 hours ago, **When** they load the Company Dashboard (including after reopening the browser), **Then** the dashboard content is shown without asking for credentials again.
5. **Given** a company whose 24-hour session has expired, **When** they load the Company Dashboard, **Then** they are shown the sign-in form again and must re-enter the Company Name and Password.

---

### User Story 3 - Company Dashboard with Employees and Subscription sections (Priority: P2)

After signing in, the company sees a dashboard with a sidebar containing exactly two sections: **Employees** and **Subscription**. The Employees section lists everyone associated with the company in a table, each row carrying a **Grant Access** checkmark action; the company uses it to admit employees who have asked for access. The Subscription section shows a small card reading "Start 30 days free trial", which is visible and clickable but does nothing yet.

**Why this priority**: This is the day-to-day surface the company uses to manage its people and see its plan, but it depends on the sign-in gate above.

**Independent Test**: Sign in as a company, confirm the two sidebar sections, confirm the Employees table shows rows with a Grant Access action that changes state when clicked, and confirm the Subscription card is present and inert.

**Acceptance Scenarios**:

1. **Given** a signed-in company, **When** the dashboard loads, **Then** a sidebar is shown with exactly the sections "Employees" and "Subscription".
2. **Given** the Employees section, **When** it is displayed, **Then** the company's associated employees are listed in a table, each row offering a "Grant Access" action.
3. **Given** an employee row, **When** the company clicks "Grant Access", **Then** the row's state visibly changes to indicate access was granted.
4. **Given** the Employees section with no associated employees, **When** it is displayed, **Then** a clear empty state is shown instead of an empty table.
5. **Given** the Subscription section, **When** it is displayed, **Then** a card reading "Start 30 days free trial" is shown, and clicking it performs no action.

---

### User Story 4 - Company Requests category in the Admin Dashboard (Priority: P3)

The Developer opens the existing hidden Admin Dashboard (AdminDashAccess) and finds a new **Company Requests** category listing the companies that submitted an onboarding request. Opening a request shows the company's submitted details — Company Name, Role, Website/Socials, and Email and Phone Number — so the Developer can review them and reach out to the company.

**Why this priority**: It closes the loop for the Developer but depends on requests existing, and its data wiring is deferred to the later backend work.

**Independent Test**: Open the Admin Dashboard, confirm the "Company Requests" category is present, open a request, and confirm its details (name, role, website/socials, email, phone) are shown for contacting the company.

**Acceptance Scenarios**:

1. **Given** the Developer is signed in to AdminDashAccess, **When** the dashboard opens, **Then** a "Company Requests" category is available alongside the existing companies list.
2. **Given** the Company Requests category, **When** it is opened, **Then** the companies that submitted a request are listed.
3. **Given** a listed request, **When** the Developer opens it, **Then** the submitted Company Name, Role, Website/Socials, and Email and Phone Number are shown.
4. **Given** no requests have been submitted, **When** the category is opened, **Then** a clear empty state is shown.

---

### Edge Cases

- The visitor clicks the cross mid-intro (before any question) → the overlay dismisses immediately and no request is recorded.
- The visitor closes the overlay after answering some but not all questions → nothing is recorded and no partial request exists.
- A question is left empty or whitespace → the visitor cannot advance and the missing input is indicated inline.
- A question is answered with a malformed value (e.g., an invalid email, a Website/Socials that is neither a web address nor a handle, or a Phone with no digits) → the visitor cannot advance and the offending field is indicated inline.
- The auto-close timer elapses while the success text is still being written → the overlay still closes, and the cross remains available until it does.
- The visitor's system requests reduced motion → the motion-heavy intro is skipped or parked in a readable state while the questions remain fully completable.
- The company sign-in form is submitted with an unknown company name, a wrong password, or both blank → access is denied with a generic message that identifies neither field.
- The company name is entered with different letter case or surrounding spaces → it still matches the stored record, and sign-in proceeds when the password is correct.
- A signed-out visitor opens the Company Dashboard route directly → the sign-in form is shown, never the dashboard.
- The Employees table has no associated employees → an empty state is shown.
- "Grant Access" is clicked more than once on the same row → the row remains in its granted state without error.
- The "Start 30 days free trial" card is clicked repeatedly → no navigation or state change occurs.
- The Admin "Company Requests" category has no entries (the expected state until request storage exists) → an empty state is shown.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: On the subscription page, "Company Request" MUST launch a full-screen onboarding overlay that covers all other content. This supersedes the inert placeholder behavior defined in the earlier employee-access specification.
- **FR-002**: The overlay MUST open with a full-screen block in the application's cherry theme color sliding in and settling with a smooth motion-blur feel.
- **FR-003**: Once the block has covered the screen, stars MUST streak outward from the center toward the viewer to convey motion into the screen.
- **FR-004**: A company-building illustration MUST be centered and start small, then grow steadily to simulate the camera flying toward the building.
- **FR-005**: After approximately five seconds of approaching the building, the view MUST enter one of the building's windows and the building MUST fade away smoothly.
- **FR-006**: After the intro, the bored-boss character animation MUST appear near the lower-center of the screen (not pinned to the very bottom) and act as the onboarding guide.
- **FR-007**: The overlay MUST present exactly four questions, one at a time and each fading in, in this order: Company Name, Role, Website/Socials, and Email and Phone Number.
- **FR-008**: Each question MUST require a valid answer before the visitor can advance, and MUST indicate the problem inline when the input is missing or malformed. Validation: Company Name and Role must be non-empty; Website/Socials must be a recognizable web address (URL or domain) or a social handle (e.g., starting with "@"); Email must resemble an email address; Phone must be a number of digits with optional separators (+, spaces, dashes, parentheses).
- **FR-009**: While the visitor types, the boss character MUST play its pen-tapping idle motion; when the visitor advances a question, the boss MUST play a brief hands-up pose and then resume the idle motion.
- **FR-010**: After the final answer is submitted, the boss character MUST play a smile.
- **FR-011**: After the final answer, all cinematic and character animation MUST clear and the overlay MUST write, with a text-generation effect, the message: "Request Sent Successfully - Please Wait For The Team To Contact Your Representative".
- **FR-012**: The overlay MUST close by fading out automatically five seconds after the success message begins.
- **FR-013**: The overlay MUST provide a close ("cross") control at the top-right that dismisses it at any time; dismissing before completion MUST abandon the flow and record no request.
- **FR-014**: The cinematic sequence MUST honor the system's reduced-motion preference by not playing the motion-heavy animation, while leaving the questions fully completable.
- **FR-015**: The Company Dashboard MUST live at its own route and MUST require Company Name and Password before any dashboard content is shown.
- **FR-016**: Company sign-in MUST validate the entered Company Name and Password against the company record the Developer created in the Admin Dashboard; this is the only backend-connected behavior in this specification.
- **FR-017**: Invalid company credentials MUST be rejected with a generic message that does not disclose which field was incorrect.
- **FR-018**: A successful company sign-in MUST establish the company session required to view the dashboard, so the dashboard is not reachable without it. The session MUST remain valid for 24 hours from sign-in, surviving browser restarts, and MUST expire after that, requiring the Company Name and Password again.
- **FR-019**: The Company Dashboard MUST present a sidebar containing exactly two sections: "Employees" and "Subscription".
- **FR-020**: The Employees section MUST list the employees associated with the signed-in company in a table, each row offering a "Grant Access" checkmark action.
- **FR-021**: Clicking "Grant Access" MUST visibly change the row's state to indicate access was granted.
- **FR-022**: The Subscription section MUST show a small card reading "Start 30 days free trial"; clicking it MUST perform no action.
- **FR-023**: The existing Admin Dashboard (AdminDashAccess) MUST gain a "Company Requests" category listing the companies that submitted an onboarding request, with a detail view showing each request's Company Name, Role, Website/Socials, and Email and Phone Number so the Developer can contact the company.
- **FR-024**: The Company Requests list, the request detail view, and the company employees table MUST render from placeholder data with clear empty states, because this specification adds no request or employee APIs; real data wiring is deferred to the later backend specification.
- **FR-025**: The cinematic onboarding overlay MUST be dismissible at any time and MUST leave the underlying subscription page in its prior state after closing.
- **FR-026**: The onboarding submission MUST be a visual confirmation only; no submitted request is persisted on the client or on the server in this specification.
- **FR-027**: The Company Name entered at sign-in MUST be matched against the stored company name case-insensitively and after trimming surrounding whitespace.

### Key Entities *(include if feature involves data)*

- **Company Request**: A submission from the cinematic onboarding flow. Attributes: Company Name, Role, Website/Socials, Email, Phone Number, and submission time. In this specification it is not persisted at all — neither on the client nor on the server; the Admin Dashboard's Company Requests view renders from placeholder data until the later backend specification.
- **Company**: (Existing from 008) the Developer-onboarded client organization — name (its identifier), encrypted password, logo, price, and payment status. This specification adds sign-in against this record and does not change it.
- **Company Session**: The authenticated company context established by a successful sign-in; required to view the Company Dashboard and independent of the application's end-user accounts. It remains valid for 24 hours from sign-in, surviving browser restarts, and then expires.
- **Employee**: (Existing from 009) a person who has requested access to a company. This specification surfaces the company's associated employees in the dashboard table, each with a "Grant Access" action; the grant is a visual state only for now.
- **Company Dashboard Sidebar Item**: One of exactly two navigation entries in the company dashboard — "Employees" and "Subscription".

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A visitor can launch the onboarding overlay, complete all four questions, and see the success message in under two minutes.
- **SC-002**: The full cinematic intro (block → stars → building growth → window entry) plays continuously without visible stutter on a modern desktop browser.
- **SC-003**: 100% of flows abandoned via the cross, or left incomplete, result in 0 recorded requests.
- **SC-004**: 100% of sign-in attempts with a wrong company name or password are denied with a message that reveals neither field, and expose 0 company data.
- **SC-005**: A company representative with valid credentials reaches the Company Dashboard in under one minute.
- **SC-006**: The Company Dashboard sidebar consistently shows exactly the two sections "Employees" and "Subscription" in 100% of loads.
- **SC-007**: 100% of employee rows in the Employees table expose a "Grant Access" action, and its state changes on click in 100% of clicks.
- **SC-008**: 100% of clicks on the "Start 30 days free trial" card produce no navigation or state change.
- **SC-009**: With reduced motion enabled, 0 motion-heavy animations play during onboarding while 100% of the questions remain completable.
- **SC-010**: The "Company Requests" category and its detail view are reachable from the Admin Dashboard in 100% of visits, showing an empty state when no requests exist.
- **SC-011**: 100% of answers that are empty or fail their question's format check block advancing, and 100% of well-formed answers allow it.

## Assumptions

- This specification supersedes the inert "Company Request" placeholder from the employee-access specification; that button now launches the onboarding overlay.
- Only the company sign-in is backed by the API, validating against the company table created in the Admin Dashboard specification. No other backend endpoints are added; the request submission is a visual confirmation with no storage, and the Company Requests view, the employees table, and the subscription card render from placeholder data with empty states.
- "Email and Phone Number" is captured as a single contact step holding both email and phone, keeping the flow at exactly four questions.
- The bored-boss animation is the reference character supplied by the Developer; it is transplanted into the application and the standalone reference file is removed after porting.
- The cinematic sequence targets modern desktop browsers; the reduced-motion preference is honored by parking the motion-heavy parts.
- The "Company Requests" category is added to the existing hidden Admin Dashboard as UI structure; wiring it to real submissions arrives with the later backend specification.
- Employees shown in the Company Dashboard are those associated with the company through the employee request record set introduced earlier; "Grant Access" toggles a visual state for now, with persistence deferred.
- A company session is scoped to the Company Dashboard, is independent of the application's end-user (Google) accounts and of the admin session, and lasts 24 hours from sign-in before requiring the credentials again.
- Price, billing, and payment processing are out of scope; the subscription card is deliberately inert.
- No automated tests are included, per the Developer's standing instruction; verification is a manual pass.
