# NeuroSim — Domain Glossary

## Product

**NeuroSim** — AI-powered video analysis platform that predicts content performance before publishing. v2.2 uses heuristic transcript analysis + swarm simulation. No GPU required.

**Simulated Analysis** — The v2.0–v2.2 analysis mode. Uses audio transcription (Whisper tiny) + heuristic linguistic scoring to produce ROI-like predictions. Not real neural encoding. User-facing badge says "SIMULATED."

**Pro (coming soon)** — Premium tier with real GPU-powered TRIBE v2 brain encoding. $29/mo. Not yet shippable.

## Analysis Pipeline

**Upload → Transcribe → Score → Analyze** — The v2.2 processing pipeline. Video is uploaded, audio is transcribed via faster-whisper (tiny model), transcript is scored heuristically for 4 ROI dimensions, then passed through the MiroFish swarm simulator.

**Transcript** — Text extracted from video audio via faster-whisper. Used as input for heuristic ROI scoring. If no audio detected, falls back to "No audio detected. Analysis based on file metadata only."

**Heuristic Scoring** — Pure linguistic analysis of transcript text (no LLM). Maps word patterns to 4 ROI dimensions using weighted sub-signals. Fully self-contained, $0/mo.

## ROI Dimensions

**A5 (Auditory Cortex)** — Measures audio engagement: speech pacing (sentence length variance), lexical diversity (unique word ratio), and rhythm (pause markers like ellipses, dashes). Fast + varied speech = high A5.

**LO (Lateral Occipital)** — Measures visual engagement proxy: visual/descriptive language count ("see", "look", "imagine", "bright", "vivid") and emotional word density. Vivid language = high LO.

**Area45 (Broca's Area)** — Measures CTA activation and persuasion: CTA keyword density ("subscribe", "click", "buy", "join") and imperative sentence ratio. Strong calls-to-action = high Area45.

**TPJ (Temporoparietal Junction)** — Measures social cognition and curiosity: question density (curiosity gaps), social pronoun ratio ("we", "together", "community"), and emotional word frequency. Social/emotional content = high TPJ.

## Derived Metrics

**Hook Score** — Composite: `(LO × 0.6 + A5 × 0.4) × 100`. Measures how well content captures attention in the first moments.

**Authenticity Score** — Composite: `(TPJ × 0.5 + (1 − Area45) × 0.5) × 100`. Measures perceived genuineness. High Area45 (strong CTA) reduces authenticity.

**Viral Potential** — Derived from social simulation: `viral_coefficient × 30`. Predicts content spread likelihood.

**Success Probability** — Composite: `(LO × 0.3 + A5 × 0.2 + Area45 × 0.3 + TPJ × 0.2) × 100`. Overall content performance prediction.

**Risk Score** — Composite: `(1 − TPJ) × 50 + sentiment × 0.2`. Predicts backlash/controversy likelihood.

## Stage-Gate

**Stage-Gate** — A pass/fail check on `W_attn` against a threshold (default 0.4). Determines whether content quality is sufficient to proceed to social simulation.

**W_attn** — Attention weight computed from ROI scores: `W = 0.7 × LO + 0.3 × A5`. The core stage-gate metric.

**Stage-Gate PASS** — `W_attn >= 0.4`. Content has sufficient attention weight to warrant social simulation.

**Stage-Gate FAIL** — `W_attn < 0.4`. Content is predicted to underperform; social simulation is skipped.

## Engines

**TRIBE v2** — Meta's foundation model for in-silico neuroscience. In v2.2, TRIBE v2 is NOT loaded. The "TRIBE" label in the UI refers to the heuristic scoring pipeline that produces ROI-like predictions. Real TRIBE v2 requires GPU and is deferred to Pro.

**MiroFish** — Swarm intelligence simulator. Runs 1000 agents through 20 rounds of sentiment evolution based on persona distributions (loyal_fan, skeptic, trend_seeker, etc.). Produces final_sentiment, viral_prediction, backlash_prediction, and persona_distribution.

**NeuroSocialBridge** — Maps ROI scores to social propagation parameters: attention weight, skip probability, share probability, viral coefficient. The bridge between neural predictions and social behavior.

## User Concepts

**Guest Session** — Unauthenticated user identified by `guest_<uuid>` stored in localStorage. Videos uploaded by guests are tagged `user_id = guest_session_id`. On sign-in/sign-up, guest videos are reassigned to the new user via `/api/merge`.

**Demo Mode** — Fallback when backend is unreachable. Generates hardcoded analysis results so the UI remains functional. Labeled with "DEMO" badge.

**Share Link** — UUID-based public URL (`/r/{share_id}`) for sharing analysis results. Not sequential IDs (prevents enumeration).

**Embed** — Minimal read-only analysis view at `/embed/{share_id}` designed for iframe embedding. Reuses share link infrastructure.

## Deployment

**$0/mo Target** — All v2.2 features must run on free tiers: Vercel (frontend), Render 512MB RAM (backend), Supabase free (DB). No paid services.

**Render Free Tier** — 512MB RAM, ephemeral filesystem (~1GB). Constraints drive key decisions: Whisper tiny model (75MB), heuristic scoring (no LLM), file cleanup after analysis, no Ollama.

## Infrastructure

**Supabase** — Authentication + database. RLS policies enforce user-id-based access. Service key bypasses RLS (backend uses it for audit).

**faster-whisper** — CTranslate2-compiled Whisper model. Tiny model (75MB) used for transcription. Loads lazily, unloads after transcription to stay within 512MB RAM.

**In-Memory Cache** — Fallback when Supabase is not configured. TTL-based eviction: videos expire after 1 hour, analyses after 30 minutes.
