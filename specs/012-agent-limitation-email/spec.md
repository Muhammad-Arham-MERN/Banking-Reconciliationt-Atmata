# Feature Specification: Agent Tool-Limitation Email Reporting & Blue Technical-Failure Notice

**Feature Branch**: `012-agent-limitation-email`  
**Created**: 2026-11-07  
**Status**: Draft  
**Input**: User description: "We need to provide our agent with a tool to send emails. Our current extraction agent, when it extracts, uses its extraction tool; sometimes there are problems or limitations with the extraction tool such that the agent cannot successfully perform extraction and the tools need upgrades. As I push the app to production, I want to give my agent an email tool so that whenever it encounters a problem caused by a limitation of its reconciliation/extraction tools, it sends me an email with the issue, what kind of upgrade of the tool (or a new tool) it needs for better functioning. How: (1) make a Resend API email tool for the agent; (2) I have a Gmail label, so the email must start with 'Reconciliation Atmata' and go to arhambrowser@gmail.com; (3) guide the agent to use the tool whenever it knows the reconciliation failure is due to a tool/engine limitation, when there is an error with the tool, or when it needs a new tool and must tell why with a valid reason — it must always email when a failure is due to a technical limitation/problem of the tool, not just any failure; (4) the error must be provided in the email with details + example + analogy of the issue and a proposed solution; (5) when such a failure happens and the agent sends the email, the user's loading screen also shows this update — after failure the error message must clearly be indicated in Blue that there is a technical limitation from our side, the agent has sent it to the developer for improvement and to please wait in the meantime; (6) give the agent a very short and precise high-level summary of what its tools are made of (not the logic, just a very high-level overview) so its proposed solutions are relevant to context."

**Testing Policy**: **No tests are to be written for this feature.** No test files, test suites, test cases, or test tasks MUST be added on either the backend or the frontend — this follows the project's standing instruction. Verification is entirely the manual pass documented in [quickstart.md](./quickstart.md).

## Clarifications

### Session 2026-11-07

- Q: Which failure paths may trigger the limitation email and the blue user notice? → A: The AI extraction agent's own tools/engine only. The agent itself determines that a failure is a tool/engine limitation — the Developer has seen the agent correctly identify the exact issue — and it is the agent that composes and sends the report. The deterministic, agentless reconciliation path is out of scope.
- Q: How much of the user's financial file content may the limitation email include? → A: Technical detail plus an anonymised/structural example (column names, layout/shape, and the nature of the failure) — never raw sample rows, account numbers, balances, or unredacted user data.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The agent reports a tool limitation to the Developer by email (Priority: P1)

While the extraction agent is working, it hits a situation it recognises as a limitation or defect of its own tools or engine — it cannot extract a file even though it has followed its tools correctly, an existing tool errors out, or it concludes that no current tool can do the job. Instead of only failing, the agent uses its email tool to send the Developer one well-formed message describing the problem, what it tried, an example, an analogy that makes the problem easy to grasp, and the tool upgrade (or new tool) it believes is needed, with the reason. The message is delivered to the Developer's inbox with a subject that begins with "Reconciliation Atmata", so the Developer's mail rules file it under the "Reconciliation Atmata" label.

**Why this priority**: This is the whole point of the feature — it closes the feedback loop between production failures and the Developer's ability to improve the tools. Without it, every tool limitation is discovered only by chance.

**Independent Test**: Trigger a reconciliation whose extraction fails because of a genuine tool/engine limitation, then confirm the Developer's inbox (or provider send log) received exactly one email to `arhambrowser@gmail.com` whose subject begins with "Reconciliation Atmata" and whose body contains the issue, the details, an example, an analogy, and a proposed solution/upgrade.

**Acceptance Scenarios**:

1. **Given** an extraction run that fails because of a genuine tool/engine limitation, **When** the agent decides it cannot proceed for this reason, **Then** it sends exactly one email to the Developer's address.
2. **Given** the limitation email is sent, **When** the Developer views it, **Then** its subject begins with "Reconciliation Atmata" so it lands in the "Reconciliation Atmata" label.
3. **Given** the limitation email is sent, **When** the Developer reads the body, **Then** it contains a description of the issue, the supporting details, a concrete example of the problem, an analogy that explains it, and a proposed solution or tool upgrade/new tool with the reason it is needed.
4. **Given** an extraction run that fails for a reason that is NOT a tool/engine limitation (e.g. malformed or unsupported input, or an ordinary data mismatch), **When** the run fails, **Then** no limitation email is sent.

---

### User Story 2 - The user is shown a blue "technical limitation" notice (Priority: P1)

When a reconciliation fails because of a tool/engine limitation and the agent has reported it, the end user is told the truth plainly and calmly. During processing the loading experience surfaces an update that a limitation occurred on our side and that the issue has been sent to the developer for improvement. After the run fails, the error the user sees is clearly rendered in **blue** and states that there is a technical limitation from our side, that the agent has sent the limitation to the developer for improvement, and that the user should please wait in the meantime. Ordinary failures keep their existing (non-blue) treatment, so blue always means "this one is on us".

**Why this priority**: It is the user-facing half of the feature, and it turns an opaque failure into an honest, trust-preserving message. It depends on the same limitation classification as Story 1, so it is P1 alongside it.

**Independent Test**: Cause a tool-limitation failure, watch the loading screen through to failure, and confirm (a) an in-progress update announced the limitation, and (b) the final error message is rendered in blue with the technical-limitation wording. Then cause an ordinary failure and confirm no blue notice appears.

**Acceptance Scenarios**:

1. **Given** a reconciliation is running and a tool/engine limitation is hit, **When** the agent reports it, **Then** the loading screen shows an update stating a technical limitation occurred on our side and the issue has been sent to the developer.
2. **Given** the run has failed because of a tool/engine limitation, **When** the failure is displayed to the user, **Then** the error message is clearly indicated in blue and states that there is a technical limitation from our side, that the agent has sent the limitation to the developer for improvement, and to please wait in the meantime.
3. **Given** a reconciliation fails for a reason that is NOT a tool/engine limitation, **When** the failure is displayed, **Then** no blue technical-limitation notice is shown and the existing failure treatment is used.
4. **Given** the blue technical-limitation notice, **When** it is read by the user, **Then** it contains no internal jargon, stack traces, or implementation detail — only the plain statement that the problem is ours and has been reported.

---

### User Story 3 - The agent reports only genuine limitations, guided by a concise tool summary (Priority: P2)

To keep the Developer's inbox meaningful, the agent only emails when a failure is genuinely attributable to its tools or engine (or when it is confident a new tool is required), never for ordinary failures. To make its proposed solutions actionable and contextually correct, the agent is given a very short, high-level summary of what each of its tools is *for* — purpose only, never the internal logic — so an upgrade it proposes is grounded in what the tools actually do.

**Why this priority**: Without this restraint the feature becomes noise, and without the tool summary the proposed solutions are generic. It refines the P1 behavior rather than enabling a new capability, so it ranks below the P1 stories.

**Independent Test**: Run a set of failures — some genuine tool limitations, some ordinary — and confirm an email is sent only for the genuine ones; then read a produced email and confirm its proposed solution names the specific tool(s) involved and reflects their actual purpose.

**Acceptance Scenarios**:

1. **Given** the agent's instructions and toolset, **When** the agent runs, **Then** it has access to a concise, high-level description of the purpose of each of its tools.
2. **Given** the agent is deciding whether to report, **When** a failure is not attributable to a tool/engine limitation, **Then** it does not send an email.
3. **Given** the agent does report a limitation, **When** its proposed solution is read, **Then** the proposal references the specific tool(s) involved and is consistent with what those tools are documented to do.
4. **Given** a single failing run in which the agent recognises more than one limitation, **When** it reports, **Then** at most one email is sent for that run.

---

### Edge Cases

- **Email delivery fails (provider/network/spam-filter error)** → the reconciliation outcome is unchanged: the run still fails as it would have, the blue technical-limitation notice is still shown to the user, and the failure is logged; the feature never converts a successful reconciliation into a failure or vice-versa.
- **A tool/engine limitation is hit but the agent is unable to compose or send the email** → the run still surfaces the failure and the blue notice; the report is treated as best-effort.
- **The agent misjudges an ordinary failure as a technical limitation** → guarded by the requirement that the agent may report only with a valid, stated reason tied to its tools; the proposed solution must name the tool involved.
- **Multiple distinct limitations occur in one run** → the user still gets one blue notice and the Developer gets at most one email for that run.
- **A limitation occurs during a run the user cancels** → cancellation behaviour is unchanged; if no limitation was actually reported, no email and no blue notice result.
- **Sensitive content in the failing file** → the email must not expose secrets (credentials, API keys, tokens); see the data-handling requirement for how much file detail may be included.
- **The recipient address or sender is not configured** → the send is skipped safely and logged, and the user-facing failure behaviour is unaffected.

## Requirements *(mandatory)*

### Functional Requirements

**The developer notification tool**

- **FR-001**: The extraction agent MUST have access to a tool that sends the Developer an email at `arhambrowser@gmail.com`.
- **FR-002**: The subject line of every limitation email MUST begin with exactly `Reconciliation Atmata`, so the Developer's mail rules route it to the "Reconciliation Atmata" label.
- **FR-003**: The body of every limitation email MUST contain all of: (a) a clear description of the problem/limitation, (b) the supporting details (what was attempted, where it failed, and the observed error), (c) a concrete example of the problem, (d) an analogy that explains the issue in plain terms, and (e) a proposed solution — the tool upgrade or new tool the agent believes is needed — stated together with the reason it is needed.
- **FR-004**: The email MUST identify the context of the failure well enough for the Developer to act: at minimum the tool(s) involved, the affected file type/stage of extraction, and a way to correlate the report with the failing run (e.g. a run identifier).
- **FR-005**: Email sending MUST be best-effort: a delivery failure MUST NOT change the reconciliation outcome, MUST NOT crash or abort the agent run, and MUST NOT block the response to the user. When the send is skipped or fails, it MUST be recorded in the system's logs.
- **FR-006**: The agent MUST send at most one limitation email per failing reconciliation run. Reporting a limitation MUST also **stop the run immediately**: once the agent calls the reporting tool, the pipeline MUST NOT make further detection attempts and MUST NOT re-run the agent through the output guardrail loop — the failure is final and is surfaced at once.

**When the agent may — and must — report**

- **FR-007**: The agent MUST send a limitation email whenever a reconciliation/extraction failure is caused by a technical limitation or defect of its own tools or engine, or when it determines that a new tool is required — and in the latter case it MUST state the reason.
- **FR-008**: The agent MUST NOT send a limitation email for failures that are not attributable to a tool/engine limitation (for example, malformed or unsupported input files, ordinary data mismatches, or user error). Reporting MUST be limited to genuine tool/engine limitations.
- **FR-009**: The agent MUST be provided, as part of its working context, a very short and precise high-level summary of the purpose of each of its tools — what each tool is *for*, not its internal logic — so that the proposed solutions it writes are relevant to the tools that actually exist.
- **FR-010**: The reporting behaviour MUST apply only to reconciliation failures attributable to the AI extraction agent's own tools or engine. The agent itself MUST determine that a failure is a tool/engine limitation, and the agent MUST be the component that composes and sends the report. Failures of the deterministic, agentless reconciliation path are out of scope for this feature.

**The user-facing technical-limitation notice**

- **FR-011**: While a reconciliation is running, when a tool/engine limitation is hit and reported, the user's loading experience MUST surface an update stating that a technical limitation occurred on our side and that the issue has been sent to the developer for improvement.
- **FR-012**: After a reconciliation fails because of a tool/engine limitation, the user-facing error message MUST be rendered clearly in **blue** and MUST state that there is a technical limitation from our side, that the agent has sent the limitation to the developer for improvement, and that the user should please wait in the meantime.
- **FR-013**: Only tool/engine-limitation failures MUST receive the blue technical-limitation treatment; failures that are not of this kind MUST retain the existing (non-blue) failure treatment, so the blue colour always distinguishes our-side technical limitations.
- **FR-014**: The blue technical-limitation notice MUST be written for a non-technical user — no internal jargon, stack traces, or implementation detail — and MUST NOT prevent the user from retrying or navigating away.

**Data handling**

- **FR-015**: The limitation email MUST NOT include secrets — credentials, API keys, tokens, or connection strings — under any circumstance.
- **FR-016**: The email MAY include technical detail and an anonymised/structural example of the failing file — column names, layout/shape, and the nature of the failure — but MUST NOT include raw sample rows, account numbers, balances, or other unredacted user financial data.

### Key Entities *(include if feature involves data)*

- **Tool Limitation Report**: The structured content the agent assembles for the Developer — the issue description, the supporting details, an example, an analogy, the proposed solution/upgrade, the reason it is needed, and the failure context (tool(s), file type/stage, run identifier). It is the payload of the notification email.
- **Limitation Notification Email**: The delivered message — a subject beginning with "Reconciliation Atmata", the Developer as recipient (`arhambrowser@gmail.com`), and the Tool Limitation Report as its body. Delivery is best-effort and its outcome is logged; it is not otherwise persisted by this feature.
- **Technical-Limitation Failure Signal**: The classification that the agent attaches to a failure when it reports a tool/engine limitation. It flows from the agent run to the user-facing surfaces so the loading update and the blue error message can be shown, and it is what distinguishes a limitation failure from an ordinary one.
- **Tool Purpose Summary**: A concise, high-level description of the purpose of each of the agent's tools, supplied to the agent so its proposed solutions stay contextually relevant. It describes what each tool is for, not how it works.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of reconciliation failures attributable to a genuine tool/engine limitation produce exactly one developer email with a subject beginning with "Reconciliation Atmata", and 0 emails are produced for failures that are not tool/engine limitations.
- **SC-002**: 100% of produced limitation emails contain all five required elements (issue, details, example, analogy, and proposed solution with reason), verified by the Developer reading the inbox.
- **SC-003**: 100% of tool/engine-limitation failures display the blue technical-limitation message to the user, and 0 ordinary failures display it.
- **SC-004**: 0 reconciliation runs change their outcome (fail, abort, or block) because of an email delivery problem, and 0 runs lose the blue notice because the email could not be sent.
- **SC-005**: 100% of proposed solutions in limitation emails name the specific tool(s) involved, and 0 emails include secrets (credentials, API keys, tokens).
- **SC-006**: The Developer can understand a reported limitation, its cause, and the suggested fix from the email alone, without needing the original files, in the large majority of reports (target: ≥ 90% of reports require no follow-up question).

## Assumptions

- The feature targets the AI extraction/agent flow only: the agent itself determines that a failure is a tool/engine limitation and is the component that composes and sends the report. The deterministic/manual column-mapping flow has no agent and therefore no tool-limitation reporting (confirmed scope — Question 1).
- Email delivery reuses the project's existing Resend integration and its existing configuration conventions (provider API key, verified sender address, and a configurable recipient defaulting to `arhambrowser@gmail.com`); no new email provider is introduced.
- The "Reconciliation Atmata" prefix is a credential-free, information-only convention: it exists only so the Developer's Gmail rule can file the message, and no credentials travel in the subject or body.
- The agent can reliably distinguish a tool/engine limitation from an ordinary failure for the failure kinds it currently encounters; where it cannot, it does not report.
- The user-facing loading experience already streams progress updates and already renders a failure message; this feature adds a technical-limitation update and a blue-rendered message rather than replacing the loading screen or the results view.
- The blue notice is tied to the technical-limitation classification, and the email is best-effort alongside it — so the notice is shown even if the email send is skipped or fails.
- The Tool Purpose Summary is short and describes purpose only; it deliberately excludes internal logic, and it lives within the agent's working context (its instructions), not as a user-facing surface.
- "One email per run" means per failing reconciliation attempt; retries within a single run do not each produce an email.
- This feature introduces no new persisted data store; the report exists only as the delivered email plus log entries.
- No automated tests are to be written for this feature, per the project's standing instruction — verification is the manual pass in quickstart.md.
