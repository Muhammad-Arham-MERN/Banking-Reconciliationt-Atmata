---
id: spec-011-company-employee-wiring
title: company-employee-wiring-spec
stage: spec
date: 2026-10-02
surface: cli
model: claude-sonnet-4-5
feature: 011-company-employee-wiring
branch: 011-company-employee-wiring
user: developer
command: /sp.specify
labels: [spec, company-dashboard, employee-access, admin-dashboard, sign-convention, authorization, resend, edge-cases]
links:
  spec: specs/011-company-employee-wiring/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/011-company-employee-wiring/spec.md
  - specs/011-company-employee-wiring/checklists/requirements.md
  - history/prompts/011-company-employee-wiring/spec-011-company-employee-wiring.prompt.md
tests:
  - null
---

## Prompt

/sp.specify

This specification deals with the finalized implementation of company-employee dashboard system, the vendor and bank Credit-Debit Signs convention finalized and Edge Cases to be Covered + Some animation improvement

[Company-Employee Dashboard Wiring]

Currently our entire frontend is established we just need a backend wiring for the finalized implementation, here is how:
1. When employee makes a request that is associated with a company, that employee is added to the Company Table of that specific company, so employ xyz requests Greaves Pakistan, Greaves pakistan gets an employee request in Company Dashboard
2. In Company Dashboard a search bar is present, allowing companies to search particular names or ids, the search should be name based + id based automatically, so user does not have to select what they are searching, the input is evaluated against id and then name automatically
3. When in "Company Request" a request is sent successfully, that company with its given details is provided in my Admin Dashboard under Companies Requess
4. All dummy data should be removed
5. Resend should be established to send a simple email of a new company request at "ArhamBrowser@gmail.com"
6. Employee Requests can be deleted
7. Granting Access to employees enables the access of application for that particular user & employee, beforehand, the user must not be able to by-pass without access towards /upload-ai. in order to access /upload-ai they must be assigned a granted request by a company, and leave individual plan coming soon as is

[Signs Finalized throughtout App]

1. Bank
  - Unpresented Checks - Credited in cashbook is (-negative)
  - Uncleared Checks - Debited in Cashbook is (+positive)
  - Bank Debited but not credited in cashbook - is (+positive)
  - Bank Credited but not debited in cashbook - is (-negative)
2. Vendor
  - Unpresented Checks - Credited in cashbook is (-negative)
  - Uncleared Checks - Debited in Cashbook is (+positive)
  - Vendor Debits - is (-negative)
  - Vendor Credit - is (+positive)

Make sure the above mentioned sign convention is followed through out the entire app

[Edge Cases]

1. After granting user access in their dashboard in the navigation bar, they should be allowed to leave that company, and asking confirmation, which will also automatically make them lose access of application back to subscriptions or signin page
2. An employee once accessed the application can not view subscription page again without leaving company
3. A user that has requested for produce access with a company can't make a new request by clicking "Employee Request" asking them to cancel their older request, cancellation leads to deletion of employee request from company records
4. In Admin Dashboard, a company whose account has been created, also shows no. employees in the table, showing a number, hovering over them opens a Modal showing all the employees associated with the company using the application
5. App is not usable unless an employee with access granted
6. User's Data at signin and Employee Information should must be linked and reference eachother, for future features development
7. User who has a company dashboard access can see list of all their employees, this manager can also request as an employee to this company that they are managing and grant themselves access in the Company Dashboard, moreover in the company dashboard they can assign any account as "Manager" this will enable in the navigation bar of application as "Company Dashboard", allowing this manager to access the dashboard without requiring to manually remember url and also keeping company dashboard url hidden from other people

## Response snapshot

Created the feature specification at specs/011-company-employee-wiring/spec.md on new branch 011-company-employee-wiring (number 11 chosen as the highest existing spec/branch was 010; short name "company-employee-wiring"). The spec captures 7 prioritized user stories: P1 company sees/searches/grants/deletes employee requests; P1 granted access gates the app and can be left; P2 company onboarding requests reach the Admin Dashboard + ArhamBrowser@gmail.com notification; P3 admin per-company employee count + hover modal; P3 Manager role and hidden Company Dashboard navigation entry; P2 the finalized sign convention everywhere; P3 app-wide animation polish. It contains 22 functional requirements across the three areas, 16 edge cases, 7 key entities, 12 measurable success criteria, and 11 assumptions.

Before writing, the current implementation was mapped (backend company/employee/admin modules; frontend Company Dashboard, Admin Dashboard, subscription gating, sign rendering) to ground the spec. Two notable findings: (a) no accept/deny ("grant access"), employee delete, company-facing employee endpoints, or email/Resend integration exist yet — the employee status is write-only-pending and the dashboard renders placeholder data from company-placeholder.ts; (b) the current sign presentation is the opposite of the finalized convention for the Bank-side categories (Bank Credited-not-Debited is shown positive, Bank Debited-not-Credited negative) and for Vendor (debit positive, credit negative), so this is a cross-cutting flip, not just a UI tweak.

Three scoping questions were asked and resolved, then folded into the spec's Clarifications section and the FRs: (Q1) the finalized sign convention is canonical end-to-end — presentation, backend reconciliation logic, and stored database values (FR-014 updated; SC-007 updated); (Q2) the application gate hides everything except the subscription page and the sign-in page (FR-009 updated; SC-003 updated); (Q3) the animation work is an app-wide polish pass over existing transitions honoring reduced motion (FR-022 and User Story 7 updated; SC-012 added). Quality checklist at checklists/requirements.md now passes all items with no [NEEDS CLARIFICATION] markers remaining.

## Outcome

- ✅ Impact: Final wiring specification for the company-employee system delivered; branch 011-company-employee-wiring created; spec + quality checklist written; all three scoping clarifications resolved; ready for /sp.plan.
- 🧪 Tests: None run (specification stage only, per the Developer's explicit "no tests").
- 📁 Files: specs/011-company-employee-wiring/spec.md, specs/011-company-employee-wiring/checklists/requirements.md
- 🔁 Next prompts: /sp.clarify (optional) or /sp.plan for 011-company-employee-wiring
- 🧠 Reflection: The brief mixed concrete, prescriptive sign rules with unspecified scope ("throughout the entire app", "some animation improvement"); grounding the spec in the actual current code revealed the Bank/Vendor sign flip is a genuine behavior change, which made the scope questions worth asking rather than guessing. The answers pushed the sign convention all the way through the stack (DB included) and made the access gate total, which materially sharpens the plan. Faithfully enumerating both sign tables verbatim in FR-012/FR-013 (and in User Story 6) reduces the chance of an implementation re-deriving them incorrectly.

## Evaluation notes (flywheel)

- Failure modes observed: create-new-feature.ps1 is not Windows PowerShell 5.1 safe — `Join-Path $repoRoot 'history' 'prompts' $branchName` (4 positional args) throws "A positional parameter cannot be found that accepts argument 'prompts'", so the script aborts after creating the branch, specs/<branch>, and the template copy, but before creating history/prompts/<branch> or printing JSON. The branch and spec.md were created correctly; the prompts directory was created by the WriteFile call. (Same failure noted in the 008, 009, and 010 PHRs; pwsh is not installed.)
- Graders run and results (PASS/FAIL): Spec quality validation PASS — content quality, testability, measurability, edge cases, scope, and assumptions all pass; all three [NEEDS CLARIFICATION] markers resolved, none remain.
- Prompt variant (if applicable): spec-v1
- Next experiment (smallest change to try): Fix create-new-feature.ps1's multi-arg Join-Path call (nested Join-Path or [System.IO.Path]::Combine) so the script completes cleanly on Windows PowerShell 5.1.
