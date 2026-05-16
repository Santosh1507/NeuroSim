"""
Stage-Gate Logic
1. StageGate: Evaluates neural ROI scores for NeuroSim content quality.
2. DocumentGate: Validates PR crisis documents (length, language, injection defense).
"""

import re
import hashlib
from typing import Dict, Any, Tuple
from ..utils.logger import get_logger

logger = get_logger('mirofish.stage_gate')

# Default threshold — content below this score is flagged
DEFAULT_THRESHOLD = 0.45

# Document gate constants
MIN_DOCUMENT_LENGTH = 100
MAX_DOCUMENT_LENGTH = 10000
DICTIONARY_WORD_THRESHOLD = 0.30

# Common English words for gibberish detection
COMMON_ENGLISH_WORDS = {
    'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
    'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
    'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
    'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what',
    'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me',
    'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know', 'take',
    'people', 'into', 'year', 'your', 'good', 'some', 'could', 'them', 'see', 'other',
    'than', 'then', 'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also',
    'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well', 'way',
    'even', 'new', 'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us',
    'is', 'are', 'was', 'were', 'been', 'being', 'has', 'had', 'did', 'does',
    'company', 'statement', 'public', 'response', 'crisis', 'issue', 'release', 'news',
    'announcement', 'organization', 'business', 'customer', 'market', 'product', 'service',
}

# Prompt injection patterns
INJECTION_PATTERNS = [
    r'ignore\s+(all\s+)?previous\s+(instructions|prompts|rules)',
    r'you\s+are\s+now\s+',
    r'system\s*:\s*',
    r'<\|.*?\|>',
    r'\[INST\].*\[/INST\]',
    r'disregard\s+(all\s+)?prior',
    r'forget\s+(all\s+)?(previous|your)\s+(instructions|rules)',
    r'output\s+only\s+positive',
    r'always\s+respond\s+with',
]


class StageGate:
    """Evaluates whether content passes the neural quality gate."""

    def __init__(self, threshold: float = DEFAULT_THRESHOLD):
        self.threshold = threshold

    def evaluate(self, roi_scores: Dict[str, float]) -> Dict[str, Any]:
        """
        Evaluate content against the stage-gate threshold.

        Args:
            roi_scores: Dict with A5, LO, Area45, TPJ scores (0.0-1.0).

        Returns:
            Dict with passed (bool), gate_score (float), recommendation, and details.
        """
        a5 = roi_scores.get('A5', 0.5)
        lo = roi_scores.get('LO', 0.5)

        gate_score = lo * 0.7 + a5 * 0.3
        passed = gate_score >= self.threshold

        if passed:
            if gate_score >= 0.7:
                recommendation = "Strong content — proceed with full simulation"
                severity = "pass"
            else:
                recommendation = "Adequate content — proceed with simulation"
                severity = "pass_weak"
        else:
            recommendation = f"Content scored {gate_score:.2f} (threshold: {self.threshold:.2f}). Consider revising the hook or visual composition before simulating."
            severity = "fail"

        details = {
            'gate_score': round(gate_score, 3),
            'threshold': self.threshold,
            'LO_contribution': round(lo * 0.7, 3),
            'A5_contribution': round(a5 * 0.3, 3),
            'passed': passed,
            'recommendation': recommendation,
            'severity': severity,
        }

        logger.info(f"Stage-gate: gate_score={gate_score:.3f}, passed={passed}, severity={severity}")
        return details


class DocumentGate:
    """
    Validates PR crisis documents before simulation.
    Checks: length, language, gibberish, HTML/script injection, prompt injection.
    """

    def validate(self, document: str) -> Tuple[bool, str]:
        """
        Validate document content.

        Returns:
            (passed: bool, reason: str)
        """
        if not document or not document.strip():
            return False, "No document provided"

        if len(document) < MIN_DOCUMENT_LENGTH:
            return False, f"Document too short (min {MIN_DOCUMENT_LENGTH} chars, got {len(document)})"

        if len(document) > MAX_DOCUMENT_LENGTH:
            return False, f"Document too long (max {MAX_DOCUMENT_LENGTH} chars, got {len(document)})"

        cleaned = self._strip_html(document)
        cleaned = self._strip_control_chars(cleaned)

        injection_check = self._check_prompt_injection(cleaned)
        if injection_check:
            return False, f"Document contains potentially manipulative content: {injection_check}"

        if self._is_gibberish(cleaned):
            return False, "Document appears to be invalid text"

        if not self._is_english(cleaned):
            return False, "English only in Phase 1"

        return True, "Document passed validation"

    def sanitize(self, document: str) -> str:
        """Strip HTML, control characters, and return clean text."""
        cleaned = self._strip_html(document)
        cleaned = self._strip_control_chars(cleaned)
        return cleaned.strip()

    def compute_hash(self, document: str) -> str:
        """Compute SHA-256 hash of document for audit logging."""
        return hashlib.sha256(document.encode('utf-8')).hexdigest()

    def _strip_html(self, text: str) -> str:
        """Remove HTML tags and script content."""
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<[^>]+>', '', text)
        return text

    def _strip_control_chars(self, text: str) -> str:
        """Remove control characters except newlines and tabs."""
        return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

    def _check_prompt_injection(self, text: str) -> str:
        """Check for prompt injection patterns. Returns matched pattern or empty string."""
        text_lower = text.lower()
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, text_lower):
                return f"matched pattern: {pattern}"
        return ""

    def _is_english(self, text: str) -> bool:
        """Simple English detection using common word ratio."""
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        if not words:
            return False

        english_count = sum(1 for w in words if w in COMMON_ENGLISH_WORDS)
        ratio = english_count / len(words)
        return ratio >= DICTIONARY_WORD_THRESHOLD

    def _is_gibberish(self, text: str) -> bool:
        """Detect gibberish by checking dictionary word ratio."""
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        if not words:
            return True

        english_count = sum(1 for w in words if w in COMMON_ENGLISH_WORDS)
        ratio = english_count / len(words)
        return ratio < DICTIONARY_WORD_THRESHOLD
