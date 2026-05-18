# NeuroSim - Predictive Creative Intelligence Platform

AI-powered platform that predicts the performance, authenticity, emotional resonance, and social reception of creator-brand marketing content before launch.

## Architecture

```
Video Upload → TRIBE v2 (fMRI prediction) → ROI Extraction → Neuro-Social Bridge → MiroFish Swarm → Report
```

### TRIBE v2 Integration
- **Real Mode**: Loads `facebook/tribev2` from HuggingFace (requires GPU)
- **Simulated Mode**: Returns realistic mock predictions for local dev

### MiroFish Integration
- **Real Mode**: Calls self-hosted MiroFish API at `localhost:5001`
- **Simulated Mode**: Runs local swarm simulation with 1000 agents

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Configuration

### Enable Real TRIBE v2 (GPU Required)
```env
TRIBE_USE_REAL=true
HF_TOKEN=your_huggingface_token
```

### Enable Real MiroFish
1. Clone MiroFish: `git clone https://github.com/666ghj/MiroFish.git`
2. Configure MiroFish `.env` with LLM API key
3. Start MiroFish: `npm run dev` (runs on port 5001)
4. Set in NeuroSim backend:
```env
MIROFISH_USE_REAL=true
MIROFISH_API_URL=http://localhost:5001
```

## PRD Compliance
- ✅ NumPy pinned: `>=1.26.4,<2.1.0`
- ✅ Neuro-Social Bridge: `W_attn = 0.7×LO + 0.3×A5`
- ✅ Stage-Gate threshold: 0.4
- ✅ A/B Testing with 7-day propagation curve

## Tech Stack
- **Frontend**: Next.js 14, Tailwind, Framer Motion, Recharts
- **Backend**: FastAPI, Python
- **AI Models**: TRIBE v2 (Meta), MiroFish (Shanda/OASIS)
- **Deployment**: Netlify (frontend), Railway/Render (backend)
