# Pro Tier Technical Roadmap

## Current State
- Simulated TRIBE v2 (random arrays)
- Simulated MiroFish (1000-agent swarm, no real LLM)
- Heuristic scoring (lexicon-based, $0/video)

## Pro Tier Options

### Option 1: LLM-Enhanced Scoring
- Use GPT-4o-mini to score transcripts
- Cost: ~$0.002/video (1000 tokens in, 50 out)
- Pros: Easy to implement, immediate improvement
- Cons: Still not "real neural encoding"

### Option 2: Real GPU Inference
- Modal.com, RunPod, or Replicate for GPU inference
- Cost: ~$0.05-0.20/video depending on model
- Pros: Real model predictions
- Cons: Complex infrastructure, higher cost

### Option 3: Hybrid (Recommended)
- Keep heuristic as base (fast, free)
- Add LLM refinement for Pro users
- Cost: ~$0.002/video for LLM layer
- Pros: Best cost/quality ratio, incremental improvement
- Cons: Still not TRIBE v2

## Recommendation: Option 3 (Hybrid)
1. Week 1: Implement LLM scorer (llm_scorer.py)
2. Week 2: A/B test heuristic vs LLM on existing videos
3. Week 3: Build Pro tier billing + feature flag
4. Week 4: Launch Pro tier with "LLM-enhanced analysis"

## Messaging Change
- Current: "Pro — Real GPU-powered TRIBE v2 brain encoding"
- Proposed: "Pro — LLM-enhanced analysis with deeper insights"
- Remove "TRIBE v2" until there's a concrete path to it
