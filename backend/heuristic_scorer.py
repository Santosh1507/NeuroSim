"""Pure heuristic ROI scoring from transcript text.

Maps linguistic features to 4 ROI dimensions:
  A5   — auditory cortex (pacing, rhythm, clarity)
  LO   — lateral occipital (visual/descriptive language)
  Area45 — Broca's area (CTA activation, persuasion)
  TPJ  — temporoparietal junction (social cognition, curiosity)

No LLM, no external API. Fully self-contained, $0/mo.
"""
import re
import math
from typing import Dict, Any

# ── Lexicon lists ──────────────────────────────────────────────────────────

VISUAL_WORDS = {
    "see", "look", "watch", "view", "imagine", "picture", "visual", "bright",
    "color", "dark", "light", "beautiful", "stunning", "gorgeous", "vivid",
    "clear", "blurry", "shine", "glow", "sparkle", "reflect", "mirror",
    "scene", "landscape", "face", "eye", "hand", "body", "movement",
    "show", "display", "reveal", "appear", "visible", "transparent",
}

EMOTIONAL_WORDS = {
    "love", "hate", "amazing", "terrible", "awesome", "horrible", "incredible",
    "disappointing", "excited", "angry", "happy", "sad", "fear", "joy",
    "surprised", "shocked", "thrilled", "devastated", "worried", "anxious",
    "hopeful", "grateful", "frustrated", "overwhelmed", "passionate",
    "heartbreaking", "inspiring", "motivating", "powerful", "emotional",
}

SOCIAL_PRONOUNS = {
    "we", "our", "us", "together", "community", "team", "family", "friends",
    "everyone", "everybody", "people", "society", "shared", "collaborate",
}

CTA_KEYWORDS = {
    "subscribe", "click", "buy", "purchase", "order", "sign up", "register",
    "download", "join", "follow", "share", "like", "comment", "get started",
    "try now", "limited", "offer", "deal", "discount", "free trial",
    "don't miss", "act now", "hurry", "exclusive", "bonus",
}

QUESTION_PATTERNS = [
    r"\bwhat\b", r"\bhow\b", r"\bwhy\b", r"\bwhen\b", r"\bwhere\b",
    r"\bwho\b", r"\bwhich\b", r"\bis\b.*\?", r"\bare\b.*\?",
    r"\bdo\b.*\?", r"\bdoes\b.*\?", r"\bcan\b.*\?", r"\bshould\b.*\?",
    r"\bwould\b.*\?", r"\bcould\b.*\?",
]

PAUSE_MARKERS = ["...", "—", "–", ",", ";", "um", "uh", "well,", "so,"]

IMPERATIVE_STARTERS = {
    "get", "try", "buy", "click", "subscribe", "join", "follow", "download",
    "discover", "learn", "find", "start", "build", "create", "make", "watch",
}

# ── Scoring functions ──────────────────────────────────────────────────────

def _word_count(text: str) -> int:
    return len(text.split())


def _sentence_count(text: str) -> int:
    return max(1, len(re.split(r'[.!?]+', text)))


def _avg_sentence_length(text: str) -> float:
    words = _word_count(text)
    sents = _sentence_count(text)
    return words / sents if sents > 0 else 0


def _sentence_length_variance(text: str) -> float:
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    if not sentences:
        return 0
    lengths = [len(s.split()) for s in sentences]
    mean = sum(lengths) / len(lengths)
    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    return variance


def _lexical_diversity(text: str) -> float:
    words = [w.lower() for w in re.findall(r'\b[a-z]+\b', text)]
    if not words:
        return 0
    return len(set(words)) / len(words)


def _count_pattern(text: str, word_set: set) -> int:
    words = set(re.findall(r'\b[a-z]+\b', text.lower()))
    return len(words & word_set)


def _question_density(text: str) -> float:
    sents = _sentence_count(text)
    question_count = 0
    for pattern in QUESTION_PATTERNS:
        question_count += len(re.findall(pattern, text.lower()))
    return question_count / sents if sents > 0 else 0


def _pause_density(text: str) -> float:
    words = _word_count(text)
    if words == 0:
        return 0
    pause_count = sum(text.count(p) for p in PAUSE_MARKERS)
    return pause_count / words


def _imperative_ratio(text: str) -> float:
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    if not sentences:
        return 0
    imperative_count = 0
    for s in sentences:
        first_word = s.lower().split()[0] if s.split() else ""
        if first_word in IMPERATIVE_STARTERS:
            imperative_count += 1
    return imperative_count / len(sentences)


def _social_pronoun_ratio(text: str) -> float:
    words = re.findall(r'\b[a-z]+\b', text.lower())
    if not words:
        return 0
    social_count = sum(1 for w in words if w in SOCIAL_PRONOUNS)
    return social_count / len(words)


# ── ROI scorers ────────────────────────────────────────────────────────────

def score_a5(text: str) -> float:
    """Auditory cortex — pacing, rhythm, clarity."""
    variance = _sentence_length_variance(text)
    diversity = _lexical_diversity(text)
    pause_dens = _pause_density(text)

    # Moderate variance = good pacing (too uniform = boring, too wild = chaotic)
    pacing_score = math.exp(-((variance - 12) ** 2) / 200)

    # High lexical diversity = rich vocabulary = engaging
    vocab_score = min(1.0, diversity * 1.5)

    # Some pauses = natural speech rhythm
    rhythm_score = min(1.0, pause_dens * 15)

    return round(0.45 * pacing_score + 0.35 * vocab_score + 0.20 * rhythm_score, 3)


def score_lo(text: str) -> float:
    """Lateral occipital — visual/descriptive language."""
    visual_count = _count_pattern(text, VISUAL_WORDS)
    emotional_count = _count_pattern(text, EMOTIONAL_WORDS)
    words = _word_count(text)

    if words == 0:
        return 0

    visual_density = visual_count / words
    emotional_density = emotional_count / words

    # Visual words directly map to LO
    visual_score = min(1.0, visual_density * 20)

    # Emotional language enhances visual engagement
    emotion_boost = min(0.3, emotional_density * 5)

    return round(min(1.0, visual_score + emotion_boost), 3)


def score_area45(text: str) -> float:
    """Broca's area — CTA activation, persuasion."""
    cta_count = _count_pattern(text, CTA_KEYWORDS)
    imp_ratio = _imperative_ratio(text)
    words = _word_count(text)

    if words == 0:
        return 0

    cta_density = cta_count / words

    # CTA keywords
    cta_score = min(1.0, cta_density * 30)

    # Imperative sentences = direct persuasion
    imperative_score = min(1.0, imp_ratio * 4)

    return round(0.60 * cta_score + 0.40 * imperative_score, 3)


def score_tpj(text: str) -> float:
    """Temporoparietal junction — social cognition, curiosity gaps."""
    question_dens = _question_density(text)
    social_ratio = _social_pronoun_ratio(text)
    emotional_count = _count_pattern(text, EMOTIONAL_WORDS)
    words = _word_count(text)

    if words == 0:
        return 0

    emotional_density = emotional_count / words

    # Questions = curiosity gaps
    curiosity_score = min(1.0, question_dens * 3)

    # Social pronouns = empathy/connection
    social_score = min(1.0, social_ratio * 15)

    # Emotional words = empathetic resonance
    emotion_score = min(1.0, emotional_density * 10)

    return round(0.40 * curiosity_score + 0.30 * social_score + 0.30 * emotion_score, 3)


# ── Public API ─────────────────────────────────────────────────────────────

def score_transcript(text: str) -> Dict[str, Any]:
    """Score a transcript and return all 4 ROI dimensions.

    Returns dict with keys: A5, LO, Area45, TPJ (each 0-1 float),
    plus 'mode': 'heuristic' and 'word_count'.
    """
    text = text.strip()
    if not text:
        return {
            "A5": 0.5, "LO": 0.5, "Area45": 0.5, "TPJ": 0.5,
            "mode": "heuristic", "word_count": 0, "note": "empty transcript"
        }

    return {
        "A5": score_a5(text),
        "LO": score_lo(text),
        "Area45": score_area45(text),
        "TPJ": score_tpj(text),
        "mode": "heuristic",
        "word_count": _word_count(text),
    }
