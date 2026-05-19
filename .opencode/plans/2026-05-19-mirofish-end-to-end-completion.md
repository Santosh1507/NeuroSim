# MiroFish End-to-End Completion Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete MiroFish/NeuroSim end-to-end — from ship blockers through strategic positioning — in 4 sequential phases.

**Architecture:** 4 phases: (1) Ship Blockers; (2) Pre-Revenue Hardening; (3) Growth Infrastructure; (4) Strategic.

**Tech Stack:** FastAPI, Python 3.11, Supabase, Stripe, Next.js 14, TypeScript, Vitest, GitHub Actions, Render.

---

## Phase Overview

| Phase | Focus | Tasks | Est. Effort | Ships |
|-------|-------|-------|-------------|-------|
| **1: Ship Blockers** | Tests + webhook + error states + email | T1-T6 | ~6 hours | v2.5 |
| **2: Pre-Revenue Hardening** | Onboarding + recovery + rate limiting + monitoring | T7-T12 | ~15 hours | v2.6 |
| **3: Growth Infrastructure** | Route splitting + embed offline + share perms + migrations + CI/CD | T13-T18 | ~18 hours | v3.0 |
| **4: Strategic** | Validation study + Pro path + moat + LLM comparison | T19-T22 | Study + code | Post-revenue |

---

## Phase 1: Ship Blockers (v2.5)

### T1: StorageAdapter Tests — 22 tests covering all 12 methods
- Create: `backend/test_storage_adapter.py`
- Modify: `backend/storage_adapter.py` (add `_reset()` for testing)
- See: `.opencode/plans/phase1-tasks.md` for full test code

### T2: JWT Auth Tests — 10 tests covering valid/expired/invalid/dev modes
- Create: `backend/test_jwt_auth.py`
- Modify: `backend/main.py` (add `_set_jwt_secret_for_test()`)
- See: `.opencode/plans/phase1-tasks.md` for full test code

### T3: Stripe Webhook Handler + Tests — 4 tests
- Verify: `POST /api/stripe/webhook` in `backend/main.py`
- Create: `backend/test_stripe_webhook.py`

### T4: User-Friendly Error States
- Modify: `backend/main.py` (add `_user_error()` helper, fix background error handler)
- Modify: `frontend/src/app/dashboard/page.tsx` (add retry button to error state)

### T5: Email Digest End-to-End Tests — 4 tests
- Create: `backend/test_email_digest.py`

### T6: Full Test Suite Verification
- Expected: 93+ backend tests, 16 frontend tests — ALL PASS

---

## Phase 2: Pre-Revenue Hardening (v2.6)

### T7: Onboarding Flow
- Create: `frontend/src/app/components/OnboardingTour.tsx`
- Modify: `frontend/src/app/dashboard/page.tsx` (integrate onboarding)

### T8: Guest Session Recovery
- Modify: `frontend/src/lib/auth-context.tsx` (add `recoverGuestSession()`)
- Modify: `frontend/src/app/dashboard/page.tsx` (show recovery banner)

### T9: Rate Limiting (Production-Ready)
- Modify: `backend/rate_limiter.py` (add `reset()`, `check_api_limit()`)
- Modify: `backend/main.py` (apply to high-traffic endpoints)
- Create: `backend/test_rate_limiting_extended.py`

### T10: Monitoring & Observability
- Create: `backend/monitoring.py` (MetricsCollector)
- Modify: `backend/main.py` (add monitoring middleware, `/api/metrics` endpoint)
- Create: `frontend/src/lib/error-reporter.ts`

### T11: PDF Report End-to-End Verification
- Modify: `backend/test_api.py` (add PDF download test)

### T12: Full Test Suite Verification
- Expected: 100+ backend tests, 16 frontend tests — ALL PASS

---

## Phase 3: Growth Infrastructure (v3.0)

### T13: main.py Route Splitting
- Create: `backend/routes/__init__.py`, `upload.py`, `analysis.py`, `share.py`, `premium.py`, `digest.py`
- Modify: `backend/main.py` (include routers)
- Verify: All existing tests pass unchanged

### T14: Embed Widget Offline Fallback
- Modify: `frontend/src/app/embed/[id]/page.tsx` (add 5s timeout, offline state, retry button)

### T15: Share Link Permissions
- Modify: `backend/main.py` (add `ShareRequest` model with `allow_download`, `allow_embed`, `expires_in_days`)
- Create: `backend/test_share_permissions.py`

### T16: Database Migrations
- Create: `backend/migrations/001_initial_schema.sql`, `002_add_share_links.sql`
- Create: `backend/migrate.py` (migration runner)

### T17: CI/CD Auto-Deploy
- Modify: `.github/workflows/ci.yml` (add deploy jobs for Render + Netlify)

### T18: Full Test Suite Verification
- Expected: 110+ backend tests, 16 frontend tests — ALL PASS

---

## Phase 4: Strategic (Post-Revenue)

### T19: Prediction Accuracy Validation Study
- Create: `docs/validation-study.md` (hypothesis, method, success criteria)
- Create: `backend/correlation_tracker.py` (store predicted vs actual)

### T20: Pro Tier Technical Path
- Create: `docs/pro-tier-roadmap.md` (hybrid LLM approach recommended)
- Modify: Pricing page messaging (remove "coming soon" until concrete path)

### T21: Defensible Moat — Data Collection
- Create: `docs/data-moat-strategy.md`
- Modify: `frontend/src/app/dashboard/page.tsx` (add "How did this perform?" feedback)

### T22: LLM vs Heuristic Comparison
- Create: `backend/llm_scorer.py` (GPT-4o-mini scoring)
- Create: `backend/test_llm_comparison.py`

---

## Execution Order

1. **Phase 1** → Dispatch subagents for T1-T5 in parallel, then T6 verification
2. **Review checkpoint** → Full test suite, all must pass
3. **Phase 2** → Dispatch T7-T11 in parallel, then T12 verification
4. **Review checkpoint** → Full test suite, all must pass
5. **Phase 3** → Dispatch T13-T17 in parallel, then T18 verification
6. **Review checkpoint** → Full test suite, all must pass
7. **Phase 4** → Dispatch T19-T22 in parallel

**Total: ~40 hours across 4 phases.**
