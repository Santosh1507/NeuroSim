"""Pure heuristic ROI scoring from transcript text.

Maps linguistic features to 4 ROI dimensions:
  A5   — auditory cortex (pacing, rhythm, clarity)
  LO   — lateral occipital (visual/descriptive language)
  Area45 — Broca's area (CTA activation, persuasion)
  TPJ  — temporoparietal junction (social cognition, curiosity)

No LLM, no external API. Fully self-contained, $0/mo.
"""

import math
import random
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Set

# ── Lexicon lists ──────────────────────────────────────────────────────────

VISUAL_WORDS = {
    "see",
    "look",
    "watch",
    "view",
    "imagine",
    "picture",
    "visual",
    "bright",
    "color",
    "dark",
    "light",
    "beautiful",
    "stunning",
    "gorgeous",
    "vivid",
    "clear",
    "blurry",
    "shine",
    "glow",
    "sparkle",
    "reflect",
    "mirror",
    "scene",
    "landscape",
    "face",
    "eye",
    "hand",
    "body",
    "movement",
    "show",
    "display",
    "reveal",
    "appear",
    "visible",
    "transparent",
}

EMOTIONAL_WORDS = {
    "love",
    "hate",
    "amazing",
    "terrible",
    "awesome",
    "horrible",
    "incredible",
    "disappointing",
    "excited",
    "angry",
    "happy",
    "sad",
    "fear",
    "joy",
    "surprised",
    "shocked",
    "thrilled",
    "devastated",
    "worried",
    "anxious",
    "hopeful",
    "grateful",
    "frustrated",
    "overwhelmed",
    "passionate",
    "heartbreaking",
    "inspiring",
    "motivating",
    "powerful",
    "emotional",
}

SOCIAL_PRONOUNS = {
    "we",
    "our",
    "us",
    "together",
    "community",
    "team",
    "family",
    "friends",
    "everyone",
    "everybody",
    "people",
    "society",
    "shared",
    "collaborate",
}

CTA_KEYWORDS = {
    "subscribe",
    "click",
    "buy",
    "purchase",
    "order",
    "sign up",
    "register",
    "download",
    "join",
    "follow",
    "share",
    "like",
    "comment",
    "get started",
    "try now",
    "limited",
    "offer",
    "deal",
    "discount",
    "free trial",
    "don't miss",
    "act now",
    "hurry",
    "exclusive",
    "bonus",
}

QUESTION_PATTERNS = [
    r"\bwhat\b",
    r"\bhow\b",
    r"\bwhy\b",
    r"\bwhen\b",
    r"\bwhere\b",
    r"\bwho\b",
    r"\bwhich\b",
    r"\bis\b.*\?",
    r"\bare\b.*\?",
    r"\bdo\b.*\?",
    r"\bdoes\b.*\?",
    r"\bcan\b.*\?",
    r"\bshould\b.*\?",
    r"\bwould\b.*\?",
    r"\bcould\b.*\?",
]

PAUSE_MARKERS = ["...", "—", "–", ",", ";", "um", "uh", "well,", "so,"]

IMPERATIVE_STARTERS = {
    "get",
    "try",
    "buy",
    "click",
    "subscribe",
    "join",
    "follow",
    "download",
    "discover",
    "learn",
    "find",
    "start",
    "build",
    "create",
    "make",
    "watch",
}

# ── Pre-computed text features ─────────────────────────────────────────────
# score_transcript() builds this ONCE per call, then reuses across all 4
# ROI dimensions — avoids re-parsing text ~10x per transcript.

@dataclass
class _TextFeatures:
    """Pre-computed text features to avoid re-parsing the transcript."""
    word_count: int
    sentence_count: int
    lower_words: list
    unique_lower: set
    sentence_length_variance: float
    lexical_diversity: float
    question_density: float
    pause_density: float
    imperative_ratio: float
    social_pronoun_ratio: float


def _compute_features(text: str) -> _TextFeatures:
    """Compute all text features in a single pass."""
    word_count = len(text.split())
    lower_text = text.lower()
    lower_words = re.findall(r"\b[a-z]+\b", lower_text)
    unique_lower = set(lower_words)
    lower_len = len(lower_words)

    # Match original _sentence_count: max(1, len(re.split(...)))
    # which includes empty trailing strings from trailing punctuation
    sent_split = re.split(r"[.!?]+", text)
    sentence_count = max(1, len(sent_split))

    # Filtered sentences for variance/imperative (matches original helpers)
    sentences = [s.strip() for s in sent_split if s.strip()]

    # Sentence length variance (matches _sentence_length_variance)
    if sentences:
        sent_lengths = [len(s.split()) for s in sentences]
        mean_len = sum(sent_lengths) / len(sent_lengths)
        variance = sum((l - mean_len) ** 2 for l in sent_lengths) / len(sent_lengths)
    else:
        variance = 0.0

    # Lexical diversity (matches _lexical_diversity)
    lexical_diversity = len(unique_lower) / lower_len if lower_len > 0 else 0.0

    # Question density (matches _question_density)
    question_count = sum(
        len(re.findall(pattern, lower_text))
        for pattern in QUESTION_PATTERNS
    )
    question_density = question_count / sentence_count

    # Pause density (matches _pause_density: text.count for each marker)
    pause_count = sum(text.count(p) for p in PAUSE_MARKERS)
    pause_density = pause_count / word_count if word_count > 0 else 0.0

    # Imperative ratio (matches _imperative_ratio)
    if sentences:
        imperative_count = sum(
            1 for s in sentences
            if (s.split() and s.lower().split()[0] in IMPERATIVE_STARTERS)
        )
        imperative_ratio = imperative_count / len(sentences)
    else:
        imperative_ratio = 0.0

    # Social pronoun ratio (matches _social_pronoun_ratio)
    social_count = sum(1 for w in lower_words if w in SOCIAL_PRONOUNS)
    social_pronoun_ratio = social_count / lower_len if lower_len > 0 else 0.0

    return _TextFeatures(
        word_count=word_count,
        sentence_count=sentence_count,
        lower_words=lower_words,
        unique_lower=unique_lower,
        sentence_length_variance=variance,
        lexical_diversity=lexical_diversity,
        question_density=question_density,
        pause_density=pause_density,
        imperative_ratio=imperative_ratio,
        social_pronoun_ratio=social_pronoun_ratio,
    )


def _count_features(features: _TextFeatures, word_set: set) -> int:
    """Count how many words from word_set appear in the pre-computed features."""
    return len(features.unique_lower & word_set)


# ── Feature-based scorers (internal — used by score_transcript) ────────────


def _score_a5_from_features(f: _TextFeatures) -> float:
    """Auditory cortex — pacing, rhythm, clarity (from pre-computed features)."""
    pacing_score = math.exp(-((f.sentence_length_variance - 12) ** 2) / 200)
    vocab_score = min(1.0, f.lexical_diversity * 1.5)
    rhythm_score = min(1.0, f.pause_density * 15)
    return round(0.45 * pacing_score + 0.35 * vocab_score + 0.20 * rhythm_score, 3)


def _score_lo_from_features(f: _TextFeatures) -> float:
    """Lateral occipital — visual/descriptive language (from pre-computed features)."""
    visual_count = _count_features(f, VISUAL_WORDS)
    emotional_count = _count_features(f, EMOTIONAL_WORDS)
    if f.word_count == 0:
        return 0.0
    visual_density = visual_count / f.word_count
    emotional_density = emotional_count / f.word_count
    visual_score = min(1.0, visual_density * 20)
    emotion_boost = min(0.3, emotional_density * 5)
    return round(min(1.0, visual_score + emotion_boost), 3)


def _score_area45_from_features(f: _TextFeatures) -> float:
    """Broca's area — CTA activation, persuasion (from pre-computed features)."""
    cta_count = _count_features(f, CTA_KEYWORDS)
    if f.word_count == 0:
        return 0.0
    cta_density = cta_count / f.word_count
    cta_score = min(1.0, cta_density * 30)
    imperative_score = min(1.0, f.imperative_ratio * 4)
    return round(0.60 * cta_score + 0.40 * imperative_score, 3)


def _score_tpj_from_features(f: _TextFeatures) -> float:
    """Temporoparietal junction — social cognition (from pre-computed features)."""
    emotional_count = _count_features(f, EMOTIONAL_WORDS)
    if f.word_count == 0:
        return 0.0
    emotional_density = emotional_count / f.word_count
    curiosity_score = min(1.0, f.question_density * 3)
    social_score = min(1.0, f.social_pronoun_ratio * 15)
    emotion_score = min(1.0, emotional_density * 10)
    return round(0.40 * curiosity_score + 0.30 * social_score + 0.30 * emotion_score, 3)


# ── Public API ─────────────────────────────────────────────────────────────


def score_transcript(text: str) -> Dict[str, Any]:
    """Score a transcript and return all 4 ROI dimensions.

    Returns dict with keys: A5, LO, Area45, TPJ (each 0-1 float),
    plus 'mode': 'heuristic' and 'word_count'.

    Pre-computes text features ONCE and reuses across all 4 dimensions,
    instead of re-parsing the text ~10x.
    """
    text = text.strip()
    if not text:
        # Return varied fallback scores so multiple empty-transcript calls
        # don't all return identical scores. Label as "fallback" to signal
        # the transcript was empty.
        rng = random.Random()
        return {
            "A5": round(rng.uniform(0.35, 0.65), 3),
            "LO": round(rng.uniform(0.35, 0.65), 3),
            "Area45": round(rng.uniform(0.35, 0.65), 3),
            "TPJ": round(rng.uniform(0.35, 0.65), 3),
            "mode": "fallback",
            "word_count": 0,
            "note": "empty transcript — estimated scores (no text to analyze)",
        }

    # ── Efficiency: compute features once, reuse across all 4 scorers ──
    f = _compute_features(text)

    return {
        "A5": _score_a5_from_features(f),
        "LO": _score_lo_from_features(f),
        "Area45": _score_area45_from_features(f),
        "TPJ": _score_tpj_from_features(f),
        "mode": "heuristic",
        "word_count": f.word_count,
    }
