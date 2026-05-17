# Deployment Plan: MiroFish-Offline to Vercel + Render

## Overview
Deploy MiroFish-Offline (local-first fork) to cloud infrastructure: Vercel (frontend) + Render (backend) + Supabase (DB) + Neo4j Aura (graph).

## Current State
- Frontend Vercel config: `frontend/vercel.json` ✓
- Backend Render config: `backend/render.yaml` ✓
- Deployment guide: `CLAUDE.md` ✓

## Problem Statement
The offline version runs locally with Neo4j + Ollama. The deployment requires cloud alternatives:
- Neo4j (local) → Neo4j Aura (cloud)
- Ollama (local) → OpenAI/Anthropic API (cloud)

## Scope

### Phase 1: Cloud Credentials Setup
- [ ] Create Neo4j Aura free tier instance
- [ ] Get OpenAI API key (or Anthropic)
- [ ] Update CLAUDE.md with real credentials

### Phase 2: Backend Deployment (Render)
- [ ] Connect GitHub repo to Render
- [ ] Configure environment variables
- [ ] Deploy backend service
- [ ] Verify health endpoint

### Phase 3: Frontend Deployment (Vercel)
- [ ] Connect GitHub repo to Vercel
- [ ] Configure frontend env vars
- [ ] Deploy frontend
- [ ] Update VITE_API_BASE_URL

### Phase 4: Post-Deploy
- [ ] Test health endpoint
- [ ] Verify database connectivity
- [ ] Run a small simulation test

## Constraints
- Must use free tier where possible (Neo4j Aura free, Vercel hobby, Render free)
- Cannot exceed $0/month initially
- All services must be cloud-hosted (localhost URLs won't work on Render)

## Technical Details

### Backend (Render)
- Runtime: Python 3.11
- Server: gunicorn (not Flask dev server)
- Start command: `uv run gunicorn -w 1 --threads 8 -b 0.0.0.0:$PORT "app:create_app()"`
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
- VITE_API_BASE_URL

## Alternatives Considered
1. **Keep local only** - Won't work, user wants cloud deployment
2. **Different cloud providers** - Render/Vercel are the standard for this stack
3. **Self-hosted alternative** - Fly.io, Railway considered but Render is simpler

## Issues Identified (Auto-Resolved)

### Critical: render.yaml Missing Environment Variables
The backend requires these env vars for production deployment. Add to render.yaml:

```yaml
envVars:
  - key: FLASK_ENV
    value: production
  - key: SUPABASE_URL
    value: https://[project].supabase.co
  - key: SUPABASE_SERVICE_ROLE_KEY
    value: [your-key]
  - key: NEO4J_URI
    value: neo4j+s://[instance].neo4j.io
  - key: NEO4J_USER
    value: neo4j
  - key: NEO4J_PASSWORD
    value: [your-password]
  - key: LLM_API_KEY
    value: [your-api-key]
  - key: LLM_BASE_URL
    value: https://api.openai.com/v1
  - key: LLM_MODEL_NAME
    value: gpt-4o-mini
  - key: FRONTEND_URL
    value: https://[your-vercel-app].vercel.app
  - key: GROQ_API_KEY
    value: [optional-groq-api-key]
```

### Frontend: vercel.json needs env vars
Configure these in Vercel dashboard:
- VITE_SUPABASE_URL
- VITE_SUPABASE_ANON_KEY
- VITE_API_BASE_URL (point to Render backend URL)

## Open Questions
- Which LLM provider to use? (OpenAI vs Anthropic)
- What model size? (gpt-4o-mini for cost, or larger for quality)
- How to handle rate limits during simulation?
