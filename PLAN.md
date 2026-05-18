<!-- /autoplan restore point: C:\Users\gandh\.gstack\projects\NeuroSim\master-autoplan-restore-20260518-123610.md -->
# NeuroSim v2.0 — Implementation Plan

## Context
NeuroSim is an AI-powered video analysis platform that simulates neural responses to video content. Currently has a Next.js frontend with Three.js 3D brain visualization, FastAPI backend with simulated TRIBE v2 neural engine, Supabase auth/DB, and PDF report export.

## Current State
- Frontend: Next.js (GitHub Pages static export + Vercel), email/password auth, guest mode, 3D brain heatmap
- Backend: FastAPI on Render, simulated TRIBE v2, Supabase DB layer with in-memory fallback
- Deploy: GitHub Pages live, Vercel blocked by daily deploy limit (100/day)
- Users: 2 DMs on social media expressing interest, pre-product

## Proposed Features (v2.0)
1. **Real-time analysis pipeline** — Process video uploads through simulated neural engine, show live progress
2. **User dashboard improvements** — Video history, comparison view, export options (PDF already done)
3. **Guest-to-user conversion flow** — Capture guest session data, prompt signup after first analysis
4. **Pricing page** — Free tier (simulated) vs Premium (real GPU Modal) comparison
5. **Waitlist integration** — Collect emails for beta launch, show position in queue
6. **Mobile responsive fixes** — Current UI breaks on small screens
7. **Analytics dashboard** — Track usage, popular videos, engagement metrics

## Technical Changes
- Revert `next.config.js` `output: 'export'` for Vercel SSR when deploy limit resets
- Add video upload endpoint with progress tracking (WebSocket or polling)
- Add pricing tier logic to auth context
- Create waitlist table in Supabase
- Add mobile-responsive CSS to dashboard components

## Constraints
- $0/mo deployment target (Vercel + Render free tiers)
- Keep TRIBE v2 simulated for free tier
- Supabase free tier limits (500MB DB, 50K MAU)

<!-- AUTONOMOUS DECISION LOG -->
## Decision Audit Trail

| # | Phase | Decision | Classification | Principle | Rationale | Rejected |
|---|-------|----------|-----------|-----------|----------|----------|
| 1 | CEO Section 1 | Embed widget uses signed URLs (from share links), no separate auth | Auto-decided | P5 (explicit) | Simpler than full auth layer for read-only public embeds | Auth overhead |
| 2 | CEO Section 2 | Add error states for GPU cold start, deleted share links, email bounces | Auto-decided | P1 (completeness) | Missing error paths will cause silent failures | — |
| 3 | CEO Section 3 | Share links use UUIDs, not sequential IDs | Auto-decided | P1 (completeness) | Sequential IDs enable enumeration attack | Sequential IDs |
| 4 | CEO Section 6 | Accept manual QA initially for $0/mo product | Auto-decided | P3 (pragmatic) | Automated test suite overhead exceeds value at pre-PMF stage | Full CI/CD test suite |
| 5 | CEO Section 8 | Add basic request logging to FastAPI | Auto-decided | P1 (completeness) | Zero observability means zero debug capability | — |
| 6 | CEO Section 9 | Deploy less frequently to work around Vercel 100/day limit, avoid paid plan | Auto-decided | P3 (pragmatic) | Paying for Vercel Pro at 2 users is premature | Vercel Pro |
| 7 | CEO Dual Voices | Single-model review (Codex unavailable) | Mechanical | — | No codex CLI on this system | — |

## CEO Review Findings

### Strategic Note (from outside voice — Claude subagent)
The independent CEO reviewer flagged critical concerns about building before finding product-market fit. The user accepted all premises and expansions. Key risks noted: (1) 2 DMs is noise, not signal, (2) 7 features spread thin, (3) no evidence of demand for simulated neural analysis. These are acknowledged per User Sovereignty — the user's direction stands.

### "NOT in scope" (deferred)
- N/A — all expansions accepted by user

### "What already exists"
| Sub-problem | Existing code |
|---|---|
| Video processing | `neurosim/` trial simulation backend |
| PDF export | `backend/pdf_report.py` |
| Email/password auth | `AuthModal.tsx`, `auth-context.tsx` |
| DB with fallback | `database.py`, `schema.sql` |
| 3D brain visualization | `dashboard/Brain3D.tsx` |
| Dashboard layout | `dashboard/page.tsx` |
| Neural engine | `tribe_engine.py`, `bridge_logic.py` |

### Dream State Delta
Current: single-user demo, 2 pre-product DMs
This plan: 7 v2.0 features + 5 expansions deployed to production
12-month ideal: paying users, real GPU tier, analytics-driven decisions, growing distribution

### Error & Rescue Registry
| Method/Code path | What can go wrong | Exception | Rescued? | Rescue action | User sees |
|---|---|---|---|---|---|
| Modal GPU analysis | Cold start 30-60s | TimeoutError | N ← GAP | Add timeout + retry | "Processing on GPU... may take up to 60s" |
| Share link access | Deleted analysis | NotFound | N ← GAP | Return friendly 404 | "This analysis no longer exists" |
| Email digest | Bounce/invalid address | DeliveryError | N ← GAP | Track bounces, disable | "Digest not sent" in settings |
| Embed widget | Backend down | ConnectionError | N ← GAP | Fallback error state | "Analysis unavailable" placeholder |
| Video upload | File too large | SizeLimitError | Y | Reject with message | "File exceeds 50MB limit" |

### Failure Modes Registry
| Code path | Failure mode | Rescued? | Test? | User sees? | Logged? |
|---|---|---|---|---|---|
| Share link | Deleted content | N ← GAP | N | 404 friendly | Y |
| GPU analysis | Cold start timeout | N ← GAP | N | Processing message | Y |
| Embed widget | API unavailable | N ← GAP | N | Error placeholder | Y |
| Email digest | Bounce | N ← GAP | N | Disabled | Y |
| CRITICAL GAPS: 4 (all have clear fixes documented above)

### Phase 1 Completion Summary
```
+====================================================================+
|               CEO REVIEW — COMPLETION SUMMARY                        |
+====================================================================+
| Mode selected        | SELECTIVE EXPANSION                           |
| Premise gate         | All 5 premises accepted by user               |
| Section 1 (Arch)     | 1 issue (embed auth == signed URLs)           |
| Section 2 (Errors)   | 4 error paths mapped, 4 GAPS identified      |
| Section 3 (Security) | 1 issue (enumeration via share link IDs)      |
| Section 4 (Data/UX)  | No unhandled data flow issues                |
| Section 5 (Quality)  | 0 issues (plan is high-level)                 |
| Section 6 (Tests)    | Manual QA acceptable at pre-PMF               |
| Section 7 (Perf)     | 1 risk (Modal cold start latency)             |
| Section 8 (Observ)   | 1 gap (no logging)                            |
| Section 9 (Deploy)   | 1 risk (Vercel deploy limits)                 |
| Section 10 (Future)  | Reversibility: 4/5, debt: acceptable         |
| Section 11 (Design)  | Handled in Phase 2                            |
+--------------------------------------------------------------------+
| NOT in scope         | written (0 items — all accepted)              |
| What already exists  | written                                      |
| Dream state delta    | written                                      |
| Error/rescue registry| 5 methods, 4 CRITICAL GAPS                    |
| Failure modes        | 4 total, 4 CRITICAL GAPS                     |
| Scope proposals      | 5 proposed, 5 accepted                       |
| CEO plan             | written                                      |
| Outside voice        | subagent-only (Codex unavailable)             |
| Lake Score           | 5/5 recommendations chose complete option    |
| Diagrams produced    | architecture (text), data flow (text)         |
+====================================================================+
```

### Expansions Accepted (added to scope)
1. Shareable result links (S effort)
2. Before/after comparison slider (S effort)
3. Real GPU Modal tier (M effort)
4. Weekly email digest (M effort)
5. Public embeddable widget (M effort)

**Phase 1 complete.** Codex: unavailable. Claude subagent: 5 critical concerns (PMF risk, premises, scope, alternatives, competition). Consensus: N/A single-model. Passing to Phase 2.

## Design Review Findings

### Design Litmus Scorecard
| Dimension | Score | Critical issues |
|---|---|---|
| Information hierarchy | 3/10 | 74% of plan is meta-review artifacts, not design spec |
| State coverage | 2/10 | ~25 UI states missing across 10 features + 5 expansions |
| User journey | 1/10 | No first-run experience, emotional arc, or persona |
| UI specificity | 2/10 | All features described generically ("dashboard improvements") |
| Ambiguity resolution | 1/10 | 7 high-stakes UX decisions unresolved |
| Design system | 0/10 | No DESIGN.md, no design tokens, no component library |
| Mobile/responsive | 1/10 | "Mobile responsive fixes" with no breakpoint or layout strategy |
| Accessibility | 0/10 | No mention of keyboard nav, contrast, screen readers, touch targets |

### Key Design Gaps (auto-decided fixes)
1. **Add a Design Brief section** to the plan before implementation — user flow diagram, screen-by-screen inventory, visual priority list
2. **State tables per feature** — Loading/Empty/Success/Error for every UI feature in the plan
3. **Storyboard the GPU cold start window** (30-60s) — this is the biggest retention risk. Specify what the user sees, does, and feels during the wait
4. **Resolve 7 ambiguous decisions before coding:** simulated vs real GPU badge, guest data carry-over, conversion timing, waitlist UX pattern, 3D brain on mobile, comparison slider content, embed widget capability
5. **Add DESIGN.md** — at minimum, color palette, typography, spacing scale, and component patterns

### Dual Voices
Codex: unavailable. Claude subagent: 7 dimensions scored, average 1.4/10. Consensus: N/A single-model.

**Phase 2 complete.** Design: 1.4/10 average. Major gaps documented. Passing to Phase 3.

## Engineering Review Findings

### Eng Litmus Scorecard
| Dimension | Score | Critical issues |
|---|---|---|
| Architecture soundness | 3/10 | Duplicated domain logic diverging (modal_backend.py vs canonical modules), dead test suite, single-process bottleneck |
| Edge case coverage | 2/10 | Unbounded caches (OOM risk), no file cleanup, synchronous blocking upload, seeded simulation by filename |
| Test plan adequacy | 1/10 | Integration tests broken on import, zero frontend tests, zero Supabase failure tests, no engine contract tests |
| Security posture | 4/10 | Public RLS policy bypass, Vercel wildcard rewrite, open CORS on Modal, no rate limiting or auth on API |
| Hidden complexity exposure | 2/10 | Real-time pipeline 3-5x more work than implied, GPU tier cost model absent, guest conversion unhandled, analytics scope too large |
| Resilience and failure modes | 3/10 | 4/4 failure modes unrescued from Phase 1, no retry logic, no background task queue |

### Architecture: Component Structure & Coupling
**CRITICAL: Duplicated domain logic** — `modal_backend.py` contains complete copies of `NeuroSocialBridge`, `TRIBEV2Engine`, `MiroFishSwarm` with slightly different logic than canonical versions in `bridge_logic.py`, `tribe_engine.py`, `mirofish_engine.py`. Any fix must be applied twice. NeuralROI vs ROI are different dataclasses with different rounding.

**HIGH: Dead variable in report generator** — `pdf_report.py:71` reads `analysis.get('summary', {})` but `/upload` response has no `summary` key. Every PDF report shows 0% for all metrics.

**MEDIUM: Dual control plane for engines** — TRIBE and MiroFish are both random-number generators in same process with no abstraction boundary. Switching to real ML means untangling `process_video()` in `main.py:100-186`.

**Fix:** Delete `modal_backend.py` copies and import from canonical modules. Fix PDF report to read top-level metrics. Extract an engine interface before adding real-model paths.

### Edge Cases: What Breaks at 10x / at 2am Friday
**CRITICAL: In-memory caches unbounded** — `_videos_cache` and `_analyses_cache` grow forever with no eviction. Under 10x load (~100 uploads/day) on Render free tier (512MB RAM), process OOMs within days.

**CRITICAL: Synchronous blocking upload** — `/upload` reads full file, writes to disk, then calls `process_video` synchronously. A 2GB upload blocks the entire API. The 15s frontend timeout in `dashboard/page.tsx:60` fires before analysis even starts.

**HIGH: No file cleanup** — Videos land in `settings.upload_dir` (default `./uploads/`) with zero cleanup. Render's ephemeral filesystem (~1GB available) fills up, container crashes.

**HIGH: Seeded simulation collision** — `tribe_engine.py:52` — `np.random.seed(hash(video_path) % (2**32))`. Two videos with same filename get identical "neural predictions." Entire "AI" engine is deterministic random noise keyed on filename.

**MEDIUM: Non-deterministic tests** — `mirofish_engine._simulated_simulation()` uses `random.choices` (stdlib never seeded). Test output fluctuates run to run.

**MEDIUM: Unvalidated what-if endpoint** — `/simulation/what-if/{video_id}` accepts arbitrary dict with no schema validation.

**Fix:** Add TTL-based cache eviction (30min). Move processing to background task queue with status polling. Add file cleanup cron. Stop seeding by filename. Pin stdlib random seed in tests. Add input schema validation.

### Tests: What's Missing
**CRITICAL: Integration test suite broken** — `test_api.py:4` imports `videos_db, analyses_db` from `main` but actual names are `_videos_cache, _analyses_cache`. `pytest` gives ImportError before any test executes.

**HIGH: Zero frontend tests** — 873 lines of dashboard with 6 complex state paths (loading, empty, error, demo, analyzed, A/B testing) and zero tests.

**HIGH: No Supabase failure tests** — `database.py` wraps Supabase calls in `if self.enabled` but neither branch is tested.

**MEDIUM: PDF report untested** — `pdf_report.py` is never called in tests. The broken `summary` key bug would've been caught immediately.

**MEDIUM: No engine contract tests** — No test that `process_video()` returns expected schema shape.

**Fix:** Fix broken imports. Add `pytest` for simulation determinism. Add schema validation test for `process_video` output. Add frontend smoke test.

### Security: New Attack Surface
**HIGH: Public RLS policy in schema** — `schema.sql:30-31` — `CREATE POLICY "Allow all access" ... FOR ALL USING (true)`. Bypasses Supabase RLS entirely. Anyone with Supabase URL/anon key can read/write all data.

**HIGH: Wildcard catch-all in Vercel** — `vercel.json:2` — `{ "source": "/(.*)", "destination": "/frontend/$1" }`. Rewrites all paths, potentially exposing internal routes.

**MEDIUM: Wide-open CORS in modal backend** — `modal_backend.py:48` — `allow_origins=["*"]`. Main backend uses `settings.cors_origins` but Modal deployment is completely open.

**MEDIUM: No rate limiting or auth on API** — Any public endpoint is unprotected. Render URLs are guessable.

**Fix:** Remove public RLS policy in favor of user-id-based policies. Remove/narrow Vercel rewrite. Lock CORS in Modal. Add API key or rate limiting.

### Hidden Complexity: What Looks Simple But Isn't
**CRITICAL: "Real-time analysis progress"** — Plan says "WebSocket or polling." Current code is synchronous. True progress tracking requires: background task executor (Celery/ARQ/RQ), WebSocket handler with reconnect logic, progress reporting from simulation engine (currently just `await asyncio.sleep(1.5)` then returns). This is 3-5x more work than implied.

**CRITICAL: "Real GPU Modal tier"** — Switching from random-number simulation to actual TRIBE v2 involves: downloading 3B-parameter model (multi-GB, 30-60s cold start), 4-bit quantization setup, model load failures/OOM/timeout handling, cost ~$0.50/hr for A10G. Maintaining free+premium paths means two entirely different execution paths pretending to produce comparable results.

**HIGH: "Guest-to-user conversion"** — Guest data lives in `_videos_cache` (in-memory, no user association). Requires: guest session ID in browser (localStorage), merge endpoint reassigning records on signup, race condition handling for returning guests.

**HIGH: "Pricing page + Premium tier"** — Requires Stripe Checkout integration, webhook handling for subscription lifecycle, usage counting (10/mo free), feature gating middleware, and the $29/mo price doesn't cover GPU compute cost.

**HIGH: "Analytics dashboard"** — Zero analytics infrastructure exists. Building requires event pipeline, time-series storage, dashboard with real charts, privacy considerations.

**Fix:** Split progress tracking into clear subtask with WebSocket research. Add cost model before pricing GPU tier. Build guest merge endpoint as prerequisite. Remove analytics dashboard from v2.0 scope.

### Summary

| Severity | Finding | File |
|----------|---------|------|
| CRITICAL | Test suite imports nonexistent variables | `test_api.py:4` |
| CRITICAL | In-memory caches unbounded, OOM risk | `main.py:44-45` |
| CRITICAL | Duplicated domain logic diverging | `modal_backend.py` vs canonical |
| HIGH | PDF report reads nonexistent `summary` key | `pdf_report.py:71` |
| HIGH | Video file storage with no cleanup | `main.py:72` |
| HIGH | Deterministic simulation seeded by filename | `tribe_engine.py:52` |
| HIGH | Public RLS bypass in schema | `schema.sql:30-31` |
| HIGH | 15s frontend timeout for potentially 2GB uploads | `dashboard/page.tsx:60` |
| MEDIUM | Demo fallback data duplicated (100+ lines) | `dashboard/page.tsx:83-135,214-256` |
| MEDIUM | Progress tracking complexity underestimated | Plan item #1 |
| MEDIUM | GPU tier cost model absent from pricing | Plan item #4 + expansion #3 |
| MEDIUM | No input validation on what-if endpoint | `main.py:249-251` |
| LOW | Vercel wildcard rewrite | `vercel.json:2` |

### Dual Voices
Codex: unavailable. Claude subagent: 5 critical, 4 high, 4 medium, 1 low findings. Architecture score 3/10, edge cases 2/10, tests 1/10, security 4/10, hidden complexity 2/10, resilience 3/10.

**Phase 3 complete.** Major engineering gaps: 5 critical, 4 high findings. Retest artifacts written.

### Phase 3.5: DX Review — SKIPPED
No developer-facing scope detected. No SDK, CLI, API docs, or developer portal in v2.0 scope.

## Phase 4: Approval Gate
### Taste Decisions (user sign-off)
| # | Decision | Recommendation | User choice | Override? |
|---|----------|---------------|-------------|-----------|
| 1 | Fix broken test suite first | Yes (fix before features) | ✅ Accepted | — |
| 2 | Delete duplicated modal_backend.py | Yes (delete now) | ✅ Accepted | — |
| 3 | Remove analytics from v2.0 scope | Yes (remove) | ❌ Keep in v2.0 | **OVERRIDE** — user wants analytics in v2.0 |
| 4 | Accept 5 critical gaps as pre-flight | Yes (fix before features) | ✅ Accepted | — |

### Final Status
```
+====================================================================+
|               /autoplan — COMPLETION SUMMARY                        |
+====================================================================+
| Phase 1 (CEO Review)   | DONE — SELECTIVE EXPANSION, 5 expansions  |
| Phase 2 (Design Review)| DONE — avg 1.4/10, DESIGN.md gap flagged  |
| Phase 3 (Eng Review)   | DONE — 5 critical, 4 high findings        |
| Phase 3.5 (DX Review)  | SKIPPED — no developer-facing scope        |
| Phase 4 (Approval)     | DONE — 4 taste decisions, user signed off |
+--------------------------------------------------------------------+
| Review log              | WRITTEN to this file                      |
| Next step               | Suggest /ship for PR creation             |
+====================================================================+
```
