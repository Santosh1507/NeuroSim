# NeuroSim v3.0 — Launch Plan

## The Product
AI-powered video content analysis. Upload a video, get predictions on hook strength, viral potential, and success probability. Free tier: 10 analyses/month.

## Target Users
1. **YouTube creators** (1K-100K subs) — want to predict video performance before publishing
2. **Marketing teams** — A/B test video content before spending ad budget
3. **Content agencies** — need data-driven recommendations for client videos

## Launch Sequence

### Week 1: Soft Launch (Beta)
**Goal:** 10 users, 50 analyses, first feedback data points

1. **Personal network** — DM 10 creator friends: "Built something that predicts video performance. Want early access?"
2. **Twitter/X post** — "I built an AI that predicts how well your video will perform before you publish it. Free for the first 100 users. Try it: [link]"
3. **Reddit r/YouTube** — "I analyzed 1000+ videos to find what makes them go viral. Built a free tool to score your content. Roast my predictions."
4. **Indie Hackers** — "Show HN: NeuroSim — predict video performance before publishing"

### Week 2: Public Launch
**Goal:** 100 users, 500 analyses, first validation study data

1. **Hacker News Show HN** — Title: "Show HN: NeuroSim — AI that predicts video performance before you publish"
   - Post at 9-11 AM ET on Tuesday/Wednesday/Thursday
   - First comment: technical details about the heuristic scoring + swarm simulation
   - Be responsive to comments for the first 2 hours

2. **Product Hunt** — Prepare launch assets:
   - Tagline: "Predict video performance before you publish"
   - Thumbnail: Clean screenshot of the dashboard
   - First comment from founder: "I built this because..."

3. **YouTube creator Discord servers** — Share in #tools or #resources channels

### Week 3: Content Marketing
**Goal:** Organic traffic, SEO foundation

1. **Blog post:** "The 4 Neural Patterns That Predict Video Success" — explain A5, LO, Area45, TPJ in plain English
2. **Twitter thread:** Break down a viral video's scores vs a flop
3. **Case study:** "We predicted this video would get 50K views. It got 47K."

### Week 4: Data Flywheel
**Goal:** Activate the data moat

1. **Email all users:** "How did your video perform? Share your results and get 1 month Pro free."
2. **Publish first validation study:** "Our predictions correlate at r=0.X with actual performance"
3. **Open-source the heuristic scorer:** GitHub repo drives developer interest

## Key Metrics to Track

| Metric | Week 1 | Week 2 | Week 4 | Month 3 | Month 6 |
|--------|--------|--------|--------|---------|---------|
| Signups | 10 | 100 | 500 | 2000 | 5000 |
| Analyses | 50 | 500 | 3000 | 15000 | 40000 |
| Feedback submissions | 5 | 25 | 80 | 250 | 500 |
| Correlation entries | 5 | 25 | 80 | 250 | 500 |

> **Note on feasibility:** At Week 2's 100 users, ~25% feedback rate → 25 entries. At Month 3's 2,000 users, ~12.5% feedback rate → 250 entries. Hitting 500 correlation entries realistically takes ~5-6 months at these conversion rates, not 4 weeks. The "500 in 4 weeks" assumption would require 100% of signups to submit feedback, which is unrealistic for a free tool.

## HN / Reddit Narrative: "How is this validated?"

When someone asks "How do you know these predictions are accurate?" — the answer should be direct and honest:

> "We built a first-principles model: 4 linguistic heuristics mapped to known brain region responses (auditory, visual, social, CTA), then validated against 1,000+ videos. Each prediction is scored by a 1,000-agent swarm simulation for social spread. We're running a public validation study — users submit actual performance data, we publish the correlation transparently. Current n=XX, r=0.XX. No black box."

**Key principles:**
- Acknowledge it's heuristic-based, not a neural net predicting brains
- Cite the validation study as a living, public document
- Frame the "neural" language as biomimetic feature labeling, not literal brain scanning
- Never claim "accuracy" without citing the current n and r

## Contingency: What If Validation Falls Short?

| Signal | Action |
|--------|--------|
| r < 0.15 at n=50 | **Pause public launch.** Investigate scorer quality. Iterate weights. Do not push marketing. |
| r < 0.25 at n=100 | **Soften claims.** Reframe as "content analysis" not "prediction." Focus on comparative scoring (A vs B) over absolute accuracy. |
| r > 0.3 at n=100 | **Full speed.** Publish study, double down on marketing claims, open-source scorer. |
| r > 0.4 at n=200 | **Exceptional.** Publish academic-style paper, pitch to industry blogs, expand moat claims. |

## What Not to Do

- Don't spend money on ads until you have product-market fit signal
- Don't build Pro tier features until you have 500+ correlation data points
- Don't optimize for vanity metrics (page views) over signal (feedback submissions)

## The One Metric That Matters

**Correlation entries** — each one makes the product more defensible. Everything else is noise until you hit 500.
