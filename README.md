# NeuroSim

AI-powered video content analysis using neural simulation. Predict audience engagement, optimize hooks, and simulate social feed performance before you publish.

**Live site:** [https://neurosimai.vercel.app](https://neurosimai.vercel.app)

## Features

- **Neural Encoding Analysis** — Simulates brain region responses (visual cortex, auditory cortex, language center, social cognition) to predict how viewers will react
- **Hook Scoring** — Measures curiosity gaps, attention grabbers, and retention probability
- **What-If Simulation** — Test modifications (tone, pacing, CTA, price mention) before publishing
- **Social Feed Simulator** — Predict scroll retention, VTR, and viral potential across TikTok, YouTube Shorts, and Reels
- **A/B Testing** — Compare script variants head-to-head with neural response scores
- **PDF Reports** — Export full analysis as a downloadable report

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js (TypeScript), Tailwind CSS, Framer Motion, Three.js |
| Backend | FastAPI (Python), Supabase, Gemini 2.5 Flash |
| Neural Engine | facebook/tribev2 (transformers), MiFish ROI extraction |
| Hosting | Vercel (frontend), Render (backend), Supabase (DB) |

## Local Development

### Backend

```bash
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -v --tb=short   # run tests
uvicorn main:app --reload --port 8001
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # starts on localhost:3000
```

Set `NEXT_PUBLIC_API_URL=http://localhost:8001` for local backend.

## Tests

```bash
# Backend (303 tests)
cd backend && python -m pytest -v --tb=short

# Frontend (133 tests)
cd frontend && npx vitest run
```
