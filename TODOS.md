# NeuroSim v2.4 — Deferred Items

Items deferred from the v2.3 autoplan review. These are not critical blockers but should be addressed before onboarding real users.

## Eng: Architecture & Maintainability

- [x] **Analysis deletion endpoint** — `DELETE /analyses/{video_id}` implemented. Cleans caches, share links (via reverse map), and Supabase.
- [x] **Upload MIME validation** — `_is_video_magic()` checks ftyp/RIFF+AVI/EBML signatures from first 32 bytes. Zero dependencies.
- [ ] **Supabase/cache abstraction leak** — Analysis data wraps inconsistently between Supabase (`{"data": {...}}`) and in-memory cache (flat). The `_get_analysis_or_404` helper normalizes this, but the leaky storage layer remains. Consider a `StorageAdapter` interface.

## Eng: Tests

- [x] **Missing module tests** — `database.py` (12 async tests, fallback mode) and `transcriber.py` (7 whisper-agnostic tests) now have coverage.
- [ ] **Slow API tests** — Artificial 2.3s delay per analysis test via `NEUROSIM_SYNC_MODE`. Tests are functional but slow.
- [ ] **mirofish_engine.py & pdf_report.py tests** — These two modules still lack dedicated test coverage.

## Eng: Security (demo-acceptable, address before real users)

- [ ] **No auth enforcement** — API accepts arbitrary `user_id` query params with no validation. Any user can masquerade as any other user.
- [x] **Share link expiration** — 7-day TTL added in v2.3. Expired links return 410 with clear message.

## Eng: Background Processing

- [x] **Periodic cleanup sweep** — Background asyncio task runs every 60s in lifespan, resets `_last_eviction` gate to force `_evict_stale()`.
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
