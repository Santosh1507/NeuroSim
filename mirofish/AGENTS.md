# MiroFish Deployment Guide

## Overview
MiroFish deploys to Vercel for the Vue/Vite frontend and Render for the Flask backend. Production uses Supabase Auth, Neo4j Aura, and an OpenAI-compatible LLM endpoint.

## Deployment

### Frontend (Vercel)
- Auto-deploys on push to main.
- Framework: Vite.
- Node: 22.x, or any version `>=22.12.0`.
- Build command: `npm run build`.
- Output directory: `dist`.

### Backend (Render)
- Auto-deploys on push to main.
- Runtime: Python 3.11.
- Service type: Python, Gunicorn.
- Build command: `uv sync --frozen`.
- Start command: `uv run gunicorn -w 1 --threads 8 -b 0.0.0.0:$PORT "app:create_app()"`.
- FFmpeg is required for NeuroSim video processing.

## Environment Variables

### Frontend (Vercel)
```bash
VITE_SUPABASE_URL=https://[project].supabase.co
VITE_SUPABASE_ANON_KEY=[your-anon-key]
VITE_API_BASE_URL=https://mirofish-backend.onrender.com
```

### Backend (Render)
```bash
FLASK_ENV=production
FLASK_DEBUG=false
FRONTEND_URL=https://[your-vercel-app].vercel.app

SUPABASE_URL=https://[project].supabase.co
SUPABASE_SERVICE_ROLE_KEY=[your-service-role-key]

# Neo4j Aura
NEO4J_URI=neo4j+s://[instance].neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=[your-neo4j-password]

# OpenAI-compatible LLM endpoint
LLM_API_KEY=[your-api-key]
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o-mini

# Optional: NeuroSim video transcription via Groq Whisper
GROQ_API_KEY=[your-groq-api-key]
```

Compatibility aliases are supported for older deployment notes: `NEO4J_USERNAME` maps to `NEO4J_USER`, and `LLM_MODEL` maps to `LLM_MODEL_NAME`.

## Cloud Services Needed
1. Neo4j Aura: https://neo4j.com/cloud/aura/
2. Supabase Auth: https://supabase.com/
3. OpenAI-compatible LLM API.
4. Optional Groq API key for Whisper transcription.

## Deploy Commands (Manual)
```bash
# Frontend
cd frontend && vercel --prod

# Backend
cd backend && render deploy
```

## Post-Deploy
1. Set `VITE_API_BASE_URL` to the actual Render backend URL.
2. Set `FRONTEND_URL` to the actual Vercel frontend URL.
3. Test health endpoint: `https://mirofish-backend.onrender.com/health`.
4. Verify a protected API returns `401` without a bearer token.
