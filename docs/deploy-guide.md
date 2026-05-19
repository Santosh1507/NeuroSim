# Deploy NeuroSim v3.0 — Complete Setup Guide

## Prerequisites
- GitHub account with repo access
- Render account (connected to GitHub)
- Vercel account (connected to GitHub)
- Supabase project (optional but recommended)
- Stripe account (optional, for Pro tier)

## Step 1: Set GitHub Secrets (for Render auto-deploy)

Run these commands or set manually in GitHub repo Settings > Secrets and variables > Actions:

```powershell
# Render API key (get from https://dashboard.render.com/user/settings > API Keys)
gh secret set RENDER_API_KEY --body "rnd_..."

# Render service ID (get from Render dashboard > your service > Settings > Service ID)
gh secret set RENDER_SERVICE_ID --body "srv-..."
```

**Note:** Vercel auto-deploys on push when connected to GitHub — no secrets needed.

## Step 2: Connect Frontend to Vercel

1. Go to https://vercel.com/new
2. Import the NeuroSim repo
3. Set Root Directory to `frontend`
4. Framework Preset: Next.js
5. Deploy

Vercel will auto-deploy on every push to `master`.

## Step 3: Set Render Environment Variables

Go to Render dashboard > neurosim-api > Environment and add:

| Variable | Value | Notes |
|----------|-------|-------|
| `SUPABASE_URL` | `https://your-project.supabase.co` | From Supabase project settings |
| `SUPABASE_SERVICE_KEY` | `eyJ...` | From Supabase project settings > API > service_role |
| `SUPABASE_JWT_SECRET` | `your-jwt-secret` | From Supabase project settings > API > JWT Settings |
| `CORS_ORIGINS` | `["https://your-frontend.vercel.app"]` | Your Vercel frontend URL |
| `STRIPE_SECRET_KEY` | `sk_live_...` | Only when Pro launches |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...` | Only when Pro launches |

## Step 4: Run Database Migrations

After setting Supabase env vars, SSH into Render or run locally:

```bash
# Set env vars locally first
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_SERVICE_KEY="eyJ..."

# Run migrations
cd backend
python migrate.py
```

This creates: `videos`, `analyses`, `share_links` tables + RLS policies.

## Step 5: Verify Deploy

```bash
# Check backend health
curl https://neurosim-nm22.onrender.com/health

# Check metrics endpoint
curl https://neurosim-nm22.onrender.com/api/metrics

# Check frontend
curl https://your-frontend.vercel.app
```

## Step 6: Trigger Manual Deploy (if needed)

```powershell
# Trigger Render deploy
curl -X POST "https://api.render.com/v1/services/YOUR_SERVICE_ID/deploys" `
  -H "Authorization: Bearer YOUR_API_KEY" `
  -H "Content-Type: application/json"
```

## What Auto-Deploys on Every Push to Master

1. GitHub Actions runs all tests (backend + frontend)
2. If tests pass, triggers Render deploy (backend)
3. Vercel auto-deploys frontend on push (no CI job needed)

## Post-Deploy Checklist

- [ ] `/health` returns `{"status": "healthy"}`
- [ ] `/api/metrics` returns request counts
- [ ] Frontend loads without errors
- [ ] Upload flow works (test with a small video)
- [ ] Share links work
- [ ] Embed widget loads
- [ ] Stripe webhook configured (when Pro launches)
