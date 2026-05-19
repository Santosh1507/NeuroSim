# NeuroSim v2.4 — Deferred Items

Items deferred from the v2.3 autoplan review. These are not critical blockers but should be addressed before onboarding real users.

## Eng: Architecture & Maintainability

- [ ] **Analysis deletion endpoint** — Users cannot delete analyses. With share links in play, there's no way to revoke access. Minor for demo, problematic for real usage.
- [ ] **Supabase/cache abstraction leak** — Analysis data wraps inconsistently between Supabase (`{"data": {...}}`) and in-memory cache (flat). The `_get_analysis_or_404` helper normalizes this, but the leaky storage layer remains. Consider a `StorageAdapter` interface.
- [ ] **Upload MIME validation** — Extension-only validation (`.mp4`, `.mov`, etc.) with no magic byte checking. Real users could upload non-video files.

## Eng: Tests

- [ ] **Missing module tests** — `database.py`, `transcriber.py`, `mirofish_engine.py`, `pdf_report.py` have no tests.
- [ ] **Slow API tests** — Artificial 2.3s delay per analysis test via `NEUROSIM_SYNC_MODE`. Tests are functional but slow.

## Eng: Security (demo-acceptable, address before real users)

- [ ] **No auth enforcement** — API accepts arbitrary `user_id` query params with no validation. Any user can masquerade as any other user.
- [ ] **Share links never expire** — Added 7-day TTL in v2.3, but no user-facing revoke mechanism.

## Eng: Background Processing

- [ ] **No periodic cleanup** — `_evict_stale()` is called on request and is now rate-limited to 30s intervals. Consider a background sweep for long-running sessions with no API calls.
- [ ] **No cache warming** — Free-tier Render instances sleep after inactivity. First request wakes the server AND runs analysis. Consider a warm-up endpoint for premium users.

## Design

- [ ] **Accessibility audit** — `/design-review` scored 5-6/10. Missing: `aria-*` attributes, focus traps in modals, keyboard navigation paths. DESIGN.md spec is comprehensive but partial implementation.
- [ ] **Landing/pricing unification** — Landing page uses inline Tailwind styling while dashboard uses `glass-panel` system. Pricing page deviates from glass panel system.
- [ ] **Motion token audit** — Custom CSS easing properties defined but never used in Framer Motion transitions. `ease-[cubic-bezier(...)]` tokens should be referenced consistently.

## Product

- [ ] **Email digest delivery tracking** — Digest subscriptions write to in-memory dict with zero delivery validation. Scaffolding only.
- [ ] **Analysis persistence** — In-memory cache loses analyses on server restart. Supabase persistence is optional and soft-fails silently.

---

## How to Use

Check items off as `[x]` when implemented. Items are ordered roughly by priority — start from the top.
