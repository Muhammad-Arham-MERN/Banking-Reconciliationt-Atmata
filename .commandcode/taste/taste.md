# Taste (Continuously Learned by [CommandCode][cmd])

[cmd]: https://commandcode.ai/

# imports
- Import utility functions (categorizeTransaction, generateItemId, getDisplayAmount, formatAmount) from @/lib/utils/categorizationUtils, not from @/types/categorization.types. Confidence: 0.75

# typescript
- Use `export type { ... }` syntax when re-exporting types from other modules to satisfy isolatedModules constraint. Confidence: 0.70

# code-style
- Use `/** */` JS comment blocks for file headers, never `#` hash-prefix (invalid in TypeScript/JSX files). Confidence: 0.70

# shadcn
- Prefer using official shadcn UI components over custom hand-rolled implementations. Confidence: 0.60

# nextjs-auth
- Use inline Google sign-in button on protected pages (e.g., /upload) instead of a separate /login sign-in page. Confidence: 0.65

# project-conventions
- Every Python and TypeScript file must begin with `# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ` and end with `# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ` (Islamic Prayer Bookends). Confidence: 0.85

# database
- Remove SQLModel entirely from backend projects; use raw asyncpg for all CockroachDB queries instead. Confidence: 0.75

