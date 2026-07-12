# Tasks: Google OAuth Authentication with Auth.js

**Input**: Design documents from `/specs/001-auth/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/auth-contracts.md

**Tests**: Not requested in spec — no test tasks generated.

**Constitution Compliance**: Every new file MUST include `بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيمِ` as the first line and `وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ` as the last line. Auth middleware and route guard logic MUST be prefixed with `وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ`. These markers are applied at file creation time in each task below.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- Web app: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependencies, and environment configuration

- [X] T001 Install frontend dependencies: `npm install next-auth@beta @auth/pg-adapter pg` from `frontend/`
- [X] T002 Install backend dependencies: `pip install pyjwt asyncpg` from `backend/`
- [X] T003 [P] Create `frontend/.env.local` with AUTH_GOOGLE_ID, AUTH_GOOGLE_SECRET, AUTH_SECRET, DATABASE_URL
- [X] T004 [P] Create `backend/.env` with NEXTAUTH_SECRET, DATABASE_URL

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Create CockroachDB connection module in `backend/src/services/db_service.py` using `pg`-compatible connection (or `asyncpg`)
- [X] T006 Create database migration SQL in `backend/src/models/db_migrations.py` — reconciliation_data table CREATE + users.files ALTER TABLE
- [X] T007 [P] Add backend config entries for DATABASE_URL and NEXTAUTH_SECRET in `backend/src/config.py`

**Checkpoint**: Foundation ready — CockroachDB is connectable, tables will be created, env vars configured

---

## Phase 3: User Story 1 - User Signs In with Google (Priority: P1) 🎯 MVP

**Goal**: Unauthenticated users see a Google Sign-In button, complete OAuth flow, and access the main application. Auth.js manages sessions with 24-hour expiry.

**Independent Test**: Open app in private browser → see Google Sign-In button → sign in → see main application → reopen within 24 hours → auto-authenticated

### Implementation for User Story 1

- [X] T008 [P] [US1] Create Auth.js config in `frontend/src/lib/auth.ts` — configure Google provider, PostgreSQL adapter, JWT strategy, 24-hour `maxAge`
- [X] T009 [P] [US1] Create Auth.js route handler in `frontend/src/app/api/auth/[...nextauth]/route.ts` — re-export `handlers` from auth config
- [X] T010 [P] [US1] Create SessionProvider wrapper component in `frontend/src/components/providers/session-provider.tsx`
- [X] T011 [P] [US1] Update `frontend/src/app/layout.tsx` — wrap with SessionProvider
- [X] T012 [P] [US1] Create login page in `frontend/src/app/login/page.tsx` — Google Sign-In button, redirect to main app after auth
- [X] T013 [P] [US1] Create Google Sign-In button component in `frontend/src/components/auth/sign-in-button.tsx`
- [X] T014 [US1] Implement route protection — create `frontend/src/middleware.ts` to redirect unauthenticated users to `/login`
- [X] T015 [P] [US1] Create backend auth verification middleware in `backend/src/api/middleware.py` — decode JWT, inject X-User-Id/X-User-Email headers
- [X] T016 [US1] Implement backend JWT verification service in `backend/src/services/auth_service.py`
- [X] T017 [US1] Integrate auth middleware into `backend/src/main.py` — attach to request pipeline
- [X] T018 [US1] Add OAuth error handling — user-friendly error message on sign-in page when Google OAuth fails
- [X] T019 [US1] Add session expiry handling — redirect expired sessions to `/login` via middleware

**Checkpoint**: At this point, User Story 1 should be fully functional — sign-in, session management, route protection, backend auth all work

---

## Phase 4: User Story 2 - User Signs Out (Priority: P2)

**Goal**: Authenticated users can sign out, terminating their session, and are returned to the sign-in screen.

**Independent Test**: Sign in → click sign-out → returned to sign-in screen → attempt to access app URL → redirected to sign-in

### Implementation for User Story 2

- [X] T020 [P] [US2] Create sign-out button component in `frontend/src/components/auth/session-status.tsx` — displays user info + sign-out button
- [X] T021 [US2] Integrate session status into app layout — show user avatar/name + sign-out in header/navbar in `frontend/src/app/layout.tsx`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work — full auth lifecycle (sign-in, session, sign-out)

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T022 Enable Auth.js auto-creation of auth tables — verify on first run that users/accounts/sessions/verification_token tables are created by `@auth/pg-adapter`
- [X] T023 Run `ALTER TABLE users ADD COLUMN files JSONB DEFAULT '[]'::jsonb;` — extend users table
- [X] T024 Run `CREATE TABLE reconciliation_data (...)` — create reconciliation data table
- [X] T025 Run quickstart.md verification steps — full auth flow test end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Stories (Phase 3–4)**: All depend on Foundational completion
- **Polish (Phase 5)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on US2
- **US2 (P2)**: Can start after Foundational (Phase 2) — independent from US1

### Within Each User Story

- Auth.js config (T008) before route handler (T009)
- Components before layout integration
- Backend services before middleware integration
- Story complete before moving to next priority

### Parallel Opportunities

- **Setup**: T003 and T004 can run in parallel
- **Foundational**: T005, T006 can be done together
- **US1**: T008, T009, T010, T012, T013, T015 can all run in parallel
- **US1 sequential**: T011 depends on T010, T014 depends on T011, T018/T019 depend on T012
- **US2**: T020, T021 sequential
- Stories can run sequentially (P1 → P2)

---

## Parallel Example: User Story 1

```bash
# Launch all independent files for User Story 1 together:
Task: "Create Auth.js config in frontend/src/lib/auth.ts"
Task: "Create Auth.js route handler in frontend/src/app/api/auth/[...nextauth]/route.ts"
Task: "Create SessionProvider wrapper in frontend/src/components/providers/session-provider.tsx"
Task: "Create login page in frontend/src/app/login/page.tsx"
Task: "Create sign-in button in frontend/src/components/auth/sign-in-button.tsx"
Task: "Create backend auth middleware in backend/src/api/middleware.py"
```

## Parallel Example: User Story 2

```bash
# Launch all independent files for User Story 2:
Task: "Create sign-out button + session display in frontend/src/components/auth/session-status.tsx"
Task: "Integrate session-status into layout in frontend/src/app/layout.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test sign-in flow independently
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready (DB, env vars)
2. Add User Story 1 → Sign-in works → Deploy/Demo (MVP!)
3. Add User Story 2 → Sign-out works → Deploy/Demo
4. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- No test tasks generated — tests not requested in spec
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
