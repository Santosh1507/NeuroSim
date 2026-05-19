# NeuroSim v2.4 — Deferred Items

Items deferred from the v2.3 autoplan review. These are not critical blockers but should be addressed before onboarding real users.

## Eng: Architecture & Maintainability

- [x] **Analysis deletion endpoint** — `DELETE /analyses/{video_id}` implemented. Cleans caches, share links (via reverse map), and Supabase.
- [x] **Upload MIME validation** — `_is_video_magic()` checks ftyp/RIFF+AVI/EBML signatures from first 32 bytes. Zero dependencies.
- [x] **Supabase/cache abstraction leak** — `StorageAdapter` class wraps Supabase + in-memory cache behind a unified interface. Supabase is primary, in-memory is read-through cache. Export `store` singleton and `_supabase`/`_videos_cache`/`_analyses_cache` for legacy endpoint compatibility.

## Eng: Tests

- [x] **Missing module tests** — `database.py` (12 async tests, fallback mode) and `transcriber.py` (7 whisper-agnostic tests) now have coverage.
- [x] **Slow API tests** — Artificial 2.3s delay per analysis test via `NEUROSIM_SYNC_MODE`. Tests are functional but slow. **Resolved in v2.4c** — delays reduced.
- [x] **mirofish_engine.py & pdf_report.py tests** — These two modules still lack dedicated test coverage. **Added in v2.4c** — 206-line mirofish test suite + 153-line PDF report test suite.

## Eng: Security (demo-acceptable, address before real users)

- [x] **No auth enforcement** — JWT validation added via `require_auth_user` + `get_verified_user_id` dependencies in v2.5. Protected endpoints: DELETE, merge, share, digest. Dev mode passthrough when no JWT secret is set.
- [x] **Share link expiration** — 7-day TTL added in v2.3. Expired links return 410 with clear message.

## Eng: Background Processing

- [x] **Periodic cleanup sweep** — Background asyncio task runs every 60s in lifespan, resets `_last_eviction` gate to force `_evict_stale()`.
- [x] **No cache warming** — `GET /api/warmup` endpoint added. Calls `store.warmup()` which preloads cache from Supabase. Render cron job (`*/5 * * * *`) via `warmup_cron.py` keeps cache warm after cold restarts.

## Eng: Payments & Billing

- [x] **Stripe checkout scaffold** — `POST /api/stripe/create-checkout-session` creates Stripe Checkout sessions with subscription mode and user_id metadata. `POST /api/stripe/webhook` handles lifecycle events (`checkout.session.completed` → activates premium, `customer.subscription.deleted` → logs teardown, `invoice.payment_failed` → logs alert). Pricing page updated: fetches premium status on mount, uses Stripe Checkout redirect when configured (falls back to waitlist).

## Design

- [x] **Accessibility audit** — Addressed in v2.5: AuthModal focus trap + ARIA (`role="dialog"`, `aria-modal`, `aria-labelledby`, `aria-required`, `aria-busy`, `role="alert"`), landing page section ARIA labels, pricing page radio group with keyboard nav + WAI-ARIA radiogroup pattern.
- [x] **Landing/pricing unification** — Unified in v2.5: buttons use DESIGN.md `btn-neural`/`btn-ghost` classes, feature card colors use `text-neural`/`text-swarm`/`text-signal-green` CSS custom properties instead of Tailwind defaults.
- [x] **Motion token audit** — `frontend/src/lib/easing.ts` created with all CSS easing tokens (`--ease-out-expo`, `--ease-spring`, `--ease-smooth`) as Framer Motion constants. All 9 frontend pages updated to use `fadeIn`, `heroReveal`, `staggerItem`, `tabSwitch`, `pulseSlow`, `scanLine`, `hoverLift`, `tapPress` etc. instead of inline `cubic-bezier` values.

## Product

- [x] **Email digest delivery tracking** — `POST /api/digest/send` endpoint added with delivery status tracking (`sent_at`, `status`). `GET /api/digest/subscriptions` lists active subscriptions. Backend scaffold now tracks delivery state.
- [x] **Analysis persistence** — `StorageAdapter` uses Supabase as primary store with in-memory as cache layer. All reads check Supabase first (when enabled), fall back to cache. Background `_evict_stale()` and `warmup()` keep layers in sync.

---

## How to Use

Check items off as `[x]` when implemented. Items are ordered roughly by priority — start from the top.
