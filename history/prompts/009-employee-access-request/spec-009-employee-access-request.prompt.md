---
id: spec-009-employee-access-request
title: employee-access-request-spec
stage: spec
date: 2026-09-30
surface: cli
model: claude-sonnet-4-5
feature: 009-employee-access-request
branch: 009-employee-access-request
user: developer
command: /sp.specify
labels: [spec, subscription, employees, access-request, adam-id, trial-payment]
links:
  spec: specs/009-employee-access-request/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/009-employee-access-request/spec.md
  - specs/009-employee-access-request/checklists/requirements.md
  - history/prompts/009-employee-access-request/spec-009-employee-access-request.prompt.md
tests:
  - null
---

## Prompt

/sp.specify this is the 2nd part of implementation of the trial and payment system, in the spec before this we implemented the admin panel, using username and pass the developer (me Arham, salam) can add different companies, enlist or edit them etc

Pre-Requisite:
008-admin-dashboard specfication and all its research will be a great pre-requisite for smoother more context aware flow

Current Idea:

We have established the admin dashboard where i can add different companies, assign to them statuses, and prices, and also remove or edit their information, giving them company pass and username access.
This specification is dealing with the Employee part, this employee part happens to be between Developer part (done already) and Company Dash Part (To be implemented in a later spec)
The idea is the user when they arrive first see the signin, they signin, and then instead of showing them the application, we add another layer "the subscription layer", infront of them is a company modal that states "Employee Request" and "Company Request".
This part deals with "Employee Request", the employee clicks this buttons adds necessary information like the company from which they are, their name id etc, and then asking for request access, the request access will be handled by company (again in a later specification this is dealing with employee part only)
So main role of this is, employee
signs in
requests access
fills information
waits...
when access granted, application appears to them they start using

Implementation:

The implementation will be quite straightforward with the [frontend] that includes:
1. The existing Signin, this is crucial once the user signs in then they can continue, also change this sigin to another route instead of component, and remove the popup of site leave confirmation dialog box that appears on click of sign in with google
2. The user is then sent to another page "subscription", they see A page that is:
  - Contains title "Reconciliation AI for Companies"
  - contains 2 buttons "Company Request" & "Employee Request"
  - Clicking the Company request does nothing (For Future)
3. Clicking the Employee Request button opens a shadcn UI Popup Modal that requires following entries
  - Employee Name: Required the employee name
  - ID: To be input by user, can also be given option to generate randomly on spot, should be kept simple, Required
  - Company to Request: This will be required and it will be a dropdown list, it will list all the companies that are added by me (Developer) from /AdminDashAccess, the company table in cockroach db, this list will be derived from that table, and also if the logo is available the logo is also present on its left side and if not a placeholder
4. User clicks "Request" and is given the message "Your request has been sent to the designated company successfully, you may contact them to grant you access by providing them your ID or Name"
5. On side of this company card also add "Individuals Plans"
  - It contains 2 clickable but do nothing buttons
  - Rs 300 - 1 day
  - Rs 1500 - 1 month

[Backend] implementation:
1. The ID will be used as indexed
2. ID should be kept unique but simple and should start with adam- (applied automatically)
3. Important - A Separate table "Employees" where all such employees who have placed request (Accepted or Accepted by Company) will be placed

Keep everything concise, simple, dont add any complication or extreme edge cases, and dont do tests, cling to spec well

## Response snapshot

Created the feature specification at specs/009-employee-access-request/spec.md on new branch 009-employee-access-request (number 9 chosen as the highest existing spec/branch was 008; short name "employee-access-request"). Grounded it in the 008-admin-dashboard spec and research (companies table, AdminDashAccess, deferred company-facing dashboard). The spec covers: 3 prioritized user stories (sign in on its own route and land on the Subscription page P1, submit an employee access request via popup P1, see the inert Company Request action and Individual Plans panel P2), 6 edge cases, 18 functional requirements (dedicated sign-in route; no "Leave site?" prompt on Google sign-in; post-sign-in landing on the Subscription page titled "Reconciliation AI for Companies" with Company Request and Employee Request; Employee Request popup capturing Name, ID, and Company to Request; dropdown sourced from the Developer's companies with logo or placeholder; generated-or-typed ID always automatically prefixed `adam-` and unique; the exact confirmation message; dedicated Employees record set separate from companies and users, surviving restarts, with name/ID/company/requesting-account/status/created-at and a pending default; unique indexed ID; Individual Plans "Rs 300 - 1 day" and "Rs 1500 - 1 month" as inert placeholders), 2 key entities, 7 assumptions, and 8 measurable success criteria. Generated the quality checklist at checklists/requirements.md — all items pass, no [NEEDS CLARIFICATION] markers (open points resolved as documented assumptions: employee identity is the existing Google sign-in recorded on the request; ID shape is `adam-` + short simple value with the prefix system-applied; requests start pending; application gating and company-side acceptance deferred to a later specification).

## Outcome

- ✅ Impact: Employee-facing specification (spec 2 of the trial/payment series) delivered; branch 009-employee-access-request created; quality checklist passed; ready for /sp.clarify or /sp.plan.
- 🧪 Tests: None run (specification stage only, per the user's explicit "dont do tests").
- 📁 Files: specs/009-employee-access-request/spec.md, specs/009-employee-access-request/checklists/requirements.md
- 🔁 Next prompts: /sp.clarify or /sp.plan for 009-employee-access-request
- 🧠 Reflection: The Developer asked for brevity and minimal edge-case handling, so the spec resolves ambiguity through documented assumptions instead of clarification markers. It leans on 008's established facts (the `companies` table is the dropdown source; the company-facing dashboard is deferred) and keeps everything else as visible-but-inert placeholders. No test tasks are included, consistent with the standing instruction and 008's precedent.

## Evaluation notes (flywheel)

- Failure modes observed: create-new-feature.ps1 is not Windows PowerShell 5.1 safe — `Join-Path $repoRoot 'history' 'prompts' $branchName` (4 positional args) throws, so the script aborts after creating the branch, the spec directory, and the template copy, but before creating history/prompts/<branch> or printing JSON. The branch and spec.md were created correctly; the prompts directory was created manually. (Same failure noted in the 008 PHR.)
- Graders run and results (PASS/FAIL): Spec quality validation PASS (no placeholders, no NEEDS CLARIFICATION, mandatory sections complete, success criteria measurable and technology-agnostic).
- Prompt variant (if applicable): spec-v1
- Next experiment (smallest change to try): Fix create-new-feature.ps1's multi-arg Join-Path call so the script completes cleanly on Windows PowerShell 5.1.
