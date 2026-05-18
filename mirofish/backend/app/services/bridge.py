"""
Neuro-Social Bridge
Maps neural ROI scores to OASIS simulation parameters.
Implements the mathematical mapping from PRD v2.0:
- W_attn = (0.7 × μ_LO) + (0.3 × μ_A5)  → initial attention weight
- P_skip = 1.0 - W_attn                    → skip probability
- P_share = μ_Area45 × Social_Multiplier   → share propensity (default 1.2)
"""

from typing import Dict, Any
from ..utils.logger import get_logger

logger = get_logger('mirofish.bridge')

# PRD constants
SOCIAL_MULTIPLIER = 1.2
STAGE_GATE_THRESHOLD = 0.4


class NeuroSocialBridge:
    """Maps neural ROI scores to social simulation parameters."""

    def map_to_simulation_params(self, roi_scores: Dict[str, float]) -> Dict[str, Any]:
        """
        Convert ROI scores to OASIS simulation parameters.

        PRD v2.0 §3.2 Mapping Function:
            W_attn = (0.7 × LO) + (0.3 × A5)
            P_skip = 1.0 - W_attn
            P_share = Area45 × SOCIAL_MULTIPLIER

        Args:
            roi_scores: Dict with A5, LO, Area45, TPJ scores (0.0-1.0).

        Returns:
            Dict with simulation parameters for agent initialization.
        """
        a5 = roi_scores.get('A5', 0.5)
        lo = roi_scores.get('LO', 0.5)
        area45 = roi_scores.get('Area45', 0.5)
        tpj = roi_scores.get('TPJ', 0.5)

        # PRD §3.2: W_attn = (0.7 × μ_LO) + (0.3 × μ_A5)
        w_attn = (0.7 * lo) + (0.3 * a5)

        # PRD §3.2: Agent Action Propensity
        p_skip = 1.0 - w_attn
        p_share = min(area45 * SOCIAL_MULTIPLIER, 1.0)

        # TPJ influences social engagement (comment/reply likelihood)
        social_engagement = tpj
        comment_likelihood = social_engagement * 0.8 + 0.2  # Scale to 0.2-1.0

        # Predicted reach multiplier based on share propensity
        viral_coefficient = 1.0 + (p_share * 0.8)

        # 7-day peak reach estimate (agents × viral coefficient × rounds)
        base_reach = 1000  # 1000 agents
        peak_reach = int(base_reach * viral_coefficient * (1 + w_attn))

        params = {
            'W_attn': round(w_attn, 4),
            'P_skip': round(p_skip, 4),
            'P_share': round(p_share, 4),
            'attention_weight': round(w_attn, 3),
            'viral_propensity': round(area45 * SOCIAL_MULTIPLIER, 3),
            'viral_coefficient': round(viral_coefficient, 3),
            'social_engagement': round(social_engagement, 3),
            'ignore_probability': round(p_skip, 3),
            'share_multiplier': round(min(area45 * SOCIAL_MULTIPLIER, 2.0), 3),
            'comment_likelihood': round(comment_likelihood, 3),
            'peak_reach_estimate': peak_reach,
            'roi_scores': {
                'A5': a5,
                'LO': lo,
                'Area45': area45,
                'TPJ': tpj,
            },
        }

        logger.info(
            f"Bridge mapping: W_attn={w_attn:.4f}, "
            f"P_skip={p_skip:.4f}, P_share={p_share:.4f}, "
            f"viral_coeff={viral_coefficient:.3f}"
        )
        return params

    def generate_persona_weights(
        self,
        roi_scores: Dict[str, float],
        num_personas: int = 8,
    ) -> list:
        """
        Generate persona weight adjustments based on ROI scores.

        High attention → more loyal fans and trend seekers
        High viral → more influencers
        High social → more casual viewers
        Low scores → more skeptics and anti-ad personas

        Args:
            roi_scores: Dict with A5, LO, Area45, TPJ scores.
            num_personas: Number of persona types to generate weights for.

        Returns:
            List of persona dicts with adjusted weights.
        """
        params = self.map_to_simulation_params(roi_scores)
        attn = params['attention_weight']
        viral = params['viral_propensity']
        social = params['social_engagement']

        # Base persona distribution
        personas = [
            {"type": "loyal_fan", "base_weight": 0.15},
            {"type": "skeptic", "base_weight": 0.12},
            {"type": "trend_seeker", "base_weight": 0.18},
            {"type": "budget_shopper", "base_weight": 0.15},
            {"type": "anti_ad", "base_weight": 0.10},
            {"type": "casual_viewer", "base_weight": 0.20},
            {"type": "influencer", "base_weight": 0.05},
            {"type": "hater", "base_weight": 0.05},
        ]

        # Adjust weights based on neural scores
        for p in personas:
            if p['type'] in ('loyal_fan', 'trend_seeker'):
                p['weight'] = p['base_weight'] * (1.0 + attn * 0.5)
            elif p['type'] == 'influencer':
                p['weight'] = p['base_weight'] * (1.0 + viral * 0.8)
            elif p['type'] == 'casual_viewer':
                p['weight'] = p['base_weight'] * (1.0 + social * 0.3)
            elif p['type'] in ('skeptic', 'anti_ad', 'hater'):
                # More skeptics when content is weak
                weakness = 1.0 - attn
                p['weight'] = p['base_weight'] * (1.0 + weakness * 0.5)
            else:
                p['weight'] = p['base_weight']

        # Normalize weights to sum to 1.0
        total = sum(p['weight'] for p in personas)
        for p in personas:
            p['weight'] = round(p['weight'] / total, 4)

        return personas
