# Pro Tier Technical Roadmap

## Current State
- Heuristic scoring (lexicon-based, $0/video)
- Simulated TRIBE (random arrays)
- Simulated MiroFish (1000-agent swarm, no real LLM)

## Pro Tier Options

### Option 1: LLM-Enhanced Scoring
- Use Gemini 2.5 Flash to score transcripts
- Cost: ~$0.002/video (1000 tokens in, 50 out) with free tier available
- Pros: Easy to implement, immediate improvement over heuristic
- Cons: Still not "real neural encoding"

### Option 2: Real GPU Inference
- Modal.com, RunPod, or Replicate for GPU inference
- Cost: ~$0.05-0.20/video depending on model
- Pros: Real model predictions
- Cons: Complex infrastructure, higher cost

### Option 3: Hybrid (Recommended)
- Keep heuristic as base (fast, free, always works)
- Add LLM refinement for Pro users
- Cost: ~$0.002/video for LLM layer
- Pros: Best cost/quality ratio, incremental improvement
- Cons: Still not TRIBE v2

## Recommendation: Option 3 (Hybrid)

### Timeline
1. **Week 1**: Implement LLM scorer (`llm_scorer.py`)
2. **Week 2**: A/B test heuristic vs LLM on existing videos — publish comparison
3. **Week 3**: Verify Stripe billing + premium feature flag for Pro tier
4. **Week 4**: Launch Pro tier with "LLM-enhanced analysis"

### Messaging
- Current: "LLM-enhanced analysis with deeper content insights"
- Position as: "AI-powered scoring with deeper pattern recognition"
- Remove "TRIBE v2" from marketing until there's a concrete path to it

### Success Metrics
- Pro conversion rate > 5% of active users
- LLM scoring latency < 3s per analysis
- Cost per Pro user < $0.50/month at 200 analyses/month

## Implementation Status

- [x] Pricing page updated with LLM-enhanced messaging
- [x] Heuristic scorer baseline (350 lines, $0/video)
- [x] Gemini API key configured in settings
- [x] Stripe billing infrastructure (checkout sessions, webhooks, premium flags)
- [ ] LLM scorer integration into analysis pipeline
- [ ] A/B comparison dashboard between heuristic vs LLM
- [ ] Pro feature gate on LLM-scored analyses
