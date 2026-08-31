# Taste (Continuously Learned by [CommandCode][cmd])

[cmd]: https://commandcode.ai/

# imports
- Import utility functions (categorizeTransaction, generateItemId, getDisplayAmount, formatAmount) from @/lib/utils/categorizationUtils, not from @/types/categorization.types. Confidence: 0.75

# typescript
- Use `export type { ... }` syntax when re-exporting types from other modules to satisfy isolatedModules constraint. Confidence: 0.70

# code-style
- Use `/** */` JS comment blocks for file headers, never `#` hash-prefix (invalid in TypeScript/JSX files). Confidence: 0.70
- Prefers safe identifier-style dict/contract keys (underscore form, e.g., `Transaction_Detail`) over human-spaced keys (e.g., `Transaction Detail`): spaced keys are fragile (need quoting, risk trimming/collision), while underscore keys are "safer and reliable" and consistent with the existing `Transaction_date` convention. Explicitly directed switching the discrepancy wire format to `Transaction_Detail`; a slash key like `Debit/Credit` is acceptable to keep. Confidence: 0.75

# shadcn
- Prefer using official shadcn UI components over custom hand-rolled implementations — explicitly requested the dark mode toggle "using shadcn ui (search docs)" rather than a hand-rolled theme switch. Confidence: 0.75

# frontend
See [frontend/taste.md](frontend/taste.md)
# nextjs-auth
- Use inline Google sign-in button on protected pages (e.g., /upload) instead of a separate /login sign-in page. Confidence: 0.65

# project-conventions
- Every Python and TypeScript file must begin with `# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ` and end with `# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ` (Islamic Prayer Bookends); per the constitution's Code Standards 1-3, logical crux methods (agent orchestration, extractors) are additionally marked inline with `# وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ`. Confidence: 0.85

# database
- Remove SQLModel entirely from backend projects; use raw asyncpg for all CockroachDB queries instead. Confidence: 0.75

# python
- Use pandas for general data manipulation; for PDF table extraction specifically, prefer tabula-py (see pdf-extraction section). Confidence: 0.6
- When converting dependencies to uv/pyproject and exact pins are unsatisfiable, the user sanctions basing the declaration on the prod requirements file (`requirements.prod.txt`), which uses `>=` constraints and resolves cleanly — "you can use require prod as well, it also works well" — over fighting the conflicting pins; loose `>=` constraints that let the resolver float to much newer versions (e.g., fastapi 0.141.1, pandas 3.0.5, uvicorn 0.52.1) are acceptable to him. Confidence: 0.6
- Regex patterns (e.g., `date_pattern` in extraction/assessor scripts) must be written as raw string literals (`r"^\d{2} [A-Z]{3} \d{4}$"`), never plain strings — a plain string triggered `SyntaxWarning: invalid escape sequence '\d'` in the structure assessor, which the user pasted as part of the error output to be fixed; the agent's fix was the `r` prefix and the script must then run warning-free. Even WITH the `r` prefix, the backslashes must be verified at the on-disk byte level: an over-escaped `\\d` (two literal backslashes in the actual file) silently compiles to "literal backslash + d" and matches nothing — the real `structure_assessor.py` demo `main()` returned 0 rows with no error or warning, while the agent's scratchpad validation script (single backslash) passed, masking the bug. When an edit tool's escaping is ambiguous (failed edit attempts not matching the bytes), stop guessing at escape counts and inspect the exact bytes via Python (`repr` of the line) and fix programmatically. The same trap recurs when editing agent prompt/instruction strings that embed regex examples: escaping spans three layers (on-disk bytes → Python string value → the prompt text the LLM actually sees), and the read/edit tools can render a view that differs from the raw bytes — a rule example whose on-disk source carried FOUR backslashes (while the tool view showed only two) made the prompt the formatter agent saw contain the double-backslash form the instructions were meant to forbid; always confirm exact bytes via Python `repr` and recompute what the LLM receives before declaring an instruction edit done. NOTE: `repr` itself escapes each backslash for display, so its output is NOT the raw string value — reading `repr` output literally can falsely convince you the runtime value has double backslashes when it has single ones; the unambiguous method is to parse the module with `ast.parse` and evaluate the string literal via `ast.literal_eval`, then print the resulting lines — that is exactly the prompt text the LLM sees, no interpretation layer. Confidence: 0.7
- Production consumers of LLM-emitted regex patterns must tolerate BOTH string forms the agent can emit, not just the canonical one: the raw-string form (`r"^\d{2}/..."` whose runtime value carries double backslashes — compiles to literal backslash + "d" and matches nothing) and the plain-string form (`"^\d{2}/..."` with single backslashes — correct). The user directed this explicitly for the production `src/utils/structure_assessor.py` ("i want you to make sure that it follow both operations, that means it allows both regexes r"" & "", so if values are produced from r"" then bismillah, if produced from just "" then bismillah"), so the production assessor normalizes every incoming pattern at compile time — a `_normalize_date_pattern`/`_compile_date_pattern` helper collapsing `\\` → `\` applied at every compile/match site and at the entry point — rather than requiring the agent to emit exactly one form. Confidence: 0.8
- Production consumers of LLM-emitted regex patterns must tolerate BOTH string forms the agent can emit, not just the canonical one: the raw-string form (`r"^\d{2}/..."` whose runtime value carries double backslashes — compiles to literal backslash + "d" and matches nothing) and the plain-string form (`"^\d{2}/..."` with single backslashes — correct). The user directed this explicitly for the production `src/utils/structure_assessor.py` ("i want you to make sure that it follow both operations, that means it allows both regexes r"" & "", so if values are produced from r"" then bismillah, if produced from just "" then bismillah"), so the production assessor normalizes every incoming pattern at compile time — a `_normalize_date_pattern`/`_compile_date_pattern` helper collapsing `\\` → `\` applied at every compile/match site and at the entry point — rather than requiring the agent to emit exactly one form. Confidence: 0.8

# pdf-extraction
See [pdf-extraction/taste.md](pdf-extraction/taste.md)
# reconciliation
See [reconciliation/taste.md](reconciliation/taste.md)
# agents
See [agents/taste.md](agents/taste.md)
# workflow
See [workflow/taste.md](workflow/taste.md)
- Wants agents defined with explicit function tools for file extraction (e.g., read_excel, read_pdf). Confidence: 0.6

# workflow
See [workflow/taste.md](workflow/taste.md)

# backend-api
- Backend cancellation handling must catch `asyncio.CancelledError` explicitly: in Python 3.8+ it's a `BaseException` (not `Exception`), so a generic `except Exception` in a FastAPI route never catches mid-stream cancellations — they propagate as task cancellation and the client sees a dropped connection / generic error instead of the intended structured 499 response. When a run is cancelled mid-stream, the route should convert it to the same 499 used by inter-stage checks. The user re-diagnosed this exact failure (backend returning 422 on stop instead of a cancel status); the robust fix is to check the cancellation flag in the generic `except Exception` of the streaming/retry loop and re-raise cancellation instead of treating the aborted stream as a retryable failure. Confidence: 0.8
- User-supplied data parameters (e.g., the Excel sheet name) must be captured as user input in the frontend and threaded end-to-end through the API into detection/processing — never hardcoded on the backend; a blank field should fall back to a sensible default (e.g., `"Sheet1"`). The user asked for a "sheetname system" so the system processes the Excel using the sheet name the user provides from the frontend, and the agent wired it across the endpoint (Form field), the detector call, the API client, and the frontend input. Confidence: 0.65
- Keeps all backend HTTP route handlers in the `src/api/` folder (route modules like `ai_routes.py`, `cloud_routes.py`, `auth_middleware.py`) — an endpoint the user cares about (e.g., `/reconcile-ai`) is expected to live there, not scattered elsewhere. Confidence: 0.6
- New endpoints that mirror an existing frontend-called flow (e.g., `/reconcile-ai` alongside the auth-exempt `/karwai`) must be registered in the auth middleware's exempt prefixes so the frontend can call them without a Bearer token — a 401 on such an endpoint signals a missing auth registration, not a routing/location problem (the user attributed the 401 to the route's folder location; the real cause was the exempt-path set). Confidence: 0.65
- Backend pydantic-settings config must tolerate undeclared env vars in `.env` (`extra = "ignore"` on the Settings Config): the user adds API keys directly to .env (e.g., `NANONETS_API_KEY`) that aren't referenced anywhere in code, and a boot crash caused by such a key (newer pydantic forbids extra env vars by default, older pins silently allowed them) is a regression to fix — the key is intentional and should not be removed, the config should keep matching the old tolerant behavior. Confidence: 0.65
