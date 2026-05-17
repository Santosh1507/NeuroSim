# Deployment Plan: MiroFish-Offline to Vercel + Render

## Overview
Deploy MiroFish-Offline (local-first fork) to cloud infrastructure: Vercel (frontend) + Render (backend) + Supabase (DB) + Neo4j Aura (graph).

## Current State
- Frontend Vercel config: `frontend/vercel.json` ✓
- Backend Render config: `backend/render.yaml` ✓
- Deployment guide: `CLAUDE.md` ✓ (updated: uvicorn start command)
- Environment templates: `backend/.env.example`, `frontend/.env.example` ✓

## Pre-Deployment Blocker (CRITICAL)
The existing Render service (`mirofish-backend.onrender.com`) is still connected to the OLD repo and serving Flask code. Before deploying:
1. Go to https://dashboard.render.com
2. Find the MiroFish backend service
3. Settings → "Connect new repository" → select `Santosh1507/MiroFish-Offline`
4. Root Directory: `backend`
5. Build command: `pip install -r requirements.txt`
6. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
7. Re-add all environment variables (see Phase 1)
8. Trigger manual deploy

## Problem Statement
The offline version runs locally with Neo4j + Ollama. The deployment requires cloud alternatives:
- Neo4j (local) → Neo4j Aura (cloud)
- Ollama (local) → OpenAI/Anthropic API (cloud)

## Scope

### Phase 1: Cloud Credentials Setup
- [ ] Create Neo4j Aura free tier instance
- [ ] Get OpenAI API key (or Anthropic)
- [ ] Copy `backend/.env.example` → `backend/.env` and fill in real values
- [ ] Copy `frontend/.env.example` → `frontend/.env` and fill in real values
- [ ] Add env vars to Render dashboard (all from `backend/.env.example`)
- [ ] Add env vars to Vercel dashboard (all from `frontend/.env.example`)

### Phase 2: Backend Deployment (Render)
- [ ] **Switch Render repo** (see Pre-Deployment Blocker above)
- [ ] Configure environment variables
- [ ] Deploy backend service
- [ ] Verify health endpoint: `curl https://mirofish-backend.onrender.com/health`
- [ ] Verify protected endpoint returns 401 without token

### Phase 3: Frontend Deployment (Vercel)
- [ ] Connect GitHub repo to Vercel
- [ ] Configure frontend env vars
- [ ] Deploy frontend
- [ ] Update `VITE_API_BASE_URL` to actual Render backend URL

### Phase 4: Post-Deploy Verification
- [ ] Test health endpoint returns `{"status":"ok"}`
- [ ] Verify database connectivity (run a small simulation)
- [ ] Test end-to-end flow from Vercel frontend → Render backend
- [ ] Verify Supabase auth flow (login/signup)
- [ ] Test CORS: frontend can reach backend without console errors

## Deploy Verification Checklist

Run these commands after both services are deployed:

```bash
# 1. Health check (should return 200 with {"status":"ok"})
curl -s -o /dev/null -w "%{http_code}" https://mirofish-backend.onrender.com/health

# 2. Auth check (should return 401 without token)
curl -s -o /dev/null -w "%{http_code}" https://mirofish-backend.onrender.com/api/protected

# 3. CORS check (open browser console on Vercel URL, no CORS errors)
#    Navigate to https://your-app.vercel.app and check DevTools Console

# 4. End-to-end test (run a simulation from the frontend)
#    Open https://your-app.vercel.app → start a simulation → verify results

# 5. Cold start test (first request after inactivity should complete within 60s)
time curl -s https://mirofish-backend.onrender.com/health
```

## Cold Start Warning
Render's free tier spins down after 15 minutes of inactivity. The first request after spin-down takes 30-50 seconds to complete. This is normal behavior, not a bug. Document this for users or consider a keep-alive ping service.

## Constraints
- Must use free tier where possible (Neo4j Aura free, Vercel hobby, Render free)
- Cannot exceed $0/month initially
- All services must be cloud-hosted (localhost URLs won't work on Render)

## Technical Details

### Backend (Render)
- Runtime: Python 3.11
- Server: uvicorn (FastAPI)
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Environment: Production (not debug)

### Frontend (Vercel)
- Framework: Vite + Vue
- Node: 22.x (`>=22.12.0`)
- Build: `npm run build` (outputs to dist/)
- Output directory: `frontend/dist`

### Environment Variables Required
**Backend:**
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY
- NEO4J_URI (neo4j+s://...)
- NEO4J_USER
- NEO4J_PASSWORD
- LLM_API_KEY
- LLM_BASE_URL
- LLM_MODEL_NAME
- FRONTEND_URL
- GROQ_API_KEY (optional, for NeuroSim video transcription)

**Frontend:**
- VITE_SUPABASE_URL
- VITE_SUPABASE_ANON_KEY
- VITE_API_BASE_URL (point to Render backend URL)

## Error & Rescue Paths

| Error | Detection | Rescue |
|---|---|---|
| Wrong Supabase creds | `/health` returns 500 | Check env vars, redeploy |
| Neo4j Aura unreachable | DB query timeout | Check network, verify URI format |
| LLM endpoint down | Simulation returns error | Fallback message, retry logic |
| Render build fails | Deploy log shows error | Check `requirements.txt`, Python version |
| Vercel build fails | Build log shows error | Check Node version, Vite config |
| CORS mismatch | Browser console errors | Update `FRONTEND_URL` in backend |
| Free tier cold start | First request takes 50s | Normal behavior, document it |
| Service role key leaked | Security scan | Rotate key immediately in Supabase dashboard |

## Alternatives Considered
1. **Keep local only** - Won't work, user wants cloud deployment
2. **Different cloud providers** - Render/Vercel are the standard for this stack
3. **Self-hosted alternative** - Fly.io, Railway considered but Render is simpler

## Open Questions
- Which LLM provider to use? (OpenAI vs Anthropic)
- What model size? (gpt-4o-mini for cost, or larger for quality)
- How to handle rate limits during simulation?

## Deferred (TODOS.md candidates)
- Staging environment setup
- Load testing before launch
- Error alerting (Sentry, Discord webhook)
- Auto-scaling config for Render
- Rate limiting for backend
