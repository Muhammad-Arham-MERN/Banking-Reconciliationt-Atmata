---
id: 002
title: Fix slow npm run dev startup
stage: general
date: 2026-06-27
surface: agent
model: claude-4.6-sonnet-medium-thinking
feature: none
branch: main
user: H.A.R
command: npm run dev slow startup via reconciliation_starter_bat.bat
labels: [performance, dev-server, nextjs, starter-script]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
 - reconciliation_starter_bat.bat
 - scripts/wait-for-frontend.ps1
 - frontend/next.config.ts
tests:
 - Cold start timing: server ready ~3s, first /upload compile ~35-46s without cache
 - Warm cache first page load ~490ms
 - wait-for-frontend.ps1 verified end-to-end
---

## Prompt

my npm run dev is extremely slow, it takes so long to finally load up, i am using @reconciliation_starter_bat.bat file as a starter and npm run dev takes very long to load the first time, it should not take this much time

## Response snapshot

Diagnosed that `next dev` itself starts in ~3s; the perceived slowness is the first `/upload` route compile on a cold `.next` cache (35–46s). Next.js also warns about a slow filesystem on the D: project path. Updated the starter bat to pre-warm `/upload` before opening the browser, added `optimizePackageImports` for `lucide-react`, and documented Windows Defender exclusion as the main environmental fix.

## Outcome

- ✅ Impact: Browser opens only after the upload page compiles; repeat starts stay fast when `.next` cache is preserved
- 🧪 Tests: Measured cold/warm compile times; verified wait script
- 📁 Files: reconciliation_starter_bat.bat, scripts/wait-for-frontend.ps1, frontend/next.config.ts
- 🔁 Next prompts: Add project folder to Windows Defender exclusions if cold compiles remain slow
- 🧠 Reflection: The old 5-second timeout opened the browser before Turbopack finished compiling, making the wait feel much longer than it was

## Evaluation notes (flywheel)

- Rating: 4/5
- Rationale: Root cause identified with measurements; UX fix is solid; environmental disk slowness needs user-side Defender exclusion
