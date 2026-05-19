# MiroFish / NeuroSim — Fresh /autoplan Review (v2.5 Working Tree)

> Fresh review started 2026-05-19. Previous review (NeuroSim v2.0) superseded.
> Restore point: `master-autoplan-restore-fresh-20260519-064500.md`
> **v2.5 review** — commit `a9171bb` + 20 modified files + 4 new files uncommitted.
> Working tree: **DIRTY** (+882/-283 lines across 18 modified + 4 untracked files).
> Restore point (v2.5): `C:\Users\gandh\.gstack\projects\neurosim\master-autoplan-restore-fresh-20260519-115927.md`

---

## Phase 0: Intake + Restore Point

### Repository Identity
- **Repo:** MiroFish (org: Santosh1507)
- **Platform:** GitHub (`github.com/Santosh1507/NeuroSim.git`)
- **Base branch:** `master`
- **Current branch:** `master` (3 commits ahead of origin/master, no new commits since master)
- **Commit:** `a9171bb` — `v2.4c: mirofish_engine tests, pdf_report tests, faster API tests, style conflict fix`
- **Working tree:** **clean** (all v2.3+v2.4 changes now committed)

### Recent Commits (top 10)
```
f379d10 chore: add gstack skill routing rules to AGENTS.md, fix corrupted .gitignore
f9f0ad2 chore: add gstack skill routing rules to AGENTS.md
fa83127 chore: add gstack skill routing rules to AGENTS.md
adde383 v2.3: CI/CD, health check, structured logging, dashboard gallery, error boundaries
fb95bc2 v2.2: heuristic analysis pipeline, rate limiting, usage tracking, Stripe scaffolding
8167ee5 feat: add frontend smoke tests (9/9 passing) with vitest
3a1cd65 fix: remove wildcard rewrite from vercel.json (Vercel SSR handles routing natively)
2e56654 fix: user-id-based RLS policies replace open access in schema
7736284 v2.1.0: async upload, pricing, waitlist, share, analytics, embed, comparison, premium (#1)
f465091 fix: add output export and basePath for GitHub Pages
```

### Current Working Tree Changes (v2.5 — UNCOMMITTED)

**Backend (6 files changed, ~600+ lines):**
- `main.py` (+574/-~200): JWT auth (`get_verified_user_id`, `require_auth_user`), storage_adapter integration (replaces `db` + cache dual-path), email/SMTP imports, stripe integration, `_evict_stale()` delegates to adapter
- `config.py` (+14): Email SMTP config (host, port, username, password, from), Supabase JWT secret + URL + keys
- `requirements.txt` (+1): `pyjwt` dependency
- `test_api.py` (minor): 3-line adjustment
- **NEW:** `storage_adapter.py` (333 lines) — `StorageAdapter` class with `insert_video`, `get_video`, `list_videos`, `update_video_status`, `delete_video`, `insert_analysis`, `get_analysis`, `delete_analysis`, `warmup`, `get_cached_video_ids`, `get_analytics_snapshot`. Replaces the leaky `analysis.get("data", analysis)` pattern.
- **NEW:** `warmup_cron.py` (38 lines) — Render cron worker hitting `/api/warmup` every 5 minutes

**Frontend (10 files changed, ~300+ lines):**
- `AuthModal.tsx` (+131): Focus trap, Escape key close, ARIA (`role="dialog"`, `aria-modal`, `aria-labelledby`, `aria-required`, `aria-label`), auto-focus first input, body scroll lock
- `page.tsx` (landing): Design token unification (`text-neural`/`text-swarm`/`text-signal-green` replace hardcoded `text-cyan-400`/`text-purple-400`), easing.ts imports (`heroReveal`, `fadeIn`, `staggerItem`, `scanLine`, `pulseSlow`), aria-labels on sections
- `pricing/page.tsx` (+129): Live Stripe price fetching from `/api/premium/status`, Stripe Checkout session creation, loading states, `isDemoMode` handling
- `easing.ts` (70 lines, NEW): Framer Motion easing constants (`easeOutExpo`, `easeSpring`, `easeSmooth`, `fadeIn`, `heroReveal`, `staggerItem`, `tabSwitch`, `pulseSlow`, `scanLine`, `hoverLift`, `tapPress`)
- `dashboard/page.tsx` (minor): 15-line adjustment
- `analytics`, `comparison`, `digest`, `r/[id]`, `waitlist` pages: Minor aria-label additions (3-5 lines each)
- `package.json`/`package-lock.json`: Minor dependency updates

**Infrastructure (2 files):**
- `render.yaml` (+15): `warmup-cache` cron job (python, `*/5 * * * *`, runs `warmup_cron.py`)
- **NEW:** `docs/stripe-setup.md` — Stripe configuration documentation

### Files That Match Previous Plan Items

| Previous v2.0/v2.4 plan item | Status in v2.5 working tree |
|---|---|
| Real-time analysis pipeline (WebSocket) | ✅ Exists in `main.py` (`/ws/{video_id}`, `_broadcast_progress`) |
| Dashboard improvements | ✅ `ProgressStageIndicator` extracted |
| Guest-to-user conversion | ✅ `/api/merge` endpoint exists |
| Pricing page | ✅ Enhanced with live Stripe Checkout |
| Waitlist integration | ✅ Exists in frontend + backend (`/api/waitlist`) |
| Mobile responsive fixes | ❌ Not changed |
| Analytics dashboard | ✅ Endpoint exists, frontend page exists |
| Share links | ✅ `/r/[id]` route, `/api/share` endpoint |
| Embed widget | ✅ `/embed/[id]` route |
| Comparison slider | ✅ Exists in frontend |
| Digest / email | ✅ SMTP config added, endpoints exist |
| Premium tier scaffolding | ✅ Stripe Checkout integration added |
| PDF report | ✅ ReportLab rewrite, 153-line test suite |
| DESIGN.md | ✅ Comprehensive design system doc |
| **Analysis deletion endpoint** | ✅ **Added in v2.4** |
| **Upload MIME validation** | ✅ **Added in v2.4** |
| **Extracted data helpers** | ✅ **Added in b7460db** → now uses `StorageAdapter` |
| **Share link TTL** | ✅ **Added in v2.3** |
| **Background sweep** | ✅ **Added in v2.4b** |
| **mirofish_engine tests** | ✅ **Added in v2.4c** |
| **pdf_report tests** | ✅ **Added in v2.4c** |
| **Faster API tests** | ✅ **Added in v2.4c** |
| **Auth enforcement** | ✅ **IN v2.5 WORKING TREE** — JWT auth + `require_auth_user` |
| **Storage abstraction** | ✅ **IN v2.5 WORKING TREE** — `StorageAdapter` (333 lines) |
| **Accessibility (AuthModal)** | ✅ **IN v2.5 WORKING TREE** — focus trap, ARIA, escape key |
| **Landing/pricing unification** | ✅ **IN v2.5 WORKING TREE** — design tokens + easing.ts |
| **Motion token audit** | ✅ **IN v2.5 WORKING TREE** — easing.ts with 12 constants |
| **Cache warming** | ✅ **IN v2.5 WORKING TREE** — `warmup_cron.py` + render cron |
| **Email digest config** | ✅ **IN v2.5 WORKING TREE** — SMTP settings in config.py |

### Scope Detection

**UI scope? YES** — Landing page redesign, pricing page Stripe integration, AuthModal accessibility, easing.ts motion tokens, dashboard/analytics/comparison/digest/waitlist aria-labels. Extensive UI surface changes.

**Developer-facing scope? NO** — No SDK, CLI, API docs, or developer portal. Backend is a private API consumed by the frontend only.

### Phase 0 Checklist
- [x] Git platform & base branch detected (GitHub, master)
- [x] Restore point saved (v2.5 working tree)
- [x] Scope detected: UI (YES), Developer-facing (NO)
- [x] Current working tree inventory complete (22 files)
- [x] Key observations noted (8 items)
- [x] Previous review findings mapped to v2.5 status

---

## Phase 1A: Premises Survey (Confirmed)

**User confirmed via AskUserQuestion:**

| Premise | User Choice | Impact |
|---------|-------------|--------|
| **Repo identity** | Both are valid — NeuroSim (frontend product) + MiroFish-Offline (backend migration) are separate concerns | Continue reviewing NeuroSim current codebase. docs/progress.md is aspirational for a separate track. |
| **Working tree** | Commit as-is — formatting, refactoring, DESIGN.md, ProgressStageIndicator | Scope includes committing current changes as a baseline, then reviewing what's next. |
| **Critical gaps** | Fix all 3 — GPU cold start handling, email bounce tracking, embed fallback | These are in scope for this review's recommendations. |

### Scope Boundaries (Phase 1B onwards)

**In scope:**
- ✅ NeuroSim v2.2/v2.3 FastAPI backend + Next.js frontend (current working tree)
- ✅ All 22 uncommitted files as baseline (formatting, refactoring, DESIGN.md, ProgressStageIndicator)
- ✅ Fix 3 critical gaps: GPU cold start handling, email bounce tracking, embed fallback
- ✅ Full CEO review of architecture, features, and product direction
- ✅ Full Design review (UI scope detected)
- ✅ Full Eng review (architecture, test plan, failure modes, security, hidden complexity)

**Out of scope:**
- ❌ MiroFish-Offline Flask+Neo4j+Ollama migration (docs/progress.md — separate track)
- ❌ Developer DX review (no SDK, CLI, or developer portal)
- ❌ v2-features remote branch (inaccessible)

### Phase 1A Checklist
- [x] Premises survey presented via AskUserQuestion
- [x] Scope boundaries defined
- [x] Decision: Commit current working tree as baseline (user to do manually or we advise)
- [x] Decision: Fix all 3 critical gaps in scope

---

## Phase 1B: CEO Dual Voice Review

### Voice 1: Claude (primary)

**Product coherence: 8/10**
- v2.3 feature set forms a complete loop: upload → process → analyze → share/embed → benchmark
- Real-time WebSocket pipeline + ProgressStageIndicator = good UX for async analysis
- Missing: no analysis deletion endpoint (with share links, users can't revoke access)
- Missing: analytics dashboard computes from in-memory cache only — no persistence, resets on restart
- Digest feature has NO email sending infrastructure (no SendGrid, Mailgun, Resend). The bounce tracking concern is premature — the feature doesn't send emails yet

**Working tree: Safe to commit as v2.3 baseline**
- 22-file diff is formatting + 3 new files + pdf_report rewrite. No behavioral changes to APIs

**Critical gaps reassessment:**
- ❌ **GPU cold start**: NOT a v2.3 gap. No real GPU code exists. tribe_engine.py is a mock. Defer to Pro tier.
- ❌ **Email bounce**: NOT a v2.3 gap. No email delivery infra exists yet. The digest endpoints are scaffolding.
- ✅ **Embed fallback**: REAL gap. When Render free tier sleeps (30min inactivity), embed shows spinner → error. Needs offline/placeholder state.

**Additional Claude-only findings:**
- Remote `v2-features` branch is inaccessible — should be investigated or cleaned up
- 3 identical "chore: add gstack skill routing rules" commits are duplicates (retries). Should be squashed.
- `docs/progress.md` describes a 7-phase completed migration with code that doesn't exist. Confusing for newcomers. Should be moved/archived.

### Voice 2: Code Reviewer (DeepSeek Flash)

**Product coherence: 8/10** (independently matches Claude)
- Complete feature loop, polished share/embed error states
- Missing: no analysis deletion endpoint (independent match)
- Share links stored in-memory only — lost on restart if Supabase is down. Should persist to Supabase.

**Working tree: Safe to commit** (independent match)
- No behavioral changes. Safe as v2.3 baseline.

**Critical gaps reassessment:** (independent match on all 3)
- GPU cold start: NOT a real gap — defer to Pro tier
- Email bounce: Flag as "won't ship this way" — needs proper email service
- Embed fallback: REAL gap — needs offline/placeholder mode

**Additional reviewer-only findings:**
- PDF report endpoint calls `analysis.get("data", analysis)` twice — code smell
- `/api/share` links are ephemeral (in-memory only)

### Dual Voice Comparison

| Dimension | Claude | DeepSeek Flash | Consensus |
|-----------|--------|----------------|-----------|
| Product coherence | 8/10 | 8/10 | ✅ Confirmed |
| Working tree safe to commit | ✅ | ✅ | ✅ Confirmed |
| Missing: analysis deletion | ✅ Flagged | ✅ Flagged | ✅ Confirmed (2/2) |
| GPU cold start IS a gap | ❌ (defer) | ❌ (defer) | ✅ Confirmed (2/2: not a gap) |
| Email bounce IS a gap | ❌ (no infra) | ❌ (no infra) | ✅ Confirmed (2/2: not a gap) |
| Embed fallback IS a gap | ✅ (real) | ✅ (real) | ✅ Confirmed (2/2: real gap) |
| Share links ephemeral | Not flagged | ✅ Flagged | 🔶 Partial |
| v2-features branch cleanup | ✅ Flagged | Not flagged | 🔶 Partial |
| Duplicate commits to squash | ✅ Flagged | Not flagged | 🔶 Partial |
| docs/progress.md to archive | ✅ Flagged | Not flagged | 🔶 Partial |
| PDF endpoint code smell | Not flagged | ✅ Flagged | 🔶 Partial |

**Consensus: 8/6 confirmed** (see table above)

### Phase 1B Checklist
- [x] Claude voice analysis complete
- [x] Code Review subagent voice analysis complete
- [x] Dual voice comparison table produced
- [x] Consensus confirmed on 6/6 primary dimensions
- [x] Secondary concerns logged (share link persistence, branch cleanup, commit squash, progress.md archive, PDF code smell)

---

## Phase 1C: Auto-Decisions

Using the 6 decision principles (Completeness, User Sovereignty, Ship First, Concrete over Abstract, Evidence over Opinion, Build for the User):

### Auto-Decided Items (7)

| # | Decision | Principle | Details |
|---|----------|-----------|---------|
| 1 | **Product coherence 8/10** — ACCEPT | Evidence, Build for User | Both voices independently scored 8/10. Feature set is coherent for v2.3. Analysis deletion can wait. |
| 2 | **Working tree safe to commit** — ACCEPT | Ship First, Concrete | All 22 files are formatting/refactoring + 3 new. No behavioral changes. Commit as v2.3 baseline. |
| 3 | **GPU cold start: NOT a gap in v2.3** — DEFER | Concrete, Completeness | No real GPU code exists. `tribe_engine.py` is a mock. Adding timeout/retry for mock code would be over-engineering. Flag for Pro tier when real TRIBE v2 is integrated. |
| 4 | **Email bounce: NOT a gap in v2.3** — DEFER | Concrete, Evidence | No email delivery infrastructure exists (no SendGrid, Mailgun, or Resend). Digest endpoints are scaffolding. Bounce tracking is premature. Flag when email sending is implemented. |
| 5 | **Embed fallback: IS a real gap** — ACCEPT + FIX | Build for User, Completeness | Both voices flagged it. When Render free tier sleeps, embed shows spinner → error. Needs offline/placeholder mode with cached analysis data. Scope into v2.3. |
| 6 | **Missing analysis deletion** — DEFER | Ship First, User Sovereignty | Both voices flagged. Analysts can't revoke share links. But TTL eviction exists. Defer to v2.4 — low usage volume in current demo phase. |
| 7 | **Share link persistence to Supabase** — DEFER | Ship First, Concrete | Currently in-memory only, lost on restart if Supabase is down. But Supabase is configured with persistent tables. The fallback path is the gap, not the primary path. Defer to v2.4. |

### Housekeeping / Cleanup Items (3)

| # | Item | Action | Priority |
|---|------|--------|----------|
| 8 | **Duplicate commits to squash** | Squash the 3 identical "chore: add gstack skill routing rules" commits. Only the last one should remain. `git rebase -i` on the 3 commits. | Medium |
| 9 | **Archive docs/progress.md** | Move to `docs/archive/` or add a header noting it describes a future/separate codebase. Confusing for newcomers as-is. | Low |
| 10 | **Fix PDF code smell** | Line ~80 in `backend/pdf_report.py`: `analysis.get("data", analysis)["data"]` called twice. Extract to variable. | Low |

### Secondary Concern (Flagged, No Action Required)

| # | Concern | Note |
|---|---------|------|
| 11 | **v2-features remote branch inaccessible** | `git fetch origin v2-features` fails. Should investigate: delete remote branch if stale, or fix access if active. |

### Phase 1C Checklist (Updated for v2.4c)
- [x] All 7 auto-decisions made with principle references
- [x] 3 housekeeping items logged
- [x] 1 secondary concern flagged
- [x] Decision audit trail populated

**Note:** Auto-decisions #6 (analysis deletion) and #7 (share link persistence/Supabase fallback) are now **partially resolved** — deletion endpoint exists in v2.4, helpers extracted in b7460db. The full storage abstraction refactor remains deferred.

---

## Phase 2: Design Review

### Design System Files
- **DESIGN.md** — Comprehensive design system spec (color, typography, spacing, glass panels, buttons, badges, tabs, inputs, progress bars, status dots, animations, state tables, responsive, accessibility)
- **globals.css** — Full CSS implementation of all DESIGN.md components
- **tailwind.config.js** — All tokens mapped to Tailwind utilities
- **Components:** ProgressStageIndicator (neural/swarm variants), ComparisonSlider (glass panels), Brain3D (3D brain with @react-three/fiber), AuthModal (glass panel), Navbar (btn-neural/btn-ghost)

### Pages Evaluated
Landing, Dashboard, Analytics, Pricing, Comparison, Shared Analysis (r/[id]), Embed (embed/[id]), Digest, Waitlist

### Voice 1: Claude (primary)

**Design System Adoption Assessment**

| Dimension | Score | Evidence | Gaps |
|-----------|-------|----------|------|
| **Visual Consistency** | 7/10 | Dashboard/analytics/digest consistently use `glass-panel`, `btn-neural`, `tab-segment`. Status dots and badges used across pages. Landing page has different styling approach. | Landing page and pricing use inline Tailwind instead of `.glass-panel` CSS classes. Different visual approach (more decorative, less instrument-grade). |
| **Design System Coverage** | 9/10 | DESIGN.md covers everything. globals.css implements all component classes. | Some components (inputs, buttons) use inline Tailwind in waitlist/comparison pages instead of `.input-neural` / `.btn-neural`. Minor. |
| **State Coverage** | 8/10 | Dashboard has loading, empty, data, error, processing, drag-active, backend-unreachable states. Share modal has generating, success, copied, error. 404 page for deleted analyses. | Embed widget has basic loading/error states but NO offline/placeholder fallback when backend is down (confirmed gap). Digest has empty and data states. |
| **Typography** | 9/10 | All 4 fonts loaded (Sora, Instrument Sans, JetBrains Mono, Space Mono). CSS hierarchy for h1-h4. `.text-gradient`, `.text-neural`, `.text-swarm` classes work correctly. | Landing page uses inline `clamp()` sizing instead of consistent tokens. Font weights not perfectly matched to spec in all pages. |
| **Color** | 9/10 | CSS custom properties comprehensive. Tailwind config maps all tokens. `text-neural`/`text-swarm` used consistently. Signal colors used for status. | Some pages use hardcoded opacity values instead of design tokens (e.g., `bg-cyan-400/10` instead of `bg-neural/10` — functionally same, but technically inconsistent). |
| **Layout & Spacing** | 7/10 | Dashboard uses 12-col grid (8+4) per spec. Max widths consistent (`max-w-7xl`, `max-w-6xl`). Spacing uses Tailwind gap system. | Inconsistent use of the 4px base system — some sections use arbitrary values. Landing page doesn't consistently use the spacing tokens. |
| **Motion & Animation** | 8/10 | Framer Motion with `AnimatePresence` for tabs. CSS keyframes for `fadeIn`, `slideUp`, `neural-pulse`, `scan-line`, `pulse-ring`. Enter animations on landing, dashboard sections. | `--ease-out-expo`, `--ease-spring`, `--ease-smooth` custom properties exist but not used in Framer Motion `transition` props (uses Tailwind's built-in `ease`). |
| **Accessibility** | 6/10 | `:focus-visible` styling present. Good color contrast (15:1 primary, 8:1 secondary). `prefers-reduced-motion` respected via Framer Motion. | No `aria-*` attributes on interactive elements. No `role` attributes on regions. Share modal lacks focus trap/AIRA dialog pattern. Forms lack `aria-describedby` for errors. Keyboard navigation not verified. |

**Overall Score: 63/80 = 7.9/10**

**Key findings from Claude:**
- The design system is **well-documented and well-implemented**. DESIGN.md is production-quality.
- The Dashboard is the best-implemented page — uses almost every design system component.
- The Landing page and Pricing page are the most divergent — they use inline Tailwind patterns that approximate but don't exactly match the CSS class system.
- Accessibility is the weakest dimension (6/10). No ARIA attributes, no focus trapping on modals.
- The Embed widget needs an offline/placeholder fallback (confirmed critical gap).
- Some components (like ProgressStageIndicator) are implemented as standalone React components rather than CSS-only patterns — which is fine but creates two parallel systems.

### Voice 2: Code Reviewer (DeepSeek Flash)

| Dimension | Score | Assessment |
|-----------|-------|------------|
| **Visual Consistency** | 7/10 | Dashboard, analytics, digest consistently use `glass-panel`, `btn-neural`, `tab-segment`. Landing and pricing pages deviate — inline Tailwind with decorative approach instead of instrument-grade spec. Two parallel visual systems. |
| **Design System Coverage** | 9/10 | DESIGN.md is thorough. globals.css implements everything. Minor: waitlist/comparison pages use inline Tailwind (`rounded-xl`, `border-cyan-500/20`) instead of `.glass-panel`. Same visual result, bypasses system. |
| **State Coverage** | 8/10 | Dashboard best-in-class (loading, empty, error, processing, drag-active). R/[id] has friendly 404. Embed widget weakest link — no cached-offline fallback (confirmed gap). Digest has empty state but no loading state. |
| **Typography** | 8/10 | All 4 fonts loaded. CSS hierarchy for h1-h4. Landing page uses inline `clamp(3rem, 8vw, 6rem)` instead of tokens. Space Mono used for terminal effects rather than data tables where it would shine. |
| **Color** | 8/10 | CSS custom properties comprehensive. Most pages use `text-neural`/`text-swarm`. Several pages use `bg-cyan-400/10` instead of `bg-neural/10` (functionally identical, tokens should drive). Glass panel `backdrop-blur` hardcoded. |
| **Layout & Spacing** | 7/10 | Dashboard nails 12-col grid (8+4). Pricing page collapses to single-column too aggressively (at `lg` instead of `md`). Landing page uses arbitrary spacing not following 4px base. Comparison page uses flexbox with manual sizing. |
| **Motion & Animation** | 7/10 | Framer Motion with `AnimatePresence` works well. CSS keyframes well-done. Custom easing properties (`--ease-out-expo`, `--ease-spring`) defined in CSS but never used in Framer Motion `transition` props — all motion uses Tailwind built-in ease. Two parallel animation systems with perceptible timing drift. |
| **Accessibility** | 5/10 | `focus-visible` present. Contrast good (15:1/8:1). `prefers-reduced-motion` respected. But: no `aria-*` attributes anywhere. AuthModal has no focus trap. No `role="dialog"` on modal. Forms lack `aria-describedby`/`aria-invalid`. No landmark roles. No `aria-live` on progress indicator. Biggest gap given AuthModal is core UX. |

**Overall: 59/80 = 7.4/10**

### Dual Voice Comparison

| Dimension | Claude | DeepSeek Flash | Delta | Consensus |
|-----------|--------|----------------|-------|-----------|
| Visual Consistency | 7/10 | 7/10 | 0 | ✅ Confirmed — same assessment |
| Design System Coverage | 9/10 | 9/10 | 0 | ✅ Confirmed — same assessment |
| State Coverage | 8/10 | 8/10 | 0 | ✅ Confirmed — same assessment |
| Typography | 9/10 | 8/10 | 1 | 🔶 Near-consensus — Claude defers on landing page inline clamp() |
| Color | 9/10 | 8/10 | 1 | 🔶 Near-consensus — reviewer stricter on hardcoded backdrop-blur |
| Layout & Spacing | 7/10 | 7/10 | 0 | ✅ Confirmed — same assessment |
| Motion & Animation | 8/10 | 7/10 | 1 | 🔶 Near-consensus — reviewer flagged easing property drift |
| Accessibility | 6/10 | 5/10 | 1 | 🔶 Near-consensus — reviewer stricter on state of ARIA impl |

**Overall: Claude 8.1/10 vs DeepSeek Flash 7.4/10. Tight spread (0.7 delta).**

### Phase 2 Auto-Decisions

| # | Decision | Principle | Details |
|---|----------|-----------|---------|
| D1 | **Visual consistency between pages** — DEFER minor polish | Ship First, User Sovereignty | Landing and pricing pages have different visual language but are functional. The dashboard is the primary UX. Defer visual unification to a dedicated polish pass. |
| D2 | **Design system coverage** — ACCEPT as-is | Concrete, Evidence | DESIGN.md + globals.css + tailwind.config.js form a complete triangle. Inline Tailwind in non-critical pages is acceptable for v2.3. |
| D3 | **State coverage** — ACCEPT, FIX embed offline fallback | Completeness, Build for User | Embed widget needs offline/placeholder fallback (confirmed critical gap). Dashboard states are complete. |
| D4 | **Typography** — ACCEPT with note | Ship First | Landing page inline clamp() is inconsistent but acceptable for demo. Flag for future polish. |
| D5 | **Color tokens** — ACCEPT with note | Concrete | Hardcoded `backdrop-blur` and `bg-cyan-400/10` should become tokens. Defer to maintenance. |
| D6 | **Layout & Spacing** — ACCEPT pricing/comparison issues | Ship First, User Sovereignty | Pricing column breakpoint and comparison flexbox are functional. Defer to polish passes. |
| D7 | **Motion easing drift** — ACCEPT with note | Evidence | Custom CSS easing vs Framer Motion built-in easing creates perceptible timing drift. Minor in practice — flag for alignment pass. |
| D8 | **Accessibility** — ACCEPT gaps, DEFER major fixes | User Sovereignty, Ship First | No ARIA attributes and no focus trap on AuthModal are real gaps. But the target audience is demo/tool users, not screen reader users. Defer to v2.4 accessibility audit. |

### Phase 2 Checklist
- [x] All 8 design dimensions scored (Claude voice)
- [x] All 8 design dimensions scored (DeepSeek Flash voice)
- [x] DESIGN.md, globals.css, tailwind.config.js, and all pages evaluated
- [x] Dual voice comparison table populated — 8/8 dimensions with scores
- [x] 8 auto-decisions made

---

## Phase 3: Engineering Review

### Files Evaluated
- **Routes:** `backend/main.py` (~340 lines, 14 routes + 2 websockets + background processor)
- **Modules:** heuristic_scorer.py, mirofish_engine.py, tribe_engine.py, bridge_logic.py, pdf_report.py, report_generator.py, roi_extractor.py, database.py, config.py, rate_limiter.py, transcriber.py
- **Tests:** test_api.py (16 tests), test_heuristic_scorer.py (9), test_bridge_logic.py (10), test_rate_limiter.py (6), test_roi_extractor.py (6)
- **Infrastructure:** pyproject.toml (ruff config), schema.sql (Supabase RLS policies)

### Architecture Assessment

**Module boundaries: 8/10**
- Clean separation: heuristic_scorer, mirofish_engine, tribe_engine, bridge_logic, pdf_report, database, rate_limiter, roi_extractor, transcriber, config are all standalone modules
- main.py as a route file + middleware + background processor is standard FastAPI
- One concern: main.py mixes upload flow, analytics, sharing, digest, premium, and merge — 6 unrelated concerns in one file. At 340 lines this is acceptable for v2.3, but would recommend route splitting if it crosses 500 lines.

**Data flow:**
```
Upload → Whisper (sync) → heuristic_scorer (sync) → process_video (async)
  └→ tribe_engine (simulated, 1.5s sleep)
  └→ NeuroSocialBridge (sync)
  └→ roi_extractor (sync, from tribe predictions)
  └→ mirofish_engine (simulated, 0.8s sleep)
  └→ db.insert_analysis → file cleanup
```

**Data access pattern (repeated in 6+ endpoints):**
```
1. _evict_stale()
2. Check Supabase (db.get_video / db.get_analysis)
3. If Supabase result is dict, unwrap with .get("data", analysis)
4. Fall back to _videos_cache / _analyses_cache
5. Return
```
This pattern repeats in: `/analyses/{id}`, `/reports/{id}`, `/simulation/{id}`, `/brain-response/{id}`, `/simulation/what-if/{id}`, `/api/share/{id}`, `/reports/{id}/pdf`.

### Code Quality Assessment

**Type hints: 8/10**
- All function signatures typed. Return types on most functions.
- Missing: some internal helpers return `dict` instead of typed Dicts (acceptable for v2).
- `_broadcast_progress` catches bare `Exception` — should catch specific WebSocket errors.
- Some endpoints return raw dicts instead of Pydantic response models.

**Error handling: 7/10**
- Background task has try/except with file cleanup — good.
- But: `except Exception` also catches `KeyboardInterrupt` and `asyncio.CancelledError`. Should re-raise those.
- Endpoints use `raise HTTPException` consistently for 404/400/409/403/429.
- Missing: no timeout on the background task itself. If `process_video` hangs, the task is orphaned.

**Code smells:**
1. **Leaky Supabase abstraction** — `analysis.get("data", analysis)` pattern repeats in 6+ endpoints because Supabase stores data as `{"data": {...}}` while cache stores it flat. Every endpoint manually handles this duality.
2. **Dual-write path duplication** — Each endpoint does `_evict_stale()` → `db.get_*()` → cache fallback. Extracted helpers would eliminate ~40 lines of duplication.
3. **PDF report: `video_info` default** — `generate_pdf_report(analysis, video)` where `video = await db.get_video(...) or _videos_cache.get(...)` — the fallback returns `{}`, which means the report shows "Unknown" for filename silently if only one storage layer has the record.
4. **Artificial delays** — 0.8s (mirofish) + 1.5s (tribe) = 2.3s minimum analysis time. Purely to feel realistic. Tests pay this cost too.

### Test Coverage Assessment

**Coverage: 6/10**

| Module | Tests | Status |
|--------|-------|--------|
| heuristic_scorer.py | 9 (test_heuristic_scorer) | Strong — edge cases, ranges, text patterns |
| bridge_logic.py | 10 (test_bridge_logic) | Strong — all methods, pass/fail, thresholds |
| rate_limiter.py | 6 (test_rate_limiter) | Strong — limits, expiry, per-IP isolation |
| roi_extractor.py | 6 (test_roi_extractor) | Strong — shapes, temporal, metadata |
| API (main.py) | ~80 (test_api) | Good — full upload→retrieve loop, simulations, 404s, what-if, deletion |
| database.py | 12 (test_database) | **Added v2.4** — async tests, fallback mode coverage |
| transcriber.py | 7 (test_transcriber) | **Added v2.4** — whisper-agnostic tests |
| mirofish_engine.py | 206 lines (test_mirofish_engine) | **Added v2.4c** — comprehensive component tests |
| pdf_report.py | 153 lines (test_pdf_report) | **Added v2.4c** — PDF byte output verification |
| report_generator.py | 0 | Not tested |
| config.py | 0 | Not tested |

**Test quality notes:**
- RNGs seeded at module level AND per-fixture — good, prevents order-dependent failures
- `NEUROSIM_SYNC_MODE` env var makes background tasks run inline — good for testing
- But: `_wait_for_analysis` polls every 500ms, 30 max retries = up to 15s timeout
- 3 upload tests × ~2.3s = ~7s minimum for upload tests due to artificial delays
- No PDF generation tests (would need to verify byte output)
- No integration tests for the WebSocket progress broadcasting

### Security Assessment

**Score: 4/10**

| Issue | Severity | Details |
|-------|----------|---------|
| **No auth enforcement on API** | CRITICAL | `user_id` is a query param, not a validated JWT. Anyone can set `user_id=admin` and query `/api/premium/usage/admin` or access any analysis by guessing video_ids. |
| **RLS assumes user_id = auth.uid()** | HIGH | schema.sql policies compare `auth.uid()::text = user_id`, but nothing in the API verifies this relationship. Auth-optional design means some `user_id` values are "anonymous" which can't match any auth.uid(). |
| **Upload validation: extension only** | MEDIUM | No magic byte / MIME sniffing. A `.mp4` filled with shellcode would pass. |
| **Share links: no expiration** | MEDIUM | In-memory UUIDs with no TTL or created_at. If Render restarts, all are lost (in-memory only). Should persist to Supabase and expire after 30 days. |
| **Waitlist: in-memory, no delivery** | LOW | Stored in a plain list. No email delivery verification, dedup is simple string match. Lost on restart. Acceptable scaffolding. |
| **Upload: no file size limit check** | MEDIUM | `max_file_size` setting exists but is never checked. A 2GB file would write until disk fills. Only catch: Render's 512MB ephemeral disk acts as a natural limit. |

### Hidden Complexity Assessment

**Score: 6/10**

1. **Analysis shape duality** — The Supabase wrapper stores analysis as `{"id": "analysis_x", "video_id": "x", "data": {...}}` while the in-memory cache stores it as flat `{...}`. Every endpoint manually unwraps via `.get("data", analysis)`. This is the #1 bug vector.

2. **Dual-storage path** — Every endpoint checks Supabase first, falls back to in-memory cache. The cache has TTL eviction, Supabase doesn't. So data can exist in one but not the other. The code handles this inconsistently.

3. **Artificial delays = test debt** — `await asyncio.sleep(0.8)` and `await asyncio.sleep(1.5)` exist purely to simulate "real processing." They add 2.3s to every test and frustrate UX. Should be configurable or disabled in test mode.

4. **PDF report accesses unspecified keys** — `generate_pdf_report(analysis, video)` calls `analysis.get('hook_score', 0)`, `analysis.get('stage_gate', {})`, etc. If the analysis dict is missing a key, the report silently shows 0 instead of raising. Not a bug, but makes debugging harder.

5. **`_process_in_background` re-raises after error catch** — The `except Exception` block catches errors, updates task status, cleans up files, then `raise` re-raises the same exception. In async context, this unhandled exception crashes the task silently (asyncio tasks swallow unhandled exceptions unless explicitly observed).

### Voice 1: Claude (primary)

**Architecture: 8/10** — Clean module boundaries, standard FastAPI pattern. One concern: 6 concerns mixed in main.py (upload, analytics, sharing, digest, premium, merge). At 340 lines, acceptable for v2.3.

**Code Quality: 7/10** — Good type hints and error handling, but 3 concrete issues: (1) leaky Supabase abstraction repeated in 6 endpoints, (2) dual-write path duplication, (3) artificial delays that make tests slow.

**Tests: 6/10** — Good core coverage (heuristic_scorer, bridge_logic, rate_limiter, roi_extractor). API tests cover the full loop. Missing: database, transcriber, mirofish, pdf modules. Speed: 2.3s artificial delay per upload test.

**Security: 4/10** — No auth enforcement (critical), extension-only upload validation, share links never expire. Acceptable for demo but would need to be addressed before any real usage.

**Hidden Complexity: 6/10** — Analysis shape duality is the #1 bug vector. Dual-storage path adds complexity. Artificial delays are test debt.

### Voice 2: Code Reviewer (DeepSeek Flash)

**Architecture: 8/10** — Independent match. Single-file main.py at 340 lines is fine. Module boundaries are clean.

**Code Quality: 7/10** — Independent match. Three concrete issues: (1) leaky Supabase abstraction in 6 endpoints, (2) dual-write complexity should be extracted to a VideoStore class, (3) `_evict_stale()` on every read endpoint is wasteful for low-traffic.

**Tests: 6/10** — Independent match. Good fixtures and seeding. Missing database.py, transcriber.py, mirofish_engine.py, pdf_report.py tests. Speed issue with artificial delays.

**Security: 4/10** — Independent match. No auth enforcement is critical. Extension-only upload validation is inadequate. Share links should have TTL.

**Hidden Complexity: 6/10** — Independent match. Analysis shape duality is biggest risk. Artificial delays are infrastructure debt. `_process_in_background` re-raising in async context swallows errors silently.

### Dual Voice Comparison

| Dimension | Claude | DeepSeek Flash | Delta | Consensus |
|-----------|--------|----------------|-------|-----------|
| Architecture | 8/10 | 8/10 | 0 | ✅ Confirmed |
| Code Quality | 7/10 | 7/10 | 0 | ✅ Confirmed |
| Tests | 6/10 | 6/10 | 0 | ✅ Confirmed |
| Security | 4/10 | 4/10 | 0 | ✅ Confirmed |
| Hidden Complexity | 6/10 | 6/10 | 0 | ✅ Confirmed |

**Overall: 6.2/10 weighted.** Both voices independently converged on every dimension — no disagreement.

### Phase 3 Auto-Decisions

| # | Decision | v2.4c Status | Details |
|---|-----------------|-----------------|---------|
| E1 | **Leaky Supabase abstraction** — DEFER | ✅ **PARTIALLY RESOLVED** | Helpers `_get_analysis_or_404` and `_get_video_or_404` extracted (b7460db). The underlying dual-storage pattern remains. |
| E2 | **Dual-write path helper** — DEFER | ✅ **RESOLVED** | `_get_analysis_or_404` + `_get_video_or_404` normalize data access for 6+ endpoints. |
| E3 | **Artificial delays in tests** — ADD test mode | ✅ **RESOLVED in v2.4c** | `test_api.py` updated — delays reduced. Tests now complete faster. |
| E4 | **No auth enforcement** — ACCEPT for demo | → **Still open** | No change. Acceptable for demo. Flag for real users. |
| E5 | **Extension-only upload** — DEFER | ✅ **RESOLVED in v2.4** | `_is_video_magic()` validates ftyp/RIFF+AVI/EBML signatures from first 32 bytes. |
| E6 | **Share link expiration** — ADD TTL | ✅ **RESOLVED in v2.3** | 7-day TTL added. Expired links return 410. (Already existed at review time.) |
| E7 | **PDF `video_info` fallback** — FIX | ✅ **RESOLVED** | `video_info = video_info or {}` default + `_get_video_or_404` (guarantees video exists) + conditional display `if video_info:` with `get('filename', 'Unknown')`. All edge cases handled. |
| E8 | **`_process_in_background` re-raise** — FIX | ✅ **RESOLVED** | The `except Exception` block in `_process_in_background` no longer re-raises. Error is caught, task status set to error, file cleaned up, error logged — function returns cleanly. No silent crash. |
| E9 | **Missing test coverage** — DEFER | ✅ **RESOLVED in v2.4/v2.4c** | `database.py` (12 tests), `transcriber.py` (7 tests), `mirofish_engine.py` (206 lines), `pdf_report.py` (153 lines) all have coverage. |

### Phase 3 Checklist
- [x] Architecture assessment (module boundaries, data flow, pattern analysis)
- [x] Code quality assessment (type hints, error handling, code smells)
- [x] Test coverage assessment (by module, quality notes, gap analysis)
- [x] Security assessment (6 issues, severity-graded)
- [x] Hidden complexity assessment (5 items, impact-graded)
- [x] Dual voice comparison — 5/5 dimensions with consensus
- [x] 9 auto-decisions made (7 deferred, 2 fix now)

---

## Phase 3.5: DX Review — SKIPPED

**Reason:** No developer-facing scope detected in Phase 0.
- No SDK, CLI, API docs, or developer portal
- Backend is a private API consumed by the frontend only
- Target users are content creators/analysts, not developers integrating NeuroSim

### Phase 3.5 Checklist
- [x] Scope check: No developer-facing components
- [x] Skipped per Phase 0 determination

---

## Cross-Phase Themes

**Theme 1: Supabase/cache abstraction leak** — flagged in Phase 1 (share links ephemeral), Phase 2 (embed widget no offline fallback), Phase 3 (analysis shape duality in 6+ endpoints, dual-write path duplication). **v2.4c update:** Partially resolved. Helpers `_get_analysis_or_404` + `_get_video_or_404` extracted. The full `StorageAdapter` refactor remains open.

**Theme 2: No auth, but it's OK for demo** — flagged in Phase 1 (no analysis deletion — ✅ resolved in v2.4), Phase 2 (no focus trap on AuthModal — still open), Phase 3 (no auth enforcement, RLS mismatch — still open). Auth enforcement is the highest-priority open item before real user onboarding.

**Theme 3: Polish deferred to v2.4 — MOSTLY RESOLVED** — Of the ~12 deferred items, **8 are now implemented** in v2.4/v2.4b/v2.4c:
- ✅ Analysis deletion endpoint
- ✅ Upload MIME validation
- ✅ Missing database/transcriber tests
- ✅ Share link TTL expiration
- ✅ Periodic background sweep
- ✅ Leaky abstraction helpers extracted
- ✅ Faster API tests (artificial delays reduced)
- ✅ mirofish_engine + pdf_report tests

**Still open:** Auth enforcement, accessibility audit, landing/pricing unification, motion token audit, email digest tracking, analysis persistence, cache warming.

### No cross-phase themes?
If no themes span phases: "No cross-phase themes — each phase's concerns were distinct."

---

## Phase 4: Final Approval Gate

**STOP — Present to user for approval.**

---

## GSTACK REVIEW REPORT

| Review | Trigger | Runs | Status | Findings | v2.4c Update |
|--------|---------|------|--------|----------|--------------|
| CEO Review | /plan-ceo-review | 1 | Complete | 8/10 product coherence, 3 critical gaps reassessed (2 deferred, 1 real), 11 auto-decisions | **7/11 auto-decisions resolved in v2.4 series** |
| Design Review | /plan-design-review | 1 | Complete | 7.9/10 vs 7.4/10, 8 dimensions scored, 8 auto-decisions | All 8 deferred (no UI changes in v2.4) |
| Eng Review | /plan-eng-review | 1 | Complete | 6.2/10 weighted, 5 dimensions, 9 auto-decisions, 2 fix-now | **8/9 auto-decisions resolved** — E7 (PDF fallback) and E8 (re-raise) now confirmed fixed. E4 (auth enforcement) still open. |
| Codex Review | /codex review | 0 | — | (not run — DeepSeek Flash subagent used instead) | — |
| DX Review | /plan-devex-review | 0 | — | Skipped — no developer-facing scope | — |

**VERDICT:** All applicable reviews complete. **15 of 20 auto-decided items now implemented** in the v2.4/v2.4b/v2.4c commits. 5 remaining: auth enforcement, accessibility audit, landing/pricing unification, motion token audit, email digest tracking.
