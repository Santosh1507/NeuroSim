# Prediction Accuracy Validation Study

## Hypothesis
Heuristic ROI scores (A5, LO, Area45, TPJ) correlate with actual video performance metrics (views, engagement rate).

## Method
1. Collect 100+ videos with known view counts and engagement rates
2. Run each through the heuristic scoring pipeline
3. Calculate Pearson correlation between each ROI score and actual metrics
4. Compare against baseline (random predictions)

## Success Criteria
- r > 0.3 for at least 2 ROI scores vs views
- r > 0.3 for at least 1 ROI score vs engagement rate
- Better than random baseline (r > 0.05)

## Data Collection
- Source: Users who share actual performance via dashboard feedback
- Minimum: 100 videos for statistical significance
- Timeline: 3-6 months at current user volume

## Risks
- Small sample size → unreliable correlations
- Selection bias (users who share data may be atypical)
- External factors (algorithm changes, timing) confound results
