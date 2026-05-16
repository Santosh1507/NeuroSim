"""
Report Generator Service
Aggregates simulation results into a structured report with risk score,
sentiment distribution, blind spots, and top reactions.
"""

from typing import List, Dict, Any, Optional
from ..utils.logger import get_logger

logger = get_logger('mirofish.report_generator')


class ReportGenerator:
    """
    Generates structured simulation reports from reactions and blind spots.
    """

    def generate(
        self,
        reactions: List[Dict[str, Any]],
        blind_spots: List[Dict[str, Any]],
        personas: List[Dict[str, Any]],
        document_type: str = "press_release",
        partial: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a complete simulation report.

        Args:
            reactions: List of reaction dicts from SwarmSimulator.
            blind_spots: List of blind spot dicts from BlindSpotDetector.
            personas: List of persona dicts (for display names).
            document_type: Type of document simulated.
            partial: Whether this is a partial result (some reactions missing).

        Returns:
            Report dict matching the API contract.
        """
        sentiment_dist = self._calculate_sentiment_distribution(reactions)
        risk_score = self._calculate_risk_score(reactions, blind_spots)
        top_reactions = self._get_top_reactions(reactions, personas)

        report = {
            'risk_score': round(risk_score, 2),
            'risk_label': self._risk_label(risk_score),
            'sentiment_distribution': sentiment_dist,
            'blind_spots': blind_spots,
            'top_reactions': top_reactions,
            'total_reactions': len(reactions),
            'total_personas': len(personas),
            'partial': partial,
            'document_type': document_type,
        }

        logger.info(
            f"Report generated: risk={risk_score:.2f} ({report['risk_label']}), "
            f"sentiment={sentiment_dist}, blind_spots={len(blind_spots)}"
        )

        return report

    def _calculate_sentiment_distribution(self, reactions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate sentiment distribution as ratios."""
        if not reactions:
            return {'positive': 0.0, 'neutral': 0.0, 'negative': 0.0}

        counts = {'positive': 0, 'neutral': 0, 'negative': 0}
        for r in reactions:
            sentiment = r.get('sentiment', 'neutral')
            if sentiment in counts:
                counts[sentiment] += 1

        total = len(reactions)
        return {
            'positive': round(counts['positive'] / total, 2),
            'neutral': round(counts['neutral'] / total, 2),
            'negative': round(counts['negative'] / total, 2),
        }

    def _calculate_risk_score(
        self,
        reactions: List[Dict[str, Any]],
        blind_spots: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate overall risk score (0.0-1.0).
        Higher = more risk.

        Formula:
        - Base: negative sentiment ratio (0-0.5 weight)
        - Blind spot penalty: count * severity (0-0.3 weight)
        - Sentiment divergence: |pos-neg| (0-0.2 weight)
        """
        if not reactions:
            return 0.5  # Unknown risk

        sentiment_dist = self._calculate_sentiment_distribution(reactions)
        negative_ratio = sentiment_dist['negative']

        # Blind spot penalty
        severity_weights = {'critical': 0.15, 'high': 0.1, 'medium': 0.05}
        blind_spot_penalty = sum(
            severity_weights.get(bs.get('severity', 'medium'), 0.05)
            for bs in blind_spots
        )
        blind_spot_penalty = min(blind_spot_penalty, 0.3)  # Cap at 0.3

        # Sentiment divergence
        divergence = abs(sentiment_dist['positive'] - sentiment_dist['negative'])

        # Combined score
        risk = (negative_ratio * 0.5) + blind_spot_penalty + (divergence * 0.2)
        return min(max(risk, 0.0), 1.0)  # Clamp to [0, 1]

    def _risk_label(self, risk_score: float) -> str:
        """Convert risk score to human-readable label."""
        if risk_score >= 0.7:
            return "critical"
        elif risk_score >= 0.5:
            return "high"
        elif risk_score >= 0.3:
            return "medium"
        else:
            return "low"

    def _get_top_reactions(
        self,
        reactions: List[Dict[str, Any]],
        personas: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Get representative reactions (one positive, one neutral, one negative).
        Includes persona display name.
        """
        persona_map = {p['id']: p['display_name'] for p in personas}

        top = {'positive': None, 'neutral': None, 'negative': None}

        for r in reactions:
            sentiment = r.get('sentiment', 'neutral')
            if top[sentiment] is None:
                top[sentiment] = {
                    'persona': persona_map.get(r.get('persona_id', ''), 'Unknown'),
                    'text': r.get('text', ''),
                    'sentiment': sentiment,
                }
            if all(top.values()):
                break

        return [v for v in top.values() if v is not None]
