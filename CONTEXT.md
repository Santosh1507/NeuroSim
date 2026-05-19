# NeuroSim — Domain Glossary

## Product

**NeuroSim** — AI-powered video analysis platform that analyzes content scripts and transcripts before publishing. v2.2 uses heuristic transcript analysis + swarm simulation. Positioning: "analyze your script before you even film" — catch weak hooks, missing CTAs, and low-engagement language before production. No GPU required.

**Simulated Analysis** — The v2.0–v2.2 analysis mode. Uses audio transcription (Whisper tiny) + heuristic linguistic scoring to produce ROI-like predictions. Not real neural encoding. User-facing badge says "SIMULATED."

**Pro** — Premium tier at $29/mo. Delivers features on existing infra: bulk analysis, longer video uploads, priority processing, PDF reports, team seats, and advanced comparison tools. NOT real GPU-powered TRIBE v2 (deferred to future tier).

**Free Tier Limits** — 10 analyses/month. Rate limit: 3 uploads per 10 minutes. When monthly limit reached: explicit message "You've used all 10 free analyses this month. Upgrade to Pro for unlimited." Monthly usage resets on month change.

## Analysis Pipeline

**Script Analysis (primary flow)** — User pastes or uploads a text script. Instant heuristic scoring of 4 ROI dimensions + swarm simulation. No transcription needed. Matches positioning: "analyze your script before you even film."

**Video Analysis (secondary flow)** — User uploads a finished video. Audio transcribed via faster-whisper (tiny model), then transcript scored heuristically for 4 ROI dimensions, then passed through the MiroFish swarm simulator. Slower (transcription wait) but useful for post-production review.

**Transcript** — Text extracted from video audio via faster-whisper (video flow) OR pasted directly by user (script flow). Used as input for heuristic ROI scoring. If no audio detected, falls back to "No audio detected. Analysis based on file metadata only."

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

**TRIBE v2** — Meta's foundation model for in-silico neuroscience. The core USP and competitive moat. Requires GPU infra. NOT currently loaded — deferred to premium/future release (v4.0). Current heuristic pipeline should NOT be branded as "TRIBE" in the UI to avoid confusion. Real TRIBE v2 is the premium differentiator.

**MiroFish** — Swarm intelligence simulator. Runs 1000 agents through 20 rounds of sentiment evolution based on persona distributions (loyal_fan, skeptic, trend_seeker, etc.). Produces final_sentiment, viral_prediction, backlash_prediction, and persona_distribution. Used by both NeuroSim (cloud) and MiroFish-Offline (desktop).

**MiroFish-Offline** — Local-first desktop app running the heuristic analysis pipeline (Whisper tiny + heuristic scoring + swarm simulation) entirely on-device. Serves privacy-sensitive users (agencies, enterprises) who can't upload scripts to the cloud. Instant analysis — no cold starts, no upload wait. TRIBE v2 stays cloud-only (GPU requirement) — drives users back to NeuroSim for premium.

**NeuroSocialBridge** — Maps ROI scores to social propagation parameters: attention weight, skip probability, share probability, viral coefficient. The bridge between neural predictions and social behavior.

## User Concepts

**Guest Session** — Temporary unauthenticated user identified by `guest_<uuid>` in localStorage. Only permitted for upload → sign-up → merge flow. Guest videos are tagged `user_id = guest_session_id`. On sign-in/sign-up, guest videos are reassigned to the new user via `/api/merge`. Anonymous users cannot accumulate data indefinitely — must auth to continue.

**PDF Report** — Professional client deliverable. Agencies and freelancers generate it to share analysis results with clients. Includes all scores, recommendations, and branding. Designed for external sharing, not internal debugging. — Personalized tips based on user's weakest score from recent analyses (e.g., "Your hook score was 42 — try starting with a question next time"). Drives re-engagement. NOT weekly usage summaries or generic platform updates.

**Demo Mode** — Landing page preview only. Generates hardcoded analysis results so the UI can be demonstrated. Labeled with "DEMO" badge. Disabled for authenticated users — if backend is down, show error: "Server is unavailable. Your analysis will be processed when the server restarts." Never used for actual analysis flows or validation study data.

**Share Link** — UUID-based unlisted public URL (`/r/{share_id}`) for sharing analysis results. Link-only access — no public directory. 7-day TTL; expired links return 410. Not sequential IDs (prevents enumeration).

**Embed** — Minimal read-only analysis view at `/embed/{share_id}` designed for iframe embedding. Reuses share link infrastructure.

**Comparison** — Side-by-side view of user's analysis scores against platform benchmarks (e.g., "your hook score: 72 vs average: 58"). Answers "am I doing better or worse than other creators?" Not a comparison between two arbitrary videos.

**What-If Simulation** — Slider-based UI where users adjust individual ROI scores and see real-time changes to Success Probability, Hook Score, and Viral Potential. Most actionable feature: "here's what your content would look like if you fixed it."

## Deployment

**$0/mo Target** — All v2.2 features must run on free tiers: Vercel (frontend), Render 512MB RAM (backend), Supabase free (DB). No paid services.

**Render Free Tier** — 512MB RAM, ephemeral filesystem (~1GB), spins down after 15min inactivity. Cold starts take 30-50 seconds. Constraints drive key decisions: Whisper tiny model (75MB), heuristic scoring (no LLM), file cleanup after analysis, no Ollama. Warmup cron (`warmup_cron.py` every 5min) keeps cache warm post-start but doesn't prevent cold starts. Accept cold start tax at $0; upgrade to $7/mo tier (no spin-down) when paying users exist.

## Infrastructure

**Supabase** — Authentication + database + file storage. RLS policies enforce user-id-based access. Service key bypasses RLS (backend uses it for audit). Free tier: 500MB DB, 1GB file storage, 2GB bandwidth/month. Videos stored in Supabase Storage buckets for persistence across cold starts.

**HuggingFace Data Strategy** — FineVideo dataset (43,751 YouTube videos with transcripts + engagement metadata) used to calibrate heuristic weights against real engagement patterns. DistilBERT sentiment model (~66M params, CPU-friendly) replaces simple sentiment heuristic for improved Risk Score accuracy. Free, open-source, runs on Render 512MB.

**faster-whisper** — CTranslate2-compiled Whisper model. Tiny model (75MB) used for transcription. Loads lazily, unloads after transcription to stay within 512MB RAM.

**In-Memory Cache** — Fallback when Supabase is not configured. TTL-based eviction: videos expire after 1 hour, analyses after 30 minutes.

**Validation Study** — Lightweight correlation tracking between predicted scores and actual video performance. Beta users submit video URL + analysis ID. Public metrics (views, likes, comments) scraped after 7 days. Correlation computed and published transparently — even modest correlation (0.3-0.4) builds trust over inflated claims. Launch success metric: 20 users completing the full validation loop (submit analysis → return 7-day performance data).

## Roadmap

**v2.5** (current) — JWT auth, storage adapter, email digest, Stripe billing
**v3.0** — Script analyzer (text input), validation study launch, benchmark data collection
**v3.1** — What-if simulation UI, PDF report polish, comparison against benchmarks
**v4.0** — Real neural encoding (GPU) — only after validation study proves heuristic baseline has merit
