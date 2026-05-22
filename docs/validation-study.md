# Prediction Accuracy Validation Study

## What This Actually Measures

The ROI scores (A5, LO, Area45, TPJ) are **lexicon-based heuristic feature metrics**, not a neural encoding model. Each score counts word/phrase frequencies in a transcript that correlate with known engagement patterns:

| Score | What it actually measures | Stylized label |
|-------|--------------------------|----------------|
| A5 | Sentence rhythm variance, lexical diversity, pause density | "Auditory cortex" |
| LO | Visual and emotional word frequency | "Lateral occipital" |
| Area45 | CTA keyword and imperative sentence density | "Broca's area" |
| TPJ | Question density, social pronoun ratio, emotional word frequency | "Temporoparietal junction" |

The brain-region labels are **biomimetic naming conventions** — they describe *which type of engagement* the feature targets, not literal neural measurements. The validation study tests whether these simple linguistic features correlate with actual video performance.

## Hypothesis

Lexicon-based heuristic scores (A5, LO, Area45, TPJ) correlate with actual video performance metrics (views, engagement rate).

## Method

1. Collect 100+ videos with known view counts and engagement rates
2. Run each through the heuristic scoring pipeline
3. Calculate Pearson correlation between each ROI score and actual metrics
4. Compare against baselines:
   - **Trivial baseline**: random predictions (r > 0.05)
   - **Informative baseline**: TF-IDF + linear regression on the same features (tests whether our specific weighting adds value)

## Success Criteria

- r > 0.3 for at least 2 ROI scores vs views
- r > 0.3 for at least 1 ROI score vs engagement rate
- **Beat the TF-IDF baseline** — if a simple linear model on raw word frequencies matches or exceeds our heuristic, the specific lexicon weights aren't adding value

## Data Collection

- Source: Users who share actual performance via dashboard feedback
- Minimum: 100 videos for statistical significance
- Timeline: 3-6 months at current user volume

## Risks

- **Small sample size** → unreliable correlations
- **Selection bias** (users who share data may be atypical) — consider blind/mandatory sampling for a subset of users
- **External factors** (algorithm changes, timing) confound results
- **r > 0.3 is suspicious on first pass** — if achieved with n < 100, investigate for data leakage before publishing claims
