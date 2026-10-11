---
id: spec-010-company-dashboard-onboarding
title: company-dashboard-onboarding-spec
stage: spec
date: 2026-10-01
surface: cli
model: claude-sonnet-4-5
feature: 010-company-dashboard-onboarding
branch: 010-company-dashboard-onboarding
user: developer
command: /sp.specify
labels: [spec, company-dashboard, onboarding, company-request, cinematic, subscription, employees]
links:
  spec: specs/010-company-dashboard-onboarding/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/010-company-dashboard-onboarding/spec.md
  - specs/010-company-dashboard-onboarding/checklists/requirements.md
  - history/prompts/010-company-dashboard-onboarding/spec-010-company-dashboard-onboarding.prompt.md
tests:
  - null
---

## Prompt

/sp.specify This specification is the implementation of the final block of our employee/compnay dashboard System
from specs 008 and 009, you can see we have implemented Admin Dashboard and Employee Requests system
This specification is dealing with the last part of the puzzle which is Company Dashboard.

Idea:

So idea is that a company arrives at my application, signs in, sees 2 options, and clicks "Company Request", they then get a popup to tell important details about company, like phone number for contact, email etc, brand details etc, and send request.
I receive their request, in my Admin Dashboard, where i can see different companies list, it adds a new category of "Company Requests". I can view their details and contact them.
We communicate and finally i create their account in my app with their user, pass, and price etc, and give them credentials
They can use to signin a new dashboard that will be provided to companies (This specification deals with this dashboard), they can signin, and in that page, they have a dashboard, with sidebar that contais 2 sections "Employee Requests" and "Subscription"
They can view all their employees who are currently enrolled, and when more employees ask for request they can garnt them access from here. Moreover they can start payments in the subscription section.

So this is more like an onboarding specification for company

[Implementation]

Fronted will be following:
1. The company clicks Company Request and we do some funky stuff
  - A sliding block of our cherry theme color, slides into the screen, and covers everything, the animation is smooth and motion blured when the block occupies
  - Then what I want is something cool, here is how it works, once the block captures the screen, motion blurs stars coming from the central point towards the screen, which indicates motion into the screen
  - In the center will be a company building svg, it will be in center small, and gradually its size will increase and increase, it will be like a motion of screen moving constantly into the screen towards the building and building is getting larger as distance increases
  - after 5 seconds of reaching building, the screen then enters into one of the windows of building and the building element disappears in a smooth manner, indicating as if we were travelling speedily towards a building and then entered its window
  - Then this animation [boss-loader in frontend (This animation should be used directly within nextjs, after writing this in nextjs, remove this file, and there are a few actions that this character does, it is ticking his pen on table, he keeps ticking this during the time the user is adding information that is asked to them, and when they click next his hands up animation plays and same ticking, and when all information is given, the final smile animation is shown)] appears on the buttom center, but not too bottom below, as if this man boss is guiding them bored to their onboard
2. The Company is shown following questions, each question will be shown and question fades in, the user answers and submits and then next question appears like an onboard on steroids
  - Company Name: User enters company name
  - Role: The role of company, what it serves
  - Website/Socials: Company socials
  - Email and Phone Number: The contact information
3. After submitting all animations disappear and the block writes [https://ui.aceternity.com/components/text-generate-effect] "Request Sent Successfully - Please Wait For The Team To Contact Your Representative"
4. At end the block closes that is fades out automatically after 5 seconds and also there is a "cross" on top right to skip if user accidently pressed the button for company request

5. Once this is done, a route will be created for CompanyDashboard, and it will be started with a signin, the signin will require company name and password, both will be linked and checked via the password and company name stored in the company table and same for password (Connect with backend only for this feature)
6. The dashboard will list employees that have associated themselves with the company, and the Payment will contact a small card with text that says start 30 days free trial, but it does nothing right now
6. we will create following dashboard https://ui.aceternity.com/components/sidebar
7. We will have 2 tabs on the side Employees and Payments
8. The employee will also use Shadcn Table with a check mark along each employee saying Grant Access

We will not implement any Backend in this, i think the spcification is already quite dense on the fronted part, we will implement backend after this, we just want a nice structure and will add functionality in next specification, keep things simple, dont overcomplicate, stick to the specs, and no tests

## Response snapshot

Created the feature specification at specs/010-company-dashboard-onboarding/spec.md on new branch 010-company-dashboard-onboarding (number 10 chosen as the highest existing spec/branch was 009; short name "company-dashboard-onboarding"). Resolved two scope questions with the Developer before writing (recorded in the Clarifications section): (1) the apparent "connect with backend only for this feature" vs "no backend" contradiction resolves to implementing the company sign-in API only, validated against the company record from 008, with everything else frontend structure and placeholder data; (2) the Admin Dashboard "Company Requests" category IS in scope as UI structure. The spec contains 4 prioritized user stories (cinematic Company Request onboarding overlay P1; company sign-in to the Company Dashboard P1; dashboard sidebar with Employees + Subscription P2; Admin Dashboard "Company Requests" category P3), 12 edge cases, 25 functional requirements (full-screen cherry block + motion blur, center-origin star streaks, growing building SVG, window entry after ~5s, lower-center bored-boss guide, four fade-in questions Company Name / Role / Website-Socials / Email and Phone, pen-tapping idle, hands-up on advance, smile at the end, text-generate success message, 5s auto-fade, skip cross, reduced-motion handling, company sign-in against the 008 company table as the only backend call, two-section sidebar, employees table with Grant Access, inert "Start 30 days free trial" card, admin Company Requests category with detail view, placeholder data with empty states), 5 key entities, 10 measurable success criteria, and 11 assumptions. Generated the quality checklist at checklists/requirements.md — all items pass, no [NEEDS CLARIFICATION] markers remain.

## Outcome

- ✅ Impact: Final company-facing specification (spec 3 of the admin/employee/company series) delivered; branch 010-company-dashboard-onboarding created; quality checklist passed; ready for /sp.clarify or /sp.plan.
- 🧪 Tests: None run (specification stage only, per the Developer's explicit "no tests").
- 📁 Files: specs/010-company-dashboard-onboarding/spec.md, specs/010-company-dashboard-onboarding/checklists/requirements.md
- 🔁 Next prompts: /sp.clarify or /sp.plan for 010-company-dashboard-onboarding
- 🧠 Reflection: The description mixed a rich cinematic frontend flow with a contradictory backend statement; asking two targeted questions up front (rather than guessing or emitting any [NEEDS CLARIFICATION] markers) kept the spec unambiguous and matched the constitution's ambiguity-resolution principle. The spec supersedes 009's inert "Company Request" button and leans on 008's companies table as the sole backend touchpoint, while everything else is deliberately placeholder UI with empty states.

## Evaluation notes (flywheel)

- Failure modes observed: create-new-feature.ps1 is not Windows PowerShell 5.1 safe — `Join-Path $repoRoot 'history' 'prompts' $branchName` (4 positional args) throws "A positional parameter cannot be found that accepts argument 'prompts'", so the script aborts after creating the branch, the specs directory, and the template copy, but before creating history/prompts/<branch> or printing JSON. The branch and spec.md were created correctly; the prompts directory was created manually by the WriteFile call. (Same failure noted in the 008 and 009 PHRs; pwsh is not installed on this machine.)
- Graders run and results (PASS/FAIL): Spec quality validation PASS (no placeholders, no NEEDS CLARIFICATION, mandatory sections complete, success criteria measurable and technology-agnostic).
- Prompt variant (if applicable): spec-v1
- Next experiment (smallest change to try): Fix create-new-feature.ps1's multi-arg Join-Path call (use nested Join-Path or [System.IO.Path]::Combine) so the script completes cleanly on Windows PowerShell 5.1.
